// Package tool is the core of the tool.
package tool

// Version is the tool version.
const Version = "0.4.0"

// Banner returns the startup banner.
func Banner() string { return "tool " + Version }
