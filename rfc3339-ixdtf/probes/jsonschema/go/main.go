// Command jsprobe probes github.com/santhosh-tekuri/jsonschema/v6 `format` assertion.
//
//	go build -o jsprobe .
//	./jsprobe [adapter] <variant>   (run_vectors.py adapter; stdin = one string, stdout = {"ok":…};
//	                                 RFCDT_BATCH=1: JSON lines in, one result line per input)
//	./jsprobe list                  (listed variants: <key>\t<target-kind>)
//
// variants: assert (2020-12, format date-time, Compiler.AssertFormat()),
//           default (2020-12, no AssertFormat), draft7 (draft-07, no AssertFormat),
//           date / time (2020-12, format date / time, AssertFormat()),
//           pattern (assert + the strict RFC 3339 "pattern" from ecosystem.md).
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"

	"github.com/santhosh-tekuri/jsonschema/v6"
)

// variants listed by `jsprobe list` (date / time are not date-time vectors, so not listed).
var listed = []string{"assert", "default", "draft7", "pattern"}

// validator compiles the schema for a variant once.
func validator(variant string) (func(string) map[string]any, error) {
	format := "date-time"
	switch variant {
	case "date", "time":
		format = variant
	case "assert", "default", "draft7", "pattern":
	default:
		return nil, fmt.Errorf("unknown variant %q (see: jsprobe list)", variant)
	}
	draft := "https://json-schema.org/draft/2020-12/schema"
	if variant == "draft7" {
		draft = "http://json-schema.org/draft-07/schema#"
	}
	schemaDoc := map[string]any{"$schema": draft, "type": "string", "format": format}
	if variant == "pattern" {
		schemaDoc["pattern"] = `^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])[Tt]([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)([.][0-9]+)?([Zz]|[+-]([01][0-9]|2[0-3]):[0-5][0-9])$`
	}
	c := jsonschema.NewCompiler()
	if variant != "default" && variant != "draft7" {
		c.AssertFormat()
	}
	if err := c.AddResource("mem://s.json", schemaDoc); err != nil {
		return nil, fmt.Errorf("schema: %w", err)
	}
	sch, err := c.Compile("mem://s.json")
	if err != nil {
		return nil, fmt.Errorf("compile: %w", err)
	}
	return func(s string) map[string]any {
		if err := sch.Validate(s); err != nil {
			return map[string]any{"ok": false, "error": strings.ReplaceAll(err.Error(), "\n", " | ")}
		}
		return map[string]any{"ok": true}
	}, nil
}

func emit(out map[string]any) {
	j, _ := json.Marshal(out)
	fmt.Println(string(j))
}

func main() {
	args := os.Args[1:]
	if len(args) > 0 && args[0] == "list" {
		for _, v := range listed {
			fmt.Printf("%s\trfc3339\n", v)
		}
		return
	}
	if len(args) > 0 && args[0] == "adapter" {
		args = args[1:]
	}
	variant := "assert"
	if len(args) > 0 {
		variant = args[0]
	}
	check, err := validator(variant)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	if os.Getenv("RFCDT_BATCH") == "1" {
		sc := bufio.NewScanner(os.Stdin)
		sc.Buffer(make([]byte, 1<<20), 1<<26)
		w := bufio.NewWriter(os.Stdout)
		defer w.Flush()
		for sc.Scan() {
			line := strings.TrimSpace(sc.Text())
			if line == "" {
				continue
			}
			var req struct {
				ID    string `json:"id"`
				Input string `json:"input"`
			}
			out := map[string]any{}
			if err := json.Unmarshal([]byte(line), &req); err != nil {
				out["ok"], out["error"] = false, "adapter: bad request line"
			} else {
				out = check(req.Input)
			}
			out["id"] = req.ID
			j, _ := json.Marshal(out)
			w.Write(j)
			w.WriteString("\n")
		}
		return
	}
	b, _ := io.ReadAll(os.Stdin)
	emit(check(string(b)))
}
