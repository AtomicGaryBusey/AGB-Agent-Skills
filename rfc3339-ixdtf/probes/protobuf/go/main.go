// Command pbrfc probes Go protobuf's JSON mapping of google.protobuf.Timestamp
// (google.golang.org/protobuf/encoding/protojson) against RFC 3339.
//
//	go build -o pbrfc .
//	TZ=America/New_York ./pbrfc probe   <../../inputs.json  > consumers-go.jsonl
//	TZ=America/New_York ./pbrfc produce                     > producers-go.jsonl
//	./pbrfc list                 (adapter keys: <key>\t<target-kind>)
//	./pbrfc adapter [unmarshal]  (run_vectors.py adapter, per-process and batch
//	                              (RFCDT_BATCH=1 JSON lines); prints ok + seconds/nanos)
//
// probe reads probes/inputs.json (schema 2 {"inputs","legacy"}, or the old list).
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"

	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/types/known/timestamppb"
)

type result struct {
	OK      bool   `json:"ok"`
	Seconds int64  `json:"seconds"`
	Nanos   int32  `json:"nanos"`
	Error   string `json:"error,omitempty"`
	Reemit  string `json:"reemit,omitempty"`
}

// unmarshal feeds s to protojson.Unmarshal as a JSON string literal.
func unmarshal(s string) result {
	lit, err := json.Marshal(s)
	if err != nil {
		return result{OK: false, Error: "json.Marshal: " + err.Error()}
	}
	var ts timestamppb.Timestamp
	if err := protojson.Unmarshal(lit, &ts); err != nil {
		return result{OK: false, Error: err.Error()}
	}
	r := result{OK: true, Seconds: ts.Seconds, Nanos: ts.Nanos}
	if b, err := protojson.Marshal(&ts); err == nil {
		var out string
		_ = json.Unmarshal(b, &out)
		r.Reemit = out
	} else {
		r.Reemit = "ERR " + err.Error()
	}
	return r
}

// Extra inputs aimed at protojson's own checks (fraction length, range).
var extra = []struct{ ID, S, Cat string }{
	{"pb-comma-long", "2026-09-24T12:00:00,1234567891234Z", "invalid"},
	{"pb-h1", "2026-09-24T1:00:00Z", "invalid"},
	{"pb-off2460", "2026-09-24T12:00:00+24:60", "invalid"},
	{"pb-min-off", "0001-01-01T00:00:00+01:00", "valid"},
	{"pb-max-off", "9999-12-31T23:59:59-01:00", "valid"},
	{"pb-max-frac", "9999-12-31T23:59:59.999999999Z", "valid"},
	{"pb-frac10", "2026-09-24T12:00:00.1234567890Z", "valid"},
	{"pb-offnoZ-frac10", "2026-09-24T12:00:00.1234567890+01:00", "valid"},
}

func probe() {
	type rec struct {
		ID  string `json:"id"`
		S   string `json:"s"`
		Cat string `json:"cat"`
	}
	var inputs []rec
	data, _ := io.ReadAll(os.Stdin)
	if err := json.Unmarshal(data, &inputs); err != nil {
		var doc struct {
			Inputs []rec `json:"inputs"`
			Legacy []rec `json:"legacy"`
		}
		if err2 := json.Unmarshal(data, &doc); err2 != nil {
			fmt.Fprintln(os.Stderr, err2)
			os.Exit(2)
		}
		inputs = append(doc.Inputs, doc.Legacy...)
	}
	enc := json.NewEncoder(os.Stdout)
	emit := func(id, s, cat string) {
		enc.Encode(map[string]any{"api": "go protojson.Unmarshal(Timestamp)", "id": id, "s": s, "cat": cat, "result": unmarshal(s)})
	}
	for _, in := range inputs {
		emit(in.ID, in.S, in.Cat)
	}
	for _, in := range extra {
		emit(in.ID, in.S, in.Cat)
	}
}

func produce() {
	const base = 1790251200 // 2026-09-24T12:00:00Z
	cases := []struct {
		label string
		secs  int64
		nanos int32
	}{
		{"nanos 0", base, 0},
		{"nanos 100000000 (0.1 s)", base, 100000000},
		{"nanos 123000000", base, 123000000},
		{"nanos 123456000", base, 123456000},
		{"nanos 123456789", base, 123456789},
		{"nanos 1", base, 1},
		{"zero value Timestamp{}", 0, 0},
		{"seconds -62135596800 (min)", -62135596800, 0},
		{"seconds 253402300799 (max), nanos 999999999", 253402300799, 999999999},
		{"seconds -62135596801 (below min)", -62135596801, 0},
		{"seconds 253402300800 (above max)", 253402300800, 0},
		{"nanos -1", base, -1},
		{"nanos 1000000000", base, 1000000000},
		{"seconds max, nanos 1000000000", 253402300799, 1000000000},
	}
	enc := json.NewEncoder(os.Stdout)
	for _, c := range cases {
		ts := &timestamppb.Timestamp{Seconds: c.secs, Nanos: c.nanos}
		row := map[string]any{"label": c.label, "seconds": c.secs, "nanos": c.nanos}
		if b, err := protojson.Marshal(ts); err != nil {
			row["protojson.Marshal"] = "ERR " + err.Error()
		} else {
			var out string
			_ = json.Unmarshal(b, &out)
			row["protojson.Marshal"] = out
		}
		if err := ts.CheckValid(); err != nil {
			row["CheckValid"] = "ERR " + err.Error()
		} else {
			row["CheckValid"] = "ok"
		}
		row["AsTime().Format(RFC3339Nano)"] = ts.AsTime().Format("2006-01-02T15:04:05.999999999Z07:00")
		enc.Encode(row)
	}
}

// answer is one run_vectors.py result (protobuf keeps no offset: no RFC fields).
func answer(s string) map[string]any {
	r := unmarshal(s)
	out := map[string]any{"ok": r.OK}
	if r.OK {
		out["seconds"], out["nanos"], out["reemit"] = r.Seconds, r.Nanos, r.Reemit
	} else {
		out["error"] = r.Error
	}
	return out
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: pbrfc probe|produce|list|adapter [unmarshal]")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "probe":
		probe()
	case "produce":
		produce()
	case "list":
		fmt.Println("unmarshal\trfc3339")
	case "adapter":
		if len(os.Args) > 2 && os.Args[2] != "unmarshal" {
			fmt.Fprintf(os.Stderr, "unknown adapter key %q; see: pbrfc list\n", os.Args[2])
			os.Exit(2)
		}
		b, _ := io.ReadAll(os.Stdin)
		if os.Getenv("RFCDT_BATCH") == "1" {
			for _, line := range strings.Split(string(b), "\n") {
				if strings.TrimSpace(line) == "" {
					continue
				}
				var req struct {
					ID    string `json:"id"`
					Input string `json:"input"`
				}
				if err := json.Unmarshal([]byte(line), &req); err != nil {
					fmt.Println(`{"ok":false,"error":"bad request line"}`)
					continue
				}
				out := answer(req.Input)
				out["id"] = req.ID
				j, _ := json.Marshal(out)
				fmt.Println(string(j))
			}
			return
		}
		j, _ := json.Marshal(answer(string(b)))
		fmt.Println(string(j))
	default:
		os.Exit(2)
	}
}
