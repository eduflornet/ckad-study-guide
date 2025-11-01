package main

import (
    "fmt"
    "log"
    "net/http"
    "os"
)

func main() {
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "Hello from Go! Version: %s\n", os.Getenv("APP_VERSION"))
    })
    
    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "application/json")
        fmt.Fprintf(w, `{"status":"healthy","version":"%s"}`, os.Getenv("APP_VERSION"))
    })
    
    port := os.Getenv("PORT")
    if port == "" {
        port = "8080"
    }
    
    fmt.Printf("Server starting on port %s\n", port)
    log.Fatal(http.ListenAndServe(":"+port, nil))
}
