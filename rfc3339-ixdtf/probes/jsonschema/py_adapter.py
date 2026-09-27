#!/usr/bin/env python3
"""python-jsonschema adapter for run_vectors.py (stdin = one string, stdout = {"ok": ...}).

  <venv>/bin/python py_adapter.py [adapter] assert|default|draft7|pattern|pattern-nl|date|time
  <venv>/bin/python py_adapter.py list      (date-time variants: <key>\\t<target-kind>)
RFCDT_BATCH=1: JSON lines {"id", "input", ...} in, one result line per input (run_vectors.py --batch).
assert: Draft202012Validator(format_checker=Draft202012Validator.FORMAT_CHECKER), format date-time.
default: Draft202012Validator with no format_checker (the library default).
draft7: Draft7Validator with no format_checker.
pattern: assert + the strict RFC 3339 "pattern" from ecosystem.md.
pattern-nl: pattern + "not": {"pattern": "\n"} (Python re `$` also matches before a final newline).
date / time: format date / time (not listed: the vectors are date-time strings).
Install `jsonschema[format]` (pulls rfc3339-validator) for date-time/time checks; without it they are skipped.
"""
import json, os, sys

LISTED = ["assert", "default", "draft7", "pattern", "pattern-nl"]
VARIANTS = LISTED + ["date", "time"]


def validator(variant):
    from jsonschema import Draft202012Validator, Draft7Validator
    fmt = variant if variant in ("date", "time") else "date-time"
    cls = Draft7Validator if variant == "draft7" else Draft202012Validator
    schema = {"$schema": cls.META_SCHEMA["$schema"], "type": "string", "format": fmt}
    if variant in ("pattern", "pattern-nl"):
        schema["pattern"] = r"^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])[Tt]([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)([.][0-9]+)?([Zz]|[+-]([01][0-9]|2[0-3]):[0-5][0-9])$"
    if variant == "pattern-nl":
        schema["not"] = {"pattern": "\n"}
    kw = {} if variant in ("default", "draft7") else {"format_checker": cls.FORMAT_CHECKER}
    v = cls(schema, **kw)

    def check(s):
        try:
            errs = list(v.iter_errors(s))
            return {"ok": not errs, **({"error": errs[0].message} if errs else {})}
        except Exception as e:
            return {"ok": False, "error": repr(e)}
    return check


def main(argv):
    if argv[:1] == ["list"]:
        import jsonschema.validators  # noqa: F401  (fail here when the library is missing)
        for k in LISTED:
            print(f"{k}\trfc3339")
        return 0
    if argv[:1] == ["adapter"]:
        argv = argv[1:]
    variant = argv[0] if argv else "assert"
    if variant not in VARIANTS:
        print(f"unknown variant {variant!r}; see: py_adapter.py list", file=sys.stderr)
        return 2
    check = validator(variant)
    if os.environ.get("RFCDT_BATCH") == "1":
        for line in sys.stdin:
            if line.strip():
                req = json.loads(line)
                print(json.dumps({"id": req["id"], **check(req["input"])}), flush=True)
    else:
        print(json.dumps(check(sys.stdin.buffer.read().decode("utf-8", "surrogateescape"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
