// Prints, for every file below the folder given, what go-enry's library says of it: its language and the
// predicates the enry command uses to leave a file out silently (vendored, documentation, configuration, dot
// file), plus generated and binary, which it does not use. Daodan builds it with go-enry at the version
// `premap/enry.py` pins; it reads files and runs nothing.
package main

import (
	"encoding/json"
	"io"
	"os"
	"path/filepath"

	"github.com/go-enry/go-enry/v2"
)

type row struct {
	Path          string `json:"path"`
	Language      string `json:"language"`
	Vendored      bool   `json:"vendored"`
	Documentation bool   `json:"documentation"`
	Configuration bool   `json:"configuration"`
	DotFile       bool   `json:"dot_file"`
	Generated     bool   `json:"generated"`
	Binary        bool   `json:"binary"`
}

func main() {
	root := os.Args[1]
	rows := []row{}
	filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if info.IsDir() {
			if info.Name() == ".git" {
				return filepath.SkipDir
			}
			return nil
		}
		if !info.Mode().IsRegular() {
			return nil
		}
		rel, _ := filepath.Rel(root, path)
		rel = filepath.ToSlash(rel)
		f, err := os.Open(path)
		if err != nil {
			return nil
		}
		content, _ := io.ReadAll(io.LimitReader(f, 16*1024))
		f.Close()
		rows = append(rows, row{
			Path: rel, Language: enry.GetLanguage(rel, content), Vendored: enry.IsVendor(rel),
			Documentation: enry.IsDocumentation(rel), Configuration: enry.IsConfiguration(rel),
			DotFile: enry.IsDotFile(rel), Generated: enry.IsGenerated(rel, content),
			Binary: enry.IsBinary(content) || enry.IsImage(rel),
		})
		return nil
	})
	json.NewEncoder(os.Stdout).Encode(rows)
}
