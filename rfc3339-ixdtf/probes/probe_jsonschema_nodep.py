#!/usr/bin/env python3
"""Shows that python-jsonschema silently skips format "date-time" unless the optional
rfc3339-validator package is installed (pip install jsonschema, *without* the [format] extra).

Usage: <venv-with-only-jsonschema>/bin/python probe_jsonschema_nodep.py [demo]
       ... probe_jsonschema_nodep.py list             (<key>\\t<target-kind>; lists nothing when
                                                       rfc3339-validator IS installed: not applicable)
       ... probe_jsonschema_nodep.py adapter formatchecker-nodep
           (run_vectors.py adapter: one string on stdin, or JSON lines with RFCDT_BATCH=1)
"""
import json
import os
import sys

# Run from probes/, `import jsonschema` would find the probes/jsonschema/ directory.
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
import jsonschema  # noqa: E402

KEY = "formatchecker-nodep"


def demo():
    fc = jsonschema.FormatChecker()
    print("date-time checker registered:", "date-time" in fc.checkers)
    for kw in ({"format_checker": fc}, {}):
        try:
            jsonschema.validate("not a date", {"type": "string", "format": "date-time"}, **kw)
            print("accepted 'not a date'", "with FormatChecker" if kw else "without format_checker")
        except jsonschema.ValidationError as e:
            print("rejected:", e.message)


def answer(s, fc=jsonschema.FormatChecker()):
    try:
        jsonschema.validate(s, {"type": "string", "format": "date-time"}, format_checker=fc)
        return {"ok": True}
    except jsonschema.ValidationError as e:
        return {"ok": False, "error": e.message}


def main(argv):
    cmd = argv[0] if argv else "demo"
    if cmd == "demo":
        demo()
    elif cmd == "list":
        if "date-time" not in jsonschema.FormatChecker().checkers:
            print(f"{KEY}\trfc3339")
    elif cmd == "adapter" and argv[1:] == [KEY]:
        if os.environ.get("RFCDT_BATCH") == "1":
            for line in sys.stdin:
                if line.strip():
                    req = json.loads(line)
                    print(json.dumps({"id": req["id"], **answer(req["input"])}), flush=True)
        else:
            print(json.dumps(answer(sys.stdin.buffer.read().decode("utf-8", "surrogateescape"))))
    else:
        print(__doc__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
