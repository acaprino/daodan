// Prints, for every file below the folder given, what go-enry's library functions say: the ones the enry CLI
// uses to leave a file out silently (vendored, documentation, configuration, dot file) and the ones it does not
// use (generated, binary, image). Built once into the Modal image against the pinned go-enry.
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
	Vendored      bool   `json:"vendored"`
	Documentation bool   `json:"documentation"`
	Configuration bool   `json:"configuration"`
	DotFile       bool   `json:"dot_file"`
	Generated     bool   `json:"generated"`
	Binary        bool   `json:"binary"`
	Image         bool   `json:"image"`
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
			Path: rel, Vendored: enry.IsVendor(rel), Documentation: enry.IsDocumentation(rel),
			Configuration: enry.IsConfiguration(rel), DotFile: enry.IsDotFile(rel),
			Generated: enry.IsGenerated(rel, content), Binary: enry.IsBinary(content), Image: enry.IsImage(rel),
		})
		return nil
	})
	json.NewEncoder(os.Stdout).Encode(rows)
}
