#!/usr/bin/env python3
"""Run the conformance vectors against every ecosystem probe adapter.

    python3 probes/run_vector_probes.py --list                      # languages and programs
    python3 probes/run_vector_probes.py --lang python --build-dir "$SCRATCH"
    python3 probes/run_vector_probes.py --lang all --build-dir "$SCRATCH" --build \\
        --out evals/baselines/probes/vector-runs --json-dir "$SCRATCH/json"

Each probe program has an ``adapter <key>`` mode that speaks the
scripts/run_vectors.py adapter protocol (per-process AND batch) and a
``list`` mode that prints one ``<key><TAB><target-kind>`` line per API
(target-kind = rfc3339 | ixdtf | both, as for ``--target-kind``).  This
script asks each program for its keys, then runs::

    run_vectors.py --target "<program> adapter <key>" --batch \\
        --target-kind <kind> --target-options fixed --target-has-tzdata yes

with ``TZ=America/New_York`` (the host zone of the original probe runs, so a
parser that falls back to local time shows up in the fields), and writes one
summary per language, ``<out>/<lang>.txt``: a totals table per key, then each
key's text report.  Build and scratch paths are replaced by ``<build>`` and
``<skill>`` so the files carry no machine paths.

Instant-only adapters (``"instant": True``: Swift Foundation ``Date``, SQL
timestamps, protobuf ``Timestamp``, and the Java adapter, which reports only
``utc``) keep no offset, so they return a UTC
instant (``"utc"``, or protobuf ``seconds``/``nanos``) instead of the
as-written ``fields``.  For those keys the JSON report is also passed to
``probes/swift/instant_check.py``, which compares each accepted vector's
instant with rfcdt's; its mismatch lines and counts are appended to the key's
report and to an "Instant check" table in the summary.

``--build`` runs each program's build commands first (compiled languages
write only under ``--build-dir``).  Programs whose runtime or libraries are
missing are reported as skipped with the reason (``list`` failing, or a
``requires`` check failing).
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RUNNER = os.path.join(ROOT, "scripts", "run_vectors.py")
INSTANT_CHECK = os.path.join(HERE, "swift", "instant_check.py")
PY = shlex.quote(sys.executable)

# lang -> list of programs.  {probes} = this directory, {build} = --build-dir.
# "cmd" is the program prefix: "<cmd> list" and "<cmd> adapter <key>".
PROGRAMS = {
    "python": [
        {"name": "python", "cmd": "python3 {probes}/probe_python.py",
         "version": "python3 --version"},
    ],
    "js": [
        {"name": "js", "cmd": "node {probes}/probe_js.mjs", "version": "node --version"},
    ],
    "ruby": [
        {"name": "ruby", "cmd": "ruby {probes}/probe_ruby.rb", "version": "ruby --version"},
    ],
    "java": [
        {"name": "java", "instant": True, "build": ["javac -d {build}/java {probes}/Probe.java"],
         "cmd": "java -cp {build}/java Probe", "version": "java --version"},
    ],
    "dotnet": [
        {"name": "dotnet",
         "build": ["dotnet build {probes}/probe_dotnet.cs -c Release -o {build}/dotnet"],
         "cmd": "dotnet {build}/dotnet/probe_dotnet.dll", "version": "dotnet --version"},
    ],
    "go": [
        {"name": "go", "build": ["cd {probes}/go && go build -o {build}/gorfc ."],
         "cmd": "{build}/gorfc", "version": "go version"},
    ],
    "rust": [
        {"name": "rust",
         "build": ["cargo build --release --quiet --manifest-path {probes}/rust/rfc-eval/Cargo.toml "
                   "--target-dir {build}/rust-target"],
         "cmd": "{build}/rust-target/release/adapter", "version": "rustc --version"},
    ],
    "swift": [
        {"name": "swift", "instant": True,
         "build": ["swiftc -O -o {build}/swiftrfc {probes}/swift/main.swift {probes}/swift/RFC3339Strict.swift"],
         "cmd": "{build}/swiftrfc", "version": "swiftc --version"},
    ],
    "sql": [
        {"name": "sqlite", "instant": True, "cmd": "python3 {probes}/sql/probe_sqlite.py",
         "version": "python3 -c \"import sqlite3; print('SQLite', sqlite3.sqlite_version)\""},
        # needs a running server (PGHOST/PGPORT/PGUSER, default 127.0.0.1:54329 postgres;
        # throwaway cluster: probes/sql/probe_pg.py docstring) and psycopg 3 or psql
        {"name": "postgres", "instant": True, "cmd": "python3 {probes}/sql/probe_pg.py",
         "requires": "pg_isready -q -h \"${PGHOST:-127.0.0.1}\" -p \"${PGPORT:-54329}\"",
         "version": "psql -X -A -t -h \"${PGHOST:-127.0.0.1}\" -p \"${PGPORT:-54329}\" -U \"${PGUSER:-postgres}\" "
                    "-c 'SHOW server_version'"},
    ],
    "protobuf": [
        {"name": "protobuf-go", "instant": True, "build": ["cd {probes}/protobuf/go && go build -o {build}/pbrfc ."],
         "cmd": "{build}/pbrfc", "version": "go version"},
        {"name": "protobuf-py", "instant": True, "cmd": "python3 {probes}/protobuf/probe_protobuf.py",
         "requires": "python3 -c 'import google.protobuf'",
         "version": "python3 -c \"import google.protobuf as p; print('protobuf', p.__version__)\""},
    ],
    "jsonschema": [
        {"name": "jsonschema-go", "build": ["cd {probes}/jsonschema/go && go build -o {build}/jsprobe ."],
         "cmd": "{build}/jsprobe", "version": "go version"},
        # python-jsonschema: install jsonschema[format] (rfc3339-validator) into the python3 on PATH
        {"name": "jsonschema-py", "cmd": "python3 {probes}/jsonschema/py_adapter.py",
         "requires": "python3 -I -c 'import jsonschema.validators'",
         "version": "python3 -I -c \"import jsonschema, importlib.metadata as m; print('jsonschema', m.version('jsonschema'))\""},
        # the same library WITHOUT rfc3339-validator ("format" silently not checked); lists no key otherwise
        {"name": "jsonschema-py-nodep", "cmd": "python3 {probes}/probe_jsonschema_nodep.py",
         "requires": "python3 -I -c 'import jsonschema.validators'",
         "version": "python3 -I -c \"import importlib.metadata as m; print('jsonschema', m.version('jsonschema'))\""},
        # (build strings go through str.format: literal braces are doubled)
        # JsonSchema.Net 9.4.0 must already be in the NuGet cache (restore needs network otherwise)
        {"name": "jsonschema-dotnet",
         "build": ["test -d ~/.nuget/packages/jsonschema.net || {{ echo 'JsonSchema.Net not in the NuGet "
                   "cache' >&2; exit 1; }}",
                   "dotnet build {probes}/jsonschema/dotnet/JsProbe.csproj -c Release "
                   "--artifacts-path {build}/jsprobe-dotnet"],
         "cmd": "dotnet {build}/jsprobe-dotnet/bin/JsProbe/release/JsProbe.dll", "version": "dotnet --version"},
        # networknt json-schema-validator: NETWORKNT_LIB = directory of the jars listed in JsonSchemaProbe.java
        {"name": "jsonschema-java",
         "build": ["test -d \"$NETWORKNT_LIB\" || {{ echo 'set NETWORKNT_LIB to the networknt jar directory' >&2; "
                   "exit 1; }}",
                   "javac -cp \"$NETWORKNT_LIB/*\" -d {build}/jsprobe-java {probes}/jsonschema/JsonSchemaProbe.java"],
         "requires": "test -d \"$NETWORKNT_LIB\"",
         "cmd": "java -cp \"{build}/jsprobe-java:$NETWORKNT_LIB/*\" JsonSchemaProbe", "version": "java --version"},
    ],
}

FLAGS = ["--batch", "--target-options", "fixed", "--target-has-tzdata", "yes"]
TOTAL_KEYS = ("pass", "too-lenient", "too-strict", "wrong-value", "error", "interpretation", "skip", "total")


def fmt(t, build):
    return t.format(probes=shlex.quote(HERE), build=shlex.quote(build))


def sanitize(text, build):
    for p, rep in ((os.path.realpath(build), "<build>"), (os.path.abspath(build), "<build>"),
                   (os.path.realpath(ROOT), "<skill>"), (ROOT, "<skill>"),
                   (os.path.expanduser("~"), "~")):
        text = text.replace(p, rep)
    return text


def sh(cmd, env=None, timeout=1800, input=None):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env,
                          timeout=timeout, input=input)


_EPOCH = datetime(1970, 1, 1)
_INSTANT_RE = re.compile(r"instant check: (\d+) accepted vectors compared, (\d+) WRONG VALUE, "
                         r"(\d+) lossy \(< \d+ us\), (\d+) leap seconds")


def _with_utc(rep):
    """Copy of a --json report where protobuf ``seconds``/``nanos`` answers also
    carry the ``utc`` string instant_check.py reads."""
    rep = json.loads(json.dumps(rep))
    for r in rep.get("results", []):
        out = r.get("output")
        u = out.get("utc") if isinstance(out, dict) else None
        if isinstance(u, str):
            if u.startswith("naive:"):          # no instant (offset discarded): not comparable
                del out["utc"]
            else:                               # Java prints Instant.toString(): "+YYYYY-…Z"
                out["utc"] = u[:-1].lstrip("+") if u.endswith("Z") else u.lstrip("+")
        if (isinstance(out, dict) and out.get("ok") and "utc" not in out
                and isinstance(out.get("seconds"), int)):
            try:
                t = _EPOCH + timedelta(seconds=out["seconds"])
            except OverflowError:
                continue
            out["utc"] = f"{t:%Y-%m-%dT%H:%M:%S}.{int(out.get('nanos') or 0):09d}"
    return rep


def instant_check(rep, env):
    """Run instant_check.py on ``rep``; returns (counts dict or None, output text)."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(_with_utc(rep), fh)
        path = fh.name
    try:
        cp = subprocess.run([sys.executable, INSTANT_CHECK, path], capture_output=True, text=True, env=env)
    finally:
        os.unlink(path)
    text = (cp.stdout + cp.stderr).rstrip()
    # shorten very long quoted inputs (e.g. the 1050-digit fraction vectors)
    text = re.sub(r'"([^"\n]{60})[^"\n]{20,}"', lambda m: f'"{m.group(1)}…"', text)
    m = _INSTANT_RE.search(text)
    counts = None if not m else dict(zip(("compared", "wrong", "lossy", "leap"), map(int, m.groups())))
    return counts, text


def run_program(prog, build, env, json_dir, do_build):
    """Return (header lines, rows, reports) for one program."""
    name = prog["name"]
    if do_build:
        for b in prog.get("build", []):
            cp = sh(fmt(b, build), env=env)
            if cp.returncode:
                return [f"{name}: SKIPPED (build failed: {sanitize(cp.stderr.strip()[-300:], build)})"], [], []
    if prog.get("requires") and sh(prog["requires"], env=env).returncode:
        return [f"{name}: SKIPPED (missing runtime library: `{prog['requires']}` failed)"], [], []
    cmd = fmt(prog["cmd"], build)
    cp = sh(cmd + " list", env=env)
    if cp.returncode:
        return [f"{name}: SKIPPED (`list` failed: {sanitize(cp.stderr.strip()[-300:], build)})"], [], []
    ver = sh(prog["version"], env=env) if prog.get("version") else None
    head = [f"{name}: {(ver.stdout or ver.stderr).strip().splitlines()[0] if ver else '?'}"]
    rows, reports = [], []
    for line in cp.stdout.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        key, _, kind = line.partition("\t")
        key, kind = key.strip(), (kind.strip() or "both")
        target = f"{cmd} adapter {shlex.quote(key)}"
        args = [sys.executable, RUNNER, "--target", target, "--target-kind", kind] + FLAGS
        text = subprocess.run(args, capture_output=True, text=True, env=env).stdout
        js = subprocess.run(args + ["--json"], capture_output=True, text=True, env=env).stdout
        try:
            rep = json.loads(js)
            tot = rep["totals"]
        except ValueError:
            rep, tot = None, {}
        if json_dir and rep:
            os.makedirs(json_dir, exist_ok=True)
            with open(os.path.join(json_dir, f"{name}--{re.sub(r'[^A-Za-z0-9_.-]', '_', key)}.json"),
                      "w", encoding="utf-8") as fh:
                fh.write(sanitize(json.dumps(rep, ensure_ascii=False, indent=1), build))
        inst = None
        if prog.get("instant") and rep:
            inst, itext = instant_check(rep, env)
            text = text.rstrip() + "\n\nInstant check (probes/swift/instant_check.py):\n" + itext + "\n"
        rows.append((f"{name}:{key}", kind, tot, inst))
        reports.append((f"{name}:{key}", kind, sanitize(text, build)))
    return head, rows, reports


def render(lang, heads, rows, reports, sha, count):
    out = [f"Vector runs: {lang}  (probes/run_vector_probes.py; vectors/vectors.json sha256 {sha[:16]}..., "
           f"{count} vectors)",
           "runner flags: " + " ".join(FLAGS) + " --target-kind <kind>; TZ=America/New_York", ""]
    out += heads + [""]
    w = max([len(r[0]) for r in rows] + [10])
    out.append(f"{'program:key':<{w}}  {'kind':<7} " + " ".join(f"{k[:7]:>7}" for k in TOTAL_KEYS) + "   pass%")
    for key, kind, t, _ in rows:
        scored = t.get("scored") or 0
        pct = f"{100.0 * t.get('pass', 0) / scored:6.1f}" if scored else "     -"
        out.append(f"{key:<{w}}  {kind:<7} " + " ".join(f"{t.get(k, '?'):>7}" for k in TOTAL_KEYS) + "  " + pct)
    inst = [(key, i) for key, _, _, i in rows if i is not None]
    if inst:
        out += ["", "Instant check (probes/swift/instant_check.py; accepted vectors whose UTC instant is "
                "compared with rfcdt's; lossy = below the 1 ms tolerance; leap = second 60 mapped to :59 "
                "or the next second)",
                f"{'program:key':<{w}}  " + " ".join(f"{k:>8}" for k in ("compared", "wrong", "lossy", "leap"))]
        for key, i in inst:
            out.append(f"{key:<{w}}  " + " ".join(f"{i[k]:>8}" for k in ("compared", "wrong", "lossy", "leap")))
    for key, kind, text in reports:
        out += ["", "=" * 78, f"{key}  (--target-kind {kind})", "=" * 78, text.rstrip()]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", default="all", help="comma list of " + ", ".join(PROGRAMS) + " or all")
    ap.add_argument("--build-dir", default=os.environ.get("PROBE_BUILD_DIR", ""),
                    help="where compiled adapters live (required for compiled languages)")
    ap.add_argument("--build", action="store_true", help="run build commands first")
    ap.add_argument("--out", default=os.path.join(ROOT, "evals", "baselines", "probes", "vector-runs"))
    ap.add_argument("--json-dir", help="also save each key's run_vectors.py --json report here")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    if a.list:
        for lang, progs in PROGRAMS.items():
            for p in progs:
                print(f"{lang:<11} {p['name']:<20} {p['cmd']}")
        return 0
    langs = list(PROGRAMS) if a.lang == "all" else a.lang.split(",")
    build = os.path.abspath(a.build_dir or os.path.join(ROOT, ".probe-build"))
    os.makedirs(build, exist_ok=True)
    env = dict(os.environ, TZ="America/New_York")
    with open(os.path.join(ROOT, "vectors", "vectors.json"), "rb") as fh:
        import hashlib
        raw = fh.read()
    sha, count = hashlib.sha256(raw).hexdigest(), len(json.loads(raw)["vectors"])
    os.makedirs(a.out, exist_ok=True)
    for lang in langs:
        heads, rows, reports = [], [], []
        for prog in PROGRAMS[lang]:
            h, r, rep = run_program(prog, build, env, a.json_dir, a.build)
            heads += h
            rows += r
            reports += rep
        path = os.path.join(a.out, f"{lang}.txt")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render(lang, heads, rows, reports, sha, count))
        print(f"{lang}: {len(rows)} keys -> {os.path.relpath(path, ROOT)}")
        for h in heads:
            if "SKIPPED" in h:
                print("  " + h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
