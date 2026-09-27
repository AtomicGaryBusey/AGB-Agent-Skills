package main

import (
	"encoding/json"
	jsonv2 "encoding/json/v2"
	"fmt"
	"time"
)

type W struct {
	T time.Time `json:",omitempty"`
}
type Z struct {
	T time.Time `json:",omitzero"`
}

func main() {
	fmt.Println(time.Now().String())
	b, _ := json.Marshal(W{})
	fmt.Println("v1 omitempty zero:", string(b))
	b, _ = json.Marshal(Z{})
	fmt.Println("v1 omitzero zero:", string(b))
	var w W
	err := jsonv2.Unmarshal([]byte(`{"T":"2026-09-24T12:00:00,5Z"}`), &w, json.DefaultOptionsV1(), json.ParseTimeWithLooseRFC3339(false))
	fmt.Println("v1 options + ParseTimeWithLooseRFC3339(false):", err)
}
