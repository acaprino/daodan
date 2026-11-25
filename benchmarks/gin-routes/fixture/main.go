// Fixture for the gin-routes probe: what Gin's `Routes()` and its debug hooks give. Nothing here is meant to be useful.
package main

import (
	"log"
	"net"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
)

type Server struct{ name string }

// List is registered as a method value: `r.GET("/srv", srv.List)` (its function name ends in `-fm`).
func (s *Server) List(c *gin.Context) { c.JSON(http.StatusOK, gin.H{"server": s.name}) }

func listItems(c *gin.Context)  { c.JSON(http.StatusOK, []string{"a", "b"}) }
func getItem(c *gin.Context)    { c.JSON(http.StatusOK, gin.H{"id": c.Param("id")}) }
func createItem(c *gin.Context) { c.Status(http.StatusCreated) }
func notFound(c *gin.Context)   { c.String(http.StatusNotFound, "no such route") }
func logger(c *gin.Context)     { c.Next() }

// auth is a middleware factory: its handler is a closure, `main.auth.func1`.
func auth() gin.HandlerFunc {
	return func(c *gin.Context) { c.Next() }
}

// setupRouter is the shape the Gin documentation uses for tests; a project may build its engine anywhere.
func setupRouter() *gin.Engine {
	switch os.Getenv("FIXTURE_FAIL") { // what keeps the application from loading
	case "panic":
		panic("fixture: the application does not load")
	case "db":
		conn, err := net.DialTimeout("tcp", "db.invalid:5432", 2*time.Second)
		if err != nil {
			log.Fatalf("fixture: database unreachable: %v", err)
		}
		conn.Close()
	case "block":
		time.Sleep(time.Hour) // never reaches the routes
	}

	r := gin.New()
	r.Use(logger)
	r.GET("/ping", func(c *gin.Context) { c.String(http.StatusOK, "pong") }) // closure: main.setupRouter.func1
	r.GET("/items", listItems)
	r.GET("/items/:id", getItem)
	r.POST("/items", createItem)
	srv := &Server{name: "main"}
	r.GET("/srv", srv.List)

	api := r.Group("/api/v1", auth())
	api.GET("/users", listItems) // the same function on a second path
	admin := api.Group("/admin", auth())
	admin.DELETE("/users/:id", func(c *gin.Context) { c.Status(http.StatusNoContent) })

	r.Any("/any", listItems) // nine methods
	r.Match([]string{http.MethodGet, http.MethodPost}, "/match", listItems)
	r.Static("/static", "./public") // the handler is a closure inside Gin
	r.StaticFile("/favicon.ico", "./favicon.ico")
	r.NoRoute(notFound) // not in Routes()
	return r
}

func main() {
	if os.Getenv("FIXTURE_RELEASE") != "" {
		gin.SetMode(gin.ReleaseMode) // what many applications do in main()
	}
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	r := setupRouter()
	if err := r.Run(":" + port); err != nil { // blocks here
		log.Fatal(err)
	}
}
