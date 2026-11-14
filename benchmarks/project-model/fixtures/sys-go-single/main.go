package main

import (
	"log"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"

	"example.com/hello/internal/greet"
)

func main() {
	r := chi.NewRouter()
	r.Get("/hello/{name}", func(w http.ResponseWriter, req *http.Request) {
		w.Header().Set("X-Request-Id", uuid.NewString())
		_, _ = w.Write([]byte(greet.Hello(chi.URLParam(req, "name"))))
	})
	log.Fatal(http.ListenAndServe(":8080", r))
}
