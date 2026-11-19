// Prints the stages of the Dockerfile given, with the build arguments given as a JSON object, or of each build
// a Compose model declares (`--compose`, Compose's own `config --format json`), as BuildKit's own Dockerfile
// frontend reads them: each stage's name and base, the base expanded with the arguments declared
// before the first FROM; each instruction with its lines, its words expanded as BuildKit expands them with the
// stage's ARG and ENV values, the names it references that no ARG or ENV gives (`unmatched`: the base image's
// environment may), and its flags; and what the build's .dockerignore leaves out of its context, by BuildKit's
// own matcher. Daodan builds it with BuildKit at the version `premap/dockerfile.py` pins; it reads the files and
// runs nothing.
package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strings"

	"github.com/moby/buildkit/frontend/dockerfile/instructions"
	"github.com/moby/buildkit/frontend/dockerfile/linter"
	"github.com/moby/buildkit/frontend/dockerfile/parser"
	"github.com/moby/buildkit/frontend/dockerfile/shell"
	"github.com/moby/patternmatcher"
	"github.com/moby/patternmatcher/ignorefile"
)

// The variables an instruction expands with, in the order they were set.
type variables struct {
	keys   []string
	values map[string]string
}

func (v *variables) Get(key string) (string, bool) { value, ok := v.values[key]; return value, ok }
func (v *variables) Keys() []string                 { return v.keys }

func (v *variables) set(key, value string) {
	if _, ok := v.values[key]; !ok {
		v.keys = append(v.keys, key)
	}
	v.values[key] = value
}

func (v *variables) clone() *variables {
	out := &variables{values: map[string]string{}}
	for _, key := range v.keys {
		out.set(key, v.values[key])
	}
	return out
}

type mount struct {
	Type     string `json:"type"`
	Target   string `json:"target"`
	Source   string `json:"source,omitempty"`
	From     string `json:"from,omitempty"`
	ID       string `json:"id,omitempty"`
	Required bool   `json:"required,omitempty"`
}

type file struct {
	Name string `json:"name"`
	Data string `json:"data"`
}

type command struct {
	Kind      string            `json:"kind"`
	Line      int               `json:"line"`
	EndLine   int               `json:"end_line"`
	Original  string            `json:"original"`
	Unmatched []string          `json:"unmatched,omitempty"`
	Cmd       []string          `json:"cmd,omitempty"`
	Shell     *bool             `json:"shell,omitempty"`
	Files     []file            `json:"files,omitempty"`
	Mounts    []mount           `json:"mounts,omitempty"`
	Network   string            `json:"network,omitempty"`
	Security  string            `json:"security,omitempty"`
	Sources   []string          `json:"sources,omitempty"`
	Dest      string            `json:"dest,omitempty"`
	From      string            `json:"from,omitempty"`
	Chown     string            `json:"chown,omitempty"`
	Chmod     string            `json:"chmod,omitempty"`
	Flags     []string          `json:"flags,omitempty"`
	Env       [][2]string       `json:"env,omitempty"`
	Args      []map[string]*string `json:"args,omitempty"`
	Path      string            `json:"path,omitempty"`
	User      string            `json:"user,omitempty"`
	ShellForm []string          `json:"shell_form,omitempty"`
}

type stage struct {
	Name      string    `json:"name"`
	Base      string    `json:"base"`
	BaseStage *int      `json:"base_stage"`
	Line      int       `json:"line"`
	Platform  string    `json:"platform,omitempty"`
	Commands  []command `json:"commands"`
}

func lines(location []parser.Range) (int, int) {
	if len(location) == 0 {
		return 0, 0
	}
	return location[0].Start.Line, location[len(location)-1].End.Line
}

// A build Compose declares: what `docker-compose config --format json` gives of a service's `build`.
type composed struct {
	Services map[string]struct {
		Build *struct {
			Context    string             `json:"context"`
			Dockerfile string             `json:"dockerfile"`
			Args       map[string]*string `json:"args"`
			Target     string             `json:"target"`
		} `json:"build"`
	} `json:"services"`
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}

// The values of the tracked .env files, which the pre-map's container keeps beside the copy (Daodan's
// container.named, {file: {name: value}}, files relative to the copy) while the files themselves hold placeholders.
const dotenvValues = "/daodan/state/dotenv-values.json"

var reference = regexp.MustCompile(`\$\{?([A-Za-z_][A-Za-z0-9_]*)`) // a variable Compose interpolates

// Compose's model of `file`, in its folder: once with the values of its folder's tracked .env in the environment,
// which Compose prefers to the file's placeholders (the model the build reads), once with nothing interpolated (what
// names a variable). An error is Compose's own words of the run without the values, which hold none.
func models(file, root string) (real, raw composed, values map[string]string, err error) {
	known := map[string]map[string]string{}
	if data, readErr := os.ReadFile(dotenvValues); readErr == nil {
		_ = json.Unmarshal(data, &known)
	}
	here, _ := os.Getwd()
	env, _ := filepath.Rel(root, filepath.Join(here, ".env"))
	values = known[filepath.ToSlash(env)]
	run := func(into *composed, extra []string, more ...string) error {
		command := exec.Command("docker-compose", append([]string{"-f", file, "config", "--format", "json"}, more...)...)
		command.Env = append(os.Environ(), extra...)
		out, err := command.Output()
		if err == nil {
			err = json.Unmarshal(out, into)
		}
		return err
	}
	given := []string{}
	for name, value := range values {
		given = append(given, name+"="+value)
	}
	if err = run(&real, given); err != nil {
		command := exec.Command("docker-compose", "-f", file, "config", "--format", "json")
		if _, plain := command.Output(); plain != nil {
			if exit, ok := plain.(*exec.ExitError); ok {
				return real, raw, values, errors.New(strings.TrimSpace(string(exit.Stderr)))
			}
			return real, raw, values, plain
		}
		return real, raw, values, errors.New("docker compose config did not read the files with the tracked .env")
	}
	err = run(&raw, nil, "--no-interpolate")
	return real, raw, values, err
}

// The tracked .env variables `text` names, added to `used` ({name: file}).
func named(text string, values map[string]string, used map[string]string) bool {
	found := false
	for _, match := range reference.FindAllStringSubmatch(text, -1) {
		if _, ok := values[match[1]]; ok {
			used[match[1]], found = ".env", true
		}
	}
	return found
}

func emit(value any) {
	encoder := json.NewEncoder(os.Stdout)
	encoder.SetEscapeHTML(false)
	if err := encoder.Encode(value); err != nil {
		fail(err)
	}
}

// With `--compose <file>`, each service's build of the Compose model of the file in the working folder (`models`),
// its paths relative to that folder: {builds: [{service, dockerfile, context, args, target, stages, dockerignore,
// excluded, dotenv}], errors: [{service, dockerfile, error}]}, a build whose Dockerfile or ignore file does not read
// an error; otherwise {stages, dockerignore, excluded}, the context the Dockerfile's folder. `dockerignore` and
// `excluded` (`ignored`) only where an ignore file is. A value of the tracked .env never reaches the output: an
// argument or a target that names one of its variables is that `${NAME}`, which the stage's container interpolates;
// a context or a Dockerfile that does is read where it names a path of the checkout, else it is an error naming the
// variable; `dotenv` ({name: file}) names those variables.
func main() {
	if len(os.Args) == 3 && os.Args[1] == "--compose" {
		root := os.Getenv("DAODAN_COPY") // the copy of the checkout
		if root == "" {
			root = "/work"
		}
		model, raw, values, err := models(os.Args[2], root)
		if err != nil {
			fail(err)
		}
		here, _ := os.Getwd()
		dotenv, _ := filepath.Rel(root, filepath.Join(here, ".env"))
		names := make([]string, 0, len(model.Services))
		for name := range model.Services {
			names = append(names, name)
		}
		sort.Strings(names)
		builds, unread := []map[string]any{}, []map[string]string{}
		for _, name := range names {
			build, said := model.Services[name].Build, raw.Services[name].Build
			if build == nil {
				continue
			}
			if said == nil {
				said = build
			}
			used := map[string]string{}
			file := build.Dockerfile
			if file == "" {
				file = "Dockerfile"
			}
			if !filepath.IsAbs(file) {
				file = filepath.Join(build.Context, file)
			}
			// A context or a Dockerfile a tracked .env names is read where it names a path of the checkout, which
			// the fact may say: the copy holds only what Git tracks or the snapshot records.
			if named(said.Context+" "+said.Dockerfile, values, used) {
				for _, path := range []string{build.Context, file} {
					rel, relErr := filepath.Rel(root, filepath.Clean(path))
					if _, missing := os.Stat(path); relErr != nil || rel == ".." || strings.HasPrefix(rel, "../") ||
						missing != nil {
						variables := make([]string, 0, len(used))
						for variable := range used {
							variables = append(variables, variable)
						}
						sort.Strings(variables)
						err = fmt.Errorf("%s of %s gives no file or folder of the checkout",
							strings.Join(variables, ", "), filepath.ToSlash(dotenv))
					}
				}
			}
			if err != nil {
				unread = append(unread, map[string]string{"service": name, "dockerfile": said.Dockerfile,
					"error": err.Error()})
				err = nil
				continue
			}
			given := map[string]string{}
			for key, value := range build.Args {
				if value == nil {
					continue
				}
				given[key] = *value
				if text := said.Args[key]; text != nil && named(*text, values, used) {
					given[key] = *text // the variable, which the stage's container interpolates
				}
			}
			target := build.Target
			if named(said.Target, values, used) {
				target = said.Target
			}
			context, _ := filepath.Rel(here, build.Context)
			dockerfile, _ := filepath.Rel(here, file)
			stages, err := read(file, given)
			var ignore string
			var excluded []string
			if err == nil {
				ignore, excluded, err = ignored(build.Context, file)
			}
			if err != nil {
				unread = append(unread, map[string]string{"service": name, "dockerfile": filepath.ToSlash(dockerfile),
					"error": err.Error()})
				continue
			}
			item := map[string]any{"service": name, "dockerfile": filepath.ToSlash(dockerfile),
				"context": filepath.ToSlash(context), "args": given, "target": target, "stages": stages}
			for variable := range used {
				used[variable] = filepath.ToSlash(dotenv)
			}
			if len(used) > 0 {
				item["dotenv"] = used
			}
			if ignore != "" {
				ignore, _ = filepath.Rel(here, ignore)
				item["dockerignore"], item["excluded"] = filepath.ToSlash(ignore), excluded
			}
			builds = append(builds, item)
		}
		emit(map[string]any{"builds": builds, "errors": unread})
		return
	}
	if len(os.Args) != 3 {
		fmt.Fprintln(os.Stderr, "usage: daodan-dockerfile <Dockerfile> <build arguments as JSON> | --compose <compose file>")
		os.Exit(2)
	}
	given := map[string]string{}
	if err := json.Unmarshal([]byte(os.Args[2]), &given); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	stages, err := read(os.Args[1], given)
	if err != nil {
		fail(err)
	}
	out := map[string]any{"stages": stages}
	ignore, excluded, err := ignored(filepath.Dir(os.Args[1]), os.Args[1])
	if err != nil {
		fail(err)
	}
	if ignore != "" {
		out["dockerignore"], out["excluded"] = filepath.ToSlash(ignore), excluded
	}
	emit(out)
}

// The ignore file BuildKit reads for the Dockerfile at `dockerfile` built from `context` (its frontend's
// dockerui: `<Dockerfile>.dockerignore` beside it, else the context's .dockerignore, read with ignorefile.ReadAll),
// "" for none, and the paths of the context it leaves out, relative to it: what fsutil's walk with those exclude
// patterns (patternmatcher, at the version BuildKit pins) does not send, a folder it skips whole ending in "/".
func ignored(context, dockerfile string) (string, []string, error) {
	file := dockerfile + ".dockerignore"
	data, err := os.ReadFile(file)
	if errors.Is(err, fs.ErrNotExist) {
		file = filepath.Join(context, ".dockerignore")
		data, err = os.ReadFile(file)
	}
	if errors.Is(err, fs.ErrNotExist) {
		return "", nil, nil
	} else if err != nil {
		return "", nil, err
	}
	patterns, err := ignorefile.ReadAll(bytes.NewReader(data))
	if err != nil {
		return "", nil, err
	}
	excluded := []string{}
	if len(patterns) == 0 {
		return file, excluded, nil
	}
	matcher, err := patternmatcher.New(patterns)
	if err != nil {
		return "", nil, err
	}
	// As fsutil: a folder that matches is skipped whole when every exception is a plain path (no pattern
	// character but a trailing /* or /**) and none of them lies inside it; otherwise each of its paths is matched.
	prefixes := true
	for _, pattern := range matcher.Patterns() {
		if pattern.Exclusion() && strings.ContainsAny(withoutTrailingGlob(pattern), `*[]?^\`) {
			prefixes = false
		}
	}
	err = filepath.WalkDir(context, func(path string, entry fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		rel, err := filepath.Rel(context, path)
		if err != nil || rel == "." {
			return err
		}
		matched, err := matcher.MatchesOrParentMatches(rel)
		if err != nil || !matched {
			return err
		}
		if !entry.IsDir() {
			excluded = append(excluded, filepath.ToSlash(rel))
			return nil
		}
		if !prefixes {
			return nil
		}
		inside := rel + string(filepath.Separator)
		for _, pattern := range matcher.Patterns() {
			if pattern.Exclusion() && strings.HasPrefix(withoutTrailingGlob(pattern)+string(filepath.Separator), inside) {
				return nil
			}
		}
		excluded = append(excluded, filepath.ToSlash(rel)+"/")
		return filepath.SkipDir
	})
	return file, excluded, err
}

func withoutTrailingGlob(pattern *patternmatcher.Pattern) string {
	text := strings.TrimSuffix(pattern.String(), string(filepath.Separator)+"**")
	return strings.TrimSuffix(text, string(filepath.Separator)+"*")
}

// The stages of the Dockerfile at `path` as BuildKit reads them with the build arguments `given`.
func read(path string, given map[string]string) ([]stage, error) {
	source, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer source.Close()
	parsed, err := parser.Parse(source)
	if err != nil {
		return nil, err
	}
	stages, metaArgs, err := instructions.Parse(parsed.AST, linter.New(&linter.Config{}))
	if err != nil {
		return nil, err
	}
	lex := shell.NewLex(parsed.EscapeToken)
	// The arguments before the first FROM: a given value replaces the default, as `--build-arg` does.
	meta := &variables{values: map[string]string{}}
	for _, arg := range metaArgs {
		for _, kv := range arg.Args {
			if value, ok := given[kv.Key]; ok {
				meta.set(kv.Key, value)
			} else if kv.Value != nil {
				result, _ := lex.ProcessWordWithMatches(*kv.Value, meta)
				meta.set(kv.Key, result.Result)
			}
		}
	}
	names, out, ends := map[string]int{}, []stage{}, map[int]*variables{}
	for index, st := range stages {
		base, _ := lex.ProcessWordWithMatches(st.BaseName, meta)
		start, _ := lines(st.Location)
		item := stage{Name: st.Name, Base: base.Result, Line: start, Platform: st.Platform, Commands: []command{}}
		scope := &variables{values: map[string]string{}}
		if parent, ok := names[strings.ToLower(base.Result)]; ok { // stage names are case-insensitive
			item.BaseStage = &parent
			scope = ends[parent].clone()
		}
		for _, cmd := range st.Commands {
			first, last := lines(cmd.Location())
			entry := command{Kind: cmd.Name(), Line: first, EndLine: last, Original: fmt.Sprint(cmd)}
			unmatched := map[string]struct{}{}
			expand := func(word string) (string, error) {
				result, err := lex.ProcessWordWithMatches(word, scope)
				for name := range result.Unmatched {
					unmatched[name] = struct{}{}
				}
				return result.Result, err
			}
			if c, ok := cmd.(*instructions.ArgCommand); ok {
				// BuildKit's ARG: a given value, else the default, else the meta argument of that name.
				for _, kv := range c.Args {
					var value *string
					if v, ok := given[kv.Key]; ok {
						value = &v
					} else if kv.Value != nil {
						v, _ := expand(*kv.Value)
						value = &v
					} else if v, ok := meta.Get(kv.Key); ok {
						value = &v
					}
					if value != nil {
						scope.set(kv.Key, *value)
					}
					entry.Args = append(entry.Args, map[string]*string{kv.Key: value})
				}
			} else if c, ok := cmd.(instructions.SupportsSingleWordExpansion); ok {
				if err := c.Expand(expand); err != nil {
					return nil, fmt.Errorf("line %d: %w", first, err)
				}
			}
			switch c := cmd.(type) {
			case *instructions.RunCommand:
				prepend := c.PrependShell
				entry.Cmd, entry.Shell, entry.Flags = c.CmdLine, &prepend, c.FlagsUsed
				for _, f := range c.Files {
					entry.Files = append(entry.Files, file{Name: f.Name, Data: f.Data})
				}
				for _, m := range instructions.GetMounts(c) {
					entry.Mounts = append(entry.Mounts, mount{Type: string(m.Type), Target: m.Target,
						Source: m.Source, From: m.From, ID: m.CacheID, Required: m.Required})
				}
				entry.Network, entry.Security = instructions.GetNetwork(c), instructions.GetSecurity(c)
			case *instructions.CopyCommand:
				entry.Sources, entry.Dest, entry.From = c.SourcePaths, c.DestPath, c.From
				entry.Chown, entry.Chmod = c.Chown, c.Chmod
				if c.Parents {
					entry.Flags = append(entry.Flags, "parents")
				}
				if c.Link {
					entry.Flags = append(entry.Flags, "link")
				}
				if len(c.ExcludePatterns) > 0 {
					entry.Flags = append(entry.Flags, "exclude")
				}
				for _, content := range c.SourceContents {
					entry.Files = append(entry.Files, file{Name: content.Path, Data: content.Data})
				}
			case *instructions.AddCommand:
				entry.Sources, entry.Dest, entry.Chown, entry.Chmod = c.SourcePaths, c.DestPath, c.Chown, c.Chmod
				if c.Link {
					entry.Flags = append(entry.Flags, "link")
				}
				if len(c.ExcludePatterns) > 0 {
					entry.Flags = append(entry.Flags, "exclude")
				}
				if c.Checksum != "" {
					entry.Flags = append(entry.Flags, "checksum")
				}
				for _, content := range c.SourceContents {
					entry.Files = append(entry.Files, file{Name: content.Path, Data: content.Data})
				}
			case *instructions.EnvCommand:
				for _, kv := range c.Env {
					scope.set(kv.Key, kv.Value)
					entry.Env = append(entry.Env, [2]string{kv.Key, kv.Value})
				}
			case *instructions.WorkdirCommand:
				entry.Path = c.Path
			case *instructions.UserCommand:
				entry.User = c.User
			case *instructions.ShellCommand:
				entry.ShellForm = c.Shell
			}
			for name := range unmatched {
				entry.Unmatched = append(entry.Unmatched, name)
			}
			sort.Strings(entry.Unmatched)
			item.Commands = append(item.Commands, entry)
		}
		ends[index] = scope
		if st.Name != "" {
			names[strings.ToLower(st.Name)] = index
		}
		out = append(out, item)
	}
	return out, nil
}
