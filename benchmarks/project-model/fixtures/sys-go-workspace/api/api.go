// Package api holds the wire types shared by the services.
package api

// Order is one order as it travels between services.
type Order struct {
	ID    string
	Total int64
}
