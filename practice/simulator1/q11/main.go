package main

import (
    "fmt"
    "os"
    "time"
)

func main() {
    cipherID := os.Getenv("SUN_CIPHER_ID")
    for {
        fmt.Printf("Running Golang app... SUN_CIPHER_ID=%s\n", cipherID)
        time.Sleep(5 * time.Second)
    }
}
