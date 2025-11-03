package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"os/user"
)

func main() {
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		currentUser, err := user.Current()
		if err != nil {
			currentUser = &user.User{Username: "unknown", Uid: "unknown"}
		}
		
		hostname, _ := os.Hostname()
		
		fmt.Fprintf(w, `
		<h1>Distroless Security Demo</h1>
		<ul>
			<li><strong>User:</strong> %s (UID: %s)</li>
			<li><strong>Hostname:</strong> %s</li>
			<li><strong>Process ID:</strong> %d</li>
			<li><strong>Security:</strong> Running in distroless container</li>
		</ul>
		<p>This application demonstrates secure container practices using distroless images.</p>
		`, currentUser.Username, currentUser.Uid, hostname, os.Getpid())
	})

	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintf(w, `{"status":"healthy","user":"%s"}`, getCurrentUser())
	})

	port := "8080"
	fmt.Printf("Server starting on port %s\n", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}

func getCurrentUser() string {
	currentUser, err := user.Current()
	if err != nil {
		return "unknown"
	}
	return fmt.Sprintf("%s (UID: %s)", currentUser.Username, currentUser.Uid)
}