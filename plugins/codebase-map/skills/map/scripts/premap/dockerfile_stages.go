// Prints the stages of the Dockerfile given, with the build arguments given as a JSON object, or of each build
// a Compose model declares (`--compose`, Compose's own `config --format json`), as BuildKit's own Dockerfile
// frontend reads them: each stage's name and base, the base expanded with the arguments declared
// before the first FROM; each instruction with its lines, its words expanded as BuildKit expands them with the
// stage's ARG and ENV values, the names it references that no ARG or ENV gives (`unmatched`: the base image's
// environment may), and its flags. Daodan builds it with BuildKit at the version `premap/dockerfile.py` pins; it
// reads the file and runs nothing.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/moby/buildkit/frontend/dockerfile/instructions"
	"github.com/moby/buildkit/frontend/dockerfile/linter"
	"github.com/moby/buildkit/frontend/dockerfile/parser"
	"github.com/moby/buildkit/frontend/dockerfile/shell"
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

func emit(value any) {
	encoder := json.NewEncoder(os.Stdout)
	encoder.SetEscapeHTML(false)
	if err := encoder.Encode(value); err != nil {
		fail(err)
	}
}

// With `--compose <file>`, each service's build of the Compose model in the file, its paths relative to the
// working folder: {builds: [{service, dockerfile, context, args, target, stages}], errors: [{service, dockerfile,
// error}]}, a build whose Dockerfile does not read an error; otherwise {stages}.
func main() {
	if len(os.Args) == 3 && os.Args[1] == "--compose" {
		data, err := os.ReadFile(os.Args[2])
		if err != nil {
			fail(err)
		}
		var model composed
		if err := json.Unmarshal(data, &model); err != nil {
			fail(err)
		}
		here, _ := os.Getwd()
		names := make([]string, 0, len(model.Services))
		for name := range model.Services {
			names = append(names, name)
		}
		sort.Strings(names)
		builds, errors := []map[string]any{}, []map[string]string{}
		for _, name := range names {
			build := model.Services[name].Build
			if build == nil {
				continue
			}
			file := build.Dockerfile
			if file == "" {
				file = "Dockerfile"
			}
			if !filepath.IsAbs(file) {
				file = filepath.Join(build.Context, file)
			}
			given := map[string]string{}
			for key, value := range build.Args {
				if value != nil {
					given[key] = *value
				}
			}
			context, _ := filepath.Rel(here, build.Context)
			dockerfile, _ := filepath.Rel(here, file)
			stages, err := read(file, given)
			if err != nil {
				errors = append(errors, map[string]string{"service": name, "dockerfile": filepath.ToSlash(dockerfile),
					"error": err.Error()})
				continue
			}
			builds = append(builds, map[string]any{"service": name, "dockerfile": filepath.ToSlash(dockerfile),
				"context": filepath.ToSlash(context), "args": given, "target": build.Target, "stages": stages})
		}
		emit(map[string]any{"builds": builds, "errors": errors})
		return
	}
	if len(os.Args) != 3 {
		fmt.Fprintln(os.Stderr, "usage: daodan-dockerfile <Dockerfile> <build arguments as JSON> | --compose <file>")
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
	emit(map[string]any{"stages": stages})
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
