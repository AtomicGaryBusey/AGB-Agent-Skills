// Command gorfc probes Go's time package against RFC 3339 / RFC 9557.
//
//	go build -o gorfc .
//	TZ=America/New_York ./gorfc probe   <inputs.json   > results/consumers.jsonl
//	TZ=America/New_York ./gorfc produce               > results/producers.jsonl
//	./gorfc list                 (adapter keys: <key>\t<target-kind>)
//	./gorfc adapter <key>        (run_vectors.py adapter, per-process and batch; keys:
//	                              parse3339 parse3339nano parseinlocation unmarshaljson
//	                              unmarshaltext json jsonv2 strict)
//	run_vectors.py --target './gorfc adapter json' --batch --target-kind rfc3339 \
//	    --target-options fixed --target-has-tzdata yes
//
// probe reads probes/inputs.json (schema 2 {"inputs","legacy"}, or the old list).
//
// Standard library only.
package main

import (
	"encoding/json"
	jsonv2 "encoding/json/v2"
	"fmt"
	"io"
	"os"
	"strings"
	"time"
)

type api struct {
	name string
	fn   func(string) (time.Time, error)
}

type wrap struct{ T time.Time }

var apis = []api{
	{"time.Parse(time.RFC3339)", func(s string) (time.Time, error) { return time.Parse(time.RFC3339, s) }},
	{"time.Parse(time.RFC3339Nano)", func(s string) (time.Time, error) { return time.Parse(time.RFC3339Nano, s) }},
	{"time.ParseInLocation(time.RFC3339, s, time.Local)", func(s string) (time.Time, error) {
		return time.ParseInLocation(time.RFC3339, s, time.Local)
	}},
	{"(*time.Time).UnmarshalJSON", func(s string) (time.Time, error) {
		b, _ := json.Marshal(s) // a JSON string literal of s
		var t time.Time
		err := t.UnmarshalJSON(b)
		return t, err
	}},
	{"(*time.Time).UnmarshalText", func(s string) (time.Time, error) {
		var t time.Time
		err := t.UnmarshalText([]byte(s))
		return t, err
	}},
	{"json.Unmarshal into struct{T time.Time}", func(s string) (time.Time, error) {
		b, _ := json.Marshal(map[string]string{"T": s})
		var w wrap
		err := json.Unmarshal(b, &w)
		return w.T, err
	}},
	{"encoding/json/v2 Unmarshal into struct{T time.Time}", func(s string) (time.Time, error) {
		b, _ := json.Marshal(map[string]string{"T": s})
		var w wrap
		err := jsonv2.Unmarshal(b, &w)
		return w.T, err
	}},
}

func utcString(t time.Time) string {
	return t.UTC().Format("2006-01-02T15:04:05.000000000Z")
}

func offsetString(t time.Time) string {
	name, off := t.Zone()
	sign := "+"
	if off < 0 {
		sign, off = "-", -off
	}
	s := fmt.Sprintf("%s%02d:%02d", sign, off/3600, off/60%60)
	if off%60 != 0 {
		s += fmt.Sprintf(":%02d", off%60)
	}
	loc := t.Location().String()
	if t.Location() == time.UTC {
		loc = "UTC"
	}
	return fmt.Sprintf("%s (zone=%q loc=%s)", s, name, loc)
}

type inputRec struct {
	ID   string `json:"id"`
	S    string `json:"s"`
	Cat  string `json:"cat"`
	Note string `json:"note"`
}

// readInputs accepts probes/inputs.json schema 2 ({"inputs","legacy"}) or the old list form.
func readInputs(r io.Reader) []inputRec {
	raw, err := io.ReadAll(r)
	if err != nil {
		panic(err)
	}
	var ins []inputRec
	if err := json.Unmarshal(raw, &ins); err == nil {
		return ins
	}
	var doc struct {
		Inputs []inputRec `json:"inputs"`
		Legacy []inputRec `json:"legacy"`
	}
	if err := json.Unmarshal(raw, &doc); err != nil {
		panic(err)
	}
	return append(doc.Inputs, doc.Legacy...)
}

func probe() {
	ins := readInputs(os.Stdin)
	enc := json.NewEncoder(os.Stdout)
	enc.SetEscapeHTML(false)
	// Extra inputs (not in inputs.json) that target the fallback parser.
	extraIns := []inputRec{
		{"x1-h1", "2026-09-24T1:00:00Z", "invalid", "1-digit hour"},
		{"x1-off2459", "2026-09-24T12:00:00+24:59", "invalid", "offset 24:59"},
		{"x1-off2460", "2026-09-24T12:00:00+24:60", "invalid", "offset 24:60"},
		{"x1-off2500", "2026-09-24T12:00:00+25:00", "invalid", "offset 25:00"},
		{"x1-frac-offbad", "2026-09-24T12:00:00.5+23:60", "invalid", "fraction + offset minute 60"},
		{"x1-comma12", "2026-09-24T12:00:00,123456789123Z", "invalid", "comma + 12 digits"},
		{"x1-lcz-frac", "2026-09-24T12:00:00.5z", "valid", "lowercase z after fraction"},
		{"x1-off-sec", "2026-09-24T12:00:00+00:44:30", "invalid", "offset with seconds"},
		{"x1-y99", "0099-01-01T00:00:00Z", "valid", "year 0099"},
		{"x1-nbsp", "2026-09-24T12:00:00 Z", "invalid", "NBSP before Z"},
	}
	ins = append(ins, extraIns...)
	for _, a := range apis {
		for _, in := range ins {
			rec := map[string]any{"lang": "go", "kind": "parse", "api": a.name, "id": in.ID, "input": in.S, "cat": in.Cat}
			t, err := a.fn(in.S)
			if err != nil {
				rec["ok"] = false
				rec["err"] = err.Error()
			} else {
				rec["ok"] = true
				rec["utc"] = utcString(t)
				rec["offset"] = offsetString(t)
				rec["reformat"] = t.Format(time.RFC3339Nano)
			}
			enc.Encode(rec)
		}
	}
	// Extra JSON-layer probes: escapes inside the JSON string.
	extras := []string{
		`"2026-09-24T12:00:00\u005a"`, // == "...Z" after JSON unescaping
		`"2026-09-24T12:00:00Z"`,
		`"2026-09-24T12:00:00Z\n"`,
		`"2026-09-24T12:00:00\u0000Z"`,
	}
	for _, raw := range extras {
		var t time.Time
		err := t.UnmarshalJSON([]byte(raw))
		rec := map[string]any{"lang": "go", "kind": "json-raw", "api": "(*time.Time).UnmarshalJSON raw", "input": raw}
		if err != nil {
			rec["ok"], rec["err"] = false, err.Error()
		} else {
			rec["ok"], rec["utc"] = true, utcString(t)
		}
		var w wrap
		err = json.Unmarshal([]byte(`{"T":`+raw+`}`), &w)
		if err != nil {
			rec["struct_ok"], rec["struct_err"] = false, err.Error()
		} else {
			rec["struct_ok"], rec["struct_utc"] = true, utcString(w.T)
		}
		enc.Encode(rec)
	}
}

func produce() {
	enc := json.NewEncoder(os.Stdout)
	enc.SetEscapeHTML(false)
	monrovia, err := time.LoadLocation("Africa/Monrovia")
	if err != nil {
		panic(err)
	}
	paris, _ := time.LoadLocation("Europe/Paris")
	type sample struct {
		label string
		t     time.Time
	}
	base := time.Date(2026, 9, 24, 12, 0, 0, 0, time.UTC)
	samples := []sample{
		{"UTC 2026-09-24T12:00:00Z", base},
		{"Local (TZ=America/New_York)", base.In(time.Local)},
		{"FixedZone(\"x\", -2670) [-00:44:30]", base.In(time.FixedZone("x", -2670))},
		{"FixedZone(\"\", +30) [+00:00:30]", base.In(time.FixedZone("", 30))},
		{"Africa/Monrovia 1970-01-01T12:00:00Z [LMT-ish -00:44:30]", time.Date(1970, 1, 1, 12, 0, 0, 0, time.UTC).In(monrovia)},
		{"Europe/Paris 1850-01-01T00:00:00 [LMT +00:09:21]", time.Date(1850, 1, 1, 0, 0, 0, 0, paris)},
		{"FixedZone(\"\", 25h) [+25:00]", base.In(time.FixedZone("", 25*3600))},
		{"FixedZone(\"\", 24h) [+24:00]", base.In(time.FixedZone("", 24*3600))},
		{"year 0 UTC", time.Date(0, 1, 1, 0, 0, 0, 0, time.UTC)},
		{"year 12 UTC", time.Date(12, 1, 1, 0, 0, 0, 0, time.UTC)},
		{"year 9999 UTC", time.Date(9999, 12, 31, 23, 59, 59, 0, time.UTC)},
		{"year 10000 UTC", time.Date(10000, 1, 1, 0, 0, 0, 0, time.UTC)},
		{"year -1 UTC", time.Date(-1, 1, 1, 0, 0, 0, 0, time.UTC)},
		{"nanos .123456789", base.Add(123456789)},
		{"nanos .123000000 (trailing zeros)", base.Add(123000000)},
		{"nanos .000000001", base.Add(1)},
		{"whole seconds (nsec=0)", base},
		{"time.Time{} zero value", time.Time{}},
		{"time.Date(..., sec=60) [leap second attempt]", time.Date(2016, 12, 31, 23, 59, 60, 0, time.UTC)},
		{"Parse(\"+00:00\") re-emitted", mustParse("2026-09-24T12:00:00+00:00")},
		{"Parse(\"-00:00\") re-emitted", mustParse("2026-09-24T12:00:00-00:00")},
		{"Parse(\"-04:00\") (matches Local) re-emitted", mustParse("2026-09-24T08:00:00-04:00")},
	}
	type fmtr struct {
		name string
		fn   func(time.Time) (string, error)
	}
	fmts := []fmtr{
		{"Format(time.RFC3339)", func(t time.Time) (string, error) { return t.Format(time.RFC3339), nil }},
		{"Format(time.RFC3339Nano)", func(t time.Time) (string, error) { return t.Format(time.RFC3339Nano), nil }},
		{"MarshalJSON", func(t time.Time) (string, error) {
			b, err := t.MarshalJSON()
			return string(b), err
		}},
		{"MarshalText", func(t time.Time) (string, error) {
			b, err := t.MarshalText()
			return string(b), err
		}},
		{"json.Marshal(struct{T time.Time})", func(t time.Time) (string, error) {
			b, err := json.Marshal(wrap{t})
			return string(b), err
		}},
		{"String()", func(t time.Time) (string, error) { return t.String(), nil }},
	}
	for _, s := range samples {
		for _, f := range fmts {
			out, err := f.fn(s.t)
			rec := map[string]any{"lang": "go", "kind": "format", "sample": s.label, "call": f.name,
				"true_utc": utcString(s.t), "offset_seconds": func() int { _, o := s.t.Zone(); return o }()}
			if err != nil {
				rec["ok"], rec["err"] = false, err.Error()
			} else {
				rec["ok"], rec["out"] = true, out
			}
			enc.Encode(rec)
		}
	}
	// Extra layouts named in the skill's rfc3339-checks.md.
	local := base.In(time.Local)
	parisNow := base.In(paris)
	extra := []struct {
		label string
		t     time.Time
		out   string
	}{
		{"Local t.Format(\"2006-01-02T15:04:05Z\") [literal Z]", local, local.Format("2006-01-02T15:04:05Z")},
		{"Paris t.Format(\"2006-01-02T15:04:05-0700\")", parisNow, parisNow.Format("2006-01-02T15:04:05-0700")},
		{"Paris t.Format(\"2006-01-02T15:04:05Z0700\")", parisNow, parisNow.Format("2006-01-02T15:04:05Z0700")},
		{"Paris t.Format(time.DateTime)", parisNow, parisNow.Format(time.DateTime)},
		{"Paris t.Format(time.DateTime+\"Z07:00\")", parisNow, parisNow.Format(time.DateTime + "Z07:00")},
		{"Paris t.Format(time.RFC3339+\"[MST]\") n/a — plain RFC3339", parisNow, parisNow.Format(time.RFC3339)},
		{"t.Format(\"2006-01-02T15:04:05.000000000Z07:00\") [fixed 9]", base.Add(123000000), base.Add(123000000).Format("2006-01-02T15:04:05.000000000Z07:00")},
		{"t.Format(\"2006-01-02T15:04:05.000Z07:00\") [fixed 3]", base, base.Format("2006-01-02T15:04:05.000Z07:00")},
		{"Monrovia 1970 t.Format(\"2006-01-02T15:04:05Z07:00:00\")", time.Date(1970, 1, 1, 12, 0, 0, 0, time.UTC).In(monrovia), time.Date(1970, 1, 1, 12, 0, 0, 0, time.UTC).In(monrovia).Format("2006-01-02T15:04:05Z07:00:00")},
		{"Local t.UTC().Format(time.RFC3339)", local, local.UTC().Format(time.RFC3339)},
		{"year 10000 t.UTC().Format(time.RFC3339)", time.Date(10000, 1, 1, 0, 0, 0, 0, time.UTC), time.Date(10000, 1, 1, 0, 0, 0, 0, time.UTC).Format(time.RFC3339)},
	}
	for _, e := range extra {
		enc.Encode(map[string]any{"lang": "go", "kind": "format", "sample": e.label, "call": "custom layout", "true_utc": utcString(e.t), "ok": true, "out": e.out})
	}
}

func mustParse(s string) time.Time {
	t, err := time.Parse(time.RFC3339, s)
	if err != nil {
		panic(err)
	}
	return t
}

// adapterKeys maps run_vectors.py adapter keys to the probe APIs (index into apis;
// -1 = ParseRFC3339Strict). Every key is an RFC 3339-only consumer.
var adapterKeys = []struct {
	key string
	idx int
}{
	{"parse3339", 0}, {"parse3339nano", 1}, {"parseinlocation", 2}, {"unmarshaljson", 3},
	{"unmarshaltext", 4}, {"json", 5}, {"jsonv2", 6}, {"strict", -1},
}

// answer is one run_vectors.py result for input s.
func answer(idx int, s string) map[string]any {
	out := map[string]any{}
	var t time.Time
	var err error
	leap := false
	if idx < 0 {
		t, leap, err = ParseRFC3339Strict(s)
	} else {
		t, err = apis[idx].fn(s)
	}
	if err != nil {
		out["ok"], out["error"] = false, err.Error()
		return out
	}
	_, off := t.Zone()
	sec := t.Second()
	if leap {
		sec = 60
	}
	fields := map[string]any{
		"year": t.Year(), "month": int(t.Month()), "day": t.Day(),
		"hour": t.Hour(), "minute": t.Minute(), "second": sec,
		"offset_minutes": off / 60,
		"leap_second":    leap, // time.Time cannot hold second 60; only strict reports it
	}
	if ns := t.Nanosecond(); ns != 0 { // a zero fraction is omitted (".0" and none look the same)
		fields["secfrac"] = fmt.Sprintf("%09d", ns)
	}
	out["ok"] = true
	out["fields"] = fields
	out["utc"] = utcString(t)
	if off%60 != 0 {
		out["note"] = fmt.Sprintf("offset has %d s", off)
	}
	return out
}

// adapter implements the run_vectors.py protocol: one string on stdin, or
// JSON lines when RFCDT_BATCH=1 (one result line per request, id echoed).
func adapter(which string) {
	idx, found := 0, false
	for _, k := range adapterKeys {
		if k.key == which {
			idx, found = k.idx, true
		}
	}
	e := json.NewEncoder(os.Stdout)
	e.SetEscapeHTML(false)
	if !found {
		fmt.Fprintf(os.Stderr, "unknown adapter key %q; see: gorfc list\n", which)
		os.Exit(2)
	}
	if os.Getenv("RFCDT_BATCH") == "1" {
		b, _ := io.ReadAll(os.Stdin)
		for _, line := range strings.Split(string(b), "\n") {
			if strings.TrimSpace(line) == "" {
				continue
			}
			var req struct {
				ID    string `json:"id"`
				Input string `json:"input"`
			}
			if err := json.Unmarshal([]byte(line), &req); err != nil {
				e.Encode(map[string]any{"ok": false, "error": "bad request line: " + err.Error()})
				continue
			}
			out := answer(idx, req.Input)
			out["id"] = req.ID
			e.Encode(out)
		}
		return
	}
	b, _ := io.ReadAll(os.Stdin)
	e.Encode(answer(idx, string(b)))
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: gorfc probe|produce|list|adapter <api>")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "probe":
		probe()
	case "produce":
		produce()
	case "list":
		for _, k := range adapterKeys {
			fmt.Printf("%s\trfc3339\n", k.key)
		}
	case "adapter":
		w := ""
		if len(os.Args) > 2 {
			w = os.Args[2]
		}
		adapter(w)
	default:
		os.Exit(2)
	}
}
