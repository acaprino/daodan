// Package store opens the platform storage backend.
package store

// Open names the backend chosen for this platform.
func Open() string { return backend() }
