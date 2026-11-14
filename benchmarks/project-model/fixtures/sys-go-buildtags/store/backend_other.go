//go:build !linux && !windows

package store

func backend() string { return "poll" }
