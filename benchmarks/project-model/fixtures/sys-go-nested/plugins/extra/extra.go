// Package extra is an optional plugin released as its own module.
package extra

import "example.com/tool"

// Describe names the plugin and the core it extends.
func Describe() string { return "extra plugin for " + tool.Banner() }
