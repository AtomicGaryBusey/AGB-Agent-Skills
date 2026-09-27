# Ecosystem probes

Programs behind `references/ecosystem/*.md`. Each language probe has two jobs:

1. **Vector adapter (grading).** `adapter <key>` speaks the
   `scripts/run_vectors.py` adapter protocol (per-process and `--batch`), so an
   API is graded against all conformance vectors in `vectors/vectors.json`,
   the same way an audit grades a target. `list` prints one
   `<key><TAB><target-kind>` line per API.
2. **Legacy probe (tables).** The original JSON-lines probe over
   `probes/inputs.json`, turned into tables by `probes/analyze.py` (and the
   per-language analyzers). Kept for the formatter/producer rows and for the
   original table column ids.

## Inputs

`probes/inputs.json` is generated; do not edit it by hand:

    python3 tools/gen_probe_inputs.py          # regenerate after vectors.json changes
    python3 tools/gen_probe_inputs.py --check  # exit 1 if stale (scripts/test_vectors.py runs this)

Schema 2: `inputs` has one entry per vector (`vector`, `s`, `expect`,
`profile`, `options`, `requires`, `checks`, ...); `legacy` keeps the original
2026-09-24 probe strings that have no byte-identical vector, with
`related_vectors` (same profile and rfcdt reason code). Legacy probes read
`inputs + legacy`; they also accept the old list form.

## Grading every API: `run_vector_probes.py`

    S=/path/to/scratch
    python3 probes/run_vector_probes.py --list
    python3 probes/run_vector_probes.py --lang all --build --build-dir "$S/build" --json-dir "$S/json"
    python3 probes/run_vector_probes.py --lang go,rust --build-dir "$S/build"   # already built

For every program and key it runs

    run_vectors.py --target "<program> adapter <key>" --batch --target-kind <kind> \
        --target-options fixed --target-has-tzdata yes

with `TZ=America/New_York`, and writes `evals/baselines/probes/vector-runs/<lang>.txt`
(totals per key, then each key's text report; build and skill paths are
replaced by `<build>` and `<skill>`). `--build` writes compiled adapters only
under `--build-dir`. A program whose runtime or library is missing is listed
as SKIPPED with the reason.

`--target-options fixed`: probe adapters implement one fixed policy (the
library's own), so vectors with non-default `options` are skipped.
`--target-kind rfc3339` means the API has no suffix parser (ixdtf vectors are
not applicable); `ixdtf` marks suffix-aware APIs (Temporal, jiff Zoned,
java.time `ZonedDateTime`, ...).

## Per-language commands

One adapter by hand (any key from `list`):

| Lang | Build (into `$B`) | Adapter command | Legacy probe |
|---|---|---|---|
| python | - | `python3 probes/probe_python.py adapter <key>` | `TZ=America/New_York python3 probes/probe_python.py > python.jsonl` |
| js | - | `node probes/probe_js.mjs adapter <key>` | `TZ=America/New_York node probes/probe_js.mjs > js.jsonl` |
| ruby | - | `ruby probes/probe_ruby.rb adapter <key>` | `TZ=America/New_York ruby probes/probe_ruby.rb > ruby.jsonl` |
| java | `javac -d $B/java probes/Probe.java` | `java -cp $B/java Probe adapter <key>` | `java -cp $B/java Probe` |
| dotnet | `dotnet build probes/probe_dotnet.cs -c Release -o $B/dotnet` | `dotnet $B/dotnet/probe_dotnet.dll adapter <key>` | `dotnet $B/dotnet/probe_dotnet.dll probe probes` |
| go | `(cd probes/go && go build -o $B/gorfc .)` | `$B/gorfc adapter <key>` | `$B/gorfc probe < probes/inputs.json` |
| rust | `cargo build --release --manifest-path probes/rust/rfc-eval/Cargo.toml --target-dir $B/rust-target` | `$B/rust-target/release/adapter adapter <key>` (old form `adapter <key>` also works) | `$B/rust-target/release/probe probes/inputs.json` |
| swift | `swiftc -O -o $B/swiftrfc probes/swift/main.swift probes/swift/RFC3339Strict.swift` | `$B/swiftrfc adapter <key>` | `$B/swiftrfc probe probes/inputs.json` |
| sql (SQLite) | - | `python3 probes/sql/probe_sqlite.py adapter <key>` | `python3 probes/sql/probe_sqlite.py probe` |
| sql (PostgreSQL) | throwaway cluster on 127.0.0.1:54329 (see `probe_pg.py`); uses psycopg or `psql` | `python3 probes/sql/probe_pg.py adapter <key>` | `python3 probes/sql/probe_pg.py probe` |
| protobuf (Go) | `(cd probes/protobuf/go && go build -o $B/pbrfc .)` | `$B/pbrfc adapter unmarshal` | `$B/pbrfc probe < probes/inputs.json` |
| protobuf (Python) | `pip install protobuf` | `python3 probes/protobuf/probe_protobuf.py adapter <key>` | `... probe < probes/inputs.json` |
| jsonschema (Go) | `(cd probes/jsonschema/go && go build -o $B/jsprobe .)` | `$B/jsprobe adapter <variant>` | `probes/jsonschema/probe_all.py` |
| jsonschema (Python) | `pip install 'jsonschema[format]'` | `python3 probes/jsonschema/py_adapter.py adapter <variant>` | `probes/jsonschema/probe_all.py` |
| jsonschema (.NET, Java) | see `run_vector_probes.py` (JsonSchema.Net from NuGet; networknt jars in `$NETWORKNT_LIB`) | `... adapter <variant>` | `probes/jsonschema/probe_all.py` |

Every command above takes `list` in place of `adapter <key>`. Example of a single run:

    run_vectors.py --target "$B/gorfc adapter strict" --batch --target-kind rfc3339 \
        --target-options fixed --target-has-tzdata yes

Adapters report only the fields the API's result exposes (local wall-clock
fields, `offset_minutes`, `time_zone`, `effective_tags`). APIs that return
only an instant (JS `Date`, `Temporal.Instant`, Swift Foundation, SQL,
protobuf) return no fields, so a wrong instant is not visible to
`run_vectors.py`. Check those with `probes/swift/instant_check.py` over the
`--json-dir` reports (it compares the adapters' `utc` key).

`servicenow/` has its own README.
