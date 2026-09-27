#!/usr/bin/env python3
"""Re-validate a skill against its SOURCES.lock (T4-11, T4-12).

One file serves both skills; the profile comes from the `name:` in SKILL.md.

  rfc3339-ixdtf  errata pages for RFC 3339 and RFC 9557 and the IANA Internet
                 Date/Time Format registry (network); rfcdt selfcheck (tzdata,
                 leap-seconds expiry, ICU calendars); unit suite; built-in
                 conformance vectors; gen_vectors --check; local toolchain
                 versions and upstream latest releases against the versions
                 that references/ecosystem/README.md says were probed.
  iso999         unit suite and golden tests; tool versions and sha256 of the
                 linters, golden.json and the golden corpus; licence guard.
                 The iso999 profile never touches the network and never opens
                 the licensed ISO PDF.

Usage:
  python3 tools/revalidate.py                 # --check (default)
  python3 tools/revalidate.py --update        # rewrite SOURCES.lock
  python3 tools/revalidate.py --offline       # skip network sources
  python3 tools/revalidate.py --lock PATH --report PATH

Exit status: 0 = no change against the lock, 1 = drift, 2 = error (a source
could not be read, a lock is missing or unreadable, or --update refused).
Standard library only.
"""

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request

__version__ = "1.0.0"

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
UA = "skill-revalidate/%s (local maintenance script; stdlib urllib)" % __version__
NET_TIMEOUT = 30
LOCK_SCHEMA = 1

# ---------------------------------------------------------------------------
# helpers


class SourceError(Exception):
    pass


def today():
    return _dt.date.today().isoformat()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_tree(path):
    """sha256 of a file, or of a directory's sorted (relpath, file sha) list."""
    if os.path.isfile(path):
        return sha256_file(path)
    h = hashlib.sha256()
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, path)
            h.update(("%s\0%s\n" % (rel, sha256_file(full))).encode())
    return h.hexdigest()


def run(cmd, cwd=None, timeout=900):
    """Run a command; return (exit code, stdout, stderr). Missing binary -> None code."""
    try:
        cp = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True,
                            timeout=timeout, stdin=subprocess.DEVNULL)
        return cp.returncode, cp.stdout, cp.stderr
    except FileNotFoundError:
        return None, "", "not found: %s" % cmd[0]
    except subprocess.TimeoutExpired:
        return None, "", "timeout after %ss: %s" % (timeout, " ".join(cmd))


def fetch(url, allow_network):
    if not allow_network:
        raise SourceError("network fetch attempted in a no-network profile: %s" % url)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=NET_TIMEOUT) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001 - any network failure is a source error
        raise SourceError("fetch failed: %s: %s" % (url, exc))


def skill_frontmatter(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise SourceError("SKILL.md has no front matter")
    fm = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"\s*([A-Za-z_][\w-]*):\s*(.*)$", line)
        if mm and mm.group(2):
            fm[mm.group(1)] = mm.group(2).strip().strip('"')
    return fm


def py_version_of(path, var="__version__"):
    with open(path, encoding="utf-8") as fh:
        m = re.search(r"^%s\s*=\s*['\"]([^'\"]+)['\"]" % re.escape(var), fh.read(), re.M)
    return m.group(1) if m else None


def unittest_run(args, cwd):
    """Run python -m unittest; return a summary dict."""
    code, out, err = run([sys.executable, "-m", "unittest"] + args, cwd=cwd)
    text = out + err
    ran = re.findall(r"^Ran (\d+) tests?", text, re.M)
    tail = re.findall(r"^(OK|FAILED)(?: \(([^)]*)\))?\s*$", text, re.M)
    res = {"exit": code, "ran": int(ran[-1]) if ran else None,
           "result": tail[-1][0] if tail else "UNKNOWN"}
    for part in (tail[-1][1].split(", ") if tail and tail[-1][1] else []):
        k, _, v = part.partition("=")
        if v.isdigit():
            res[k] = int(v)
    if res["result"] != "OK":
        res["tail"] = "\n".join(text.strip().splitlines()[-25:])
    return res


def vtuple(v):
    """Comparable version key; tz releases like 2026c sort by their letter too."""
    v = v or ""
    m = re.fullmatch(r"(\d{4})([a-z])", v)
    if m:
        return (int(m.group(1)), ord(m.group(2)))
    return tuple(int(x) for x in re.findall(r"\d+", v))


# ---------------------------------------------------------------------------
# rfc3339-ixdtf profile

ERRATA_URL = "https://www.rfc-editor.org/errata/%s"
IANA_URL = ("https://www.iana.org/assignments/internet-date-time-format/"
            "internet-date-time-format.xml")

# local command -> (ecosystem file, component name in the file map)
LOCAL_TOOLS = {
    "python": ([sys.executable, "--version"], r"Python (\S+)", "python.md", "Python"),
    "node": (["node", "--version"], r"v(\S+)", "javascript.md", "Node"),
    "java": (["java", "-version"], r'version "([^"]+)"', "java.md", "Temurin"),
    "dotnet": (["dotnet", "--version"], r"^(\S+)", "dotnet.md", ".NET SDK"),
    "ruby": (["ruby", "--version"], r"ruby (\S+)", "ruby.md", "Ruby"),
    "go": (["go", "version"], r"go(\d\S*)", "go.md", "Go"),
    "rustc": (["rustc", "--version"], r"rustc (\S+)", "rust.md", "Rust"),
    "swift": (["swift", "--version"], r"Swift version (\S+)", "swift.md", "Swift"),
}

# upstream packages: (registry, package, ecosystem file, component)
UPSTREAM_PACKAGES = [
    ("crates", "chrono", "rust.md", "chrono"),
    ("crates", "time", "rust.md", "time"),
    ("crates", "jiff", "rust.md", "jiff"),
    ("pypi", "pydantic", "python.md", "pydantic"),
    ("pypi", "python-dateutil", "python.md", "python-dateutil"),
    ("pypi", "jsonschema", "python.md", "jsonschema"),
    ("npm", "ajv", "javascript.md", "ajv"),
    ("npm", "ajv-formats", "javascript.md", "ajv-formats"),
]


def parse_errata(html):
    parts = re.split(r'Errata-ID:\s*<a href="/eid(\d+)/?">\s*\d+\s*</a>', html)
    items = {}
    for i in range(1, len(parts), 2):
        eid, body = parts[i], parts[i + 1]

        def field(label):
            m = re.search(r"<dt[^>]*>\s*%s:\s*</dt>\s*<dd[^>]*>\s*<span[^>]*>\s*([^<]+?)\s*</span>"
                          % re.escape(label), body)
            return m.group(1) if m else None
        items[eid] = {"status": field("Status"), "type": field("Type"),
                      "reported": field("Date Reported")}
    if not items and "No errata" not in html and "no errata" not in html:
        raise SourceError("errata page parsed to zero entries (layout change?)")
    return items


def parse_iana(xml):
    # stdlib only (no defusedxml): refuse any DTD/entity declaration before parsing, so
    # XXE and entity-expansion payloads never reach expat. The real registry has none.
    import xml.etree.ElementTree as ET
    if re.search(r"<!(DOCTYPE|ENTITY)", xml, re.I) or len(xml) > 2_000_000:
        raise SourceError("IANA registry XML has a DTD/entity declaration or is oversized: refused")
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise SourceError("IANA registry XML: %s" % exc)
    ns = {"i": "http://www.iana.org/assignments"}
    out = {"created": root.findtext("i:created", namespaces=ns),
           "updated": root.findtext("i:updated", namespaces=ns), "registries": {}}
    for reg in root.findall("i:registry", ns):
        keys = {}
        for rec in reg.findall("i:record", ns):
            key = rec.findtext("i:key", namespaces=ns)
            keys[key] = {"status": rec.findtext("i:status", namespaces=ns),
                         "date": rec.get("date"),
                         "description": rec.findtext("i:description", namespaces=ns)}
        out["registries"][reg.get("id")] = keys
    if not out["registries"]:
        raise SourceError("IANA registry parsed to zero sub-registries")
    return out


def parse_file_map(path):
    """references/ecosystem/README.md 'File map' -> {file: {component: version}}."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    sec = re.search(r"^## File map\s*\n(.*?)(?=^## )", text, re.S | re.M)
    if not sec:
        raise SourceError("ecosystem README: no '## File map' section")
    probed = {}
    for line in sec.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not cells[0].startswith("`"):
            continue
        fname = cells[0].strip("`")
        raw = cells[-1].replace("`", "")
        comps = {}
        for tok in re.split(r"\s*(?:,|;|\(\+?|\))\s*|\s+/\s+",
                            re.sub(r"\s*\([^)\d]*\)", "", raw)):
            m = re.match(r"^(.*?)\s+v?(\d+(?:\.\d+)*(?:[.\-+][0-9A-Za-z]+)*)\b", tok.strip())
            if m and m.group(1):
                comps[m.group(1).strip()] = m.group(2)
        probed[fname] = comps
    tz = re.search(r"system tzdata (\S+?)[.)]?\s", text)
    return probed, (tz.group(1) if tz else None)


def upstream_versions(probed):
    """Latest releases upstream. Raises SourceError on the first failure."""
    up = {}
    up["tzdb"] = fetch("https://data.iana.org/time-zones/tzdb/version", True).strip()
    leap = fetch("https://data.iana.org/time-zones/tzdb/leap-seconds.list", True)
    m = re.search(r"^#@\s+(\d+)", leap, re.M)
    if m:
        ntp_epoch = _dt.datetime(1900, 1, 1, tzinfo=_dt.timezone.utc)
        up["leap_seconds_list_expires"] = (
            ntp_epoch + _dt.timedelta(seconds=int(m.group(1)))).date().isoformat()
    up["go"] = fetch("https://go.dev/VERSION?m=text", True).splitlines()[0].strip().lstrip("go")
    nodes = json.loads(fetch("https://nodejs.org/dist/index.json", True))
    node_major = vtuple(probed.get("javascript.md", {}).get("Node", ""))[:1]
    up["node"] = {"current": nodes[0]["version"].lstrip("v"),
                  "lts": next((n["version"].lstrip("v") for n in nodes if n.get("lts")), None)}
    if node_major:
        up["node"]["latest_in_probed_major"] = next(
            (n["version"].lstrip("v") for n in nodes
             if vtuple(n["version"])[:1] == node_major), None)
    idx = json.loads(fetch("https://builds.dotnet.microsoft.com/dotnet/release-metadata/"
                           "releases-index.json", True))["releases-index"]
    dn_major = ".".join(str(x) for x in vtuple(probed.get("dotnet.md", {}).get(".NET SDK", ""))[:2])
    up["dotnet"] = {"newest_channel": "%s (%s, %s)" % (idx[0]["channel-version"],
                                                       idx[0]["latest-sdk"], idx[0]["support-phase"])}
    for r in idx:
        if r["channel-version"] == dn_major:
            up["dotnet"]["latest_sdk_in_probed_channel"] = r["latest-sdk"]
    pk = {}
    for reg, name, _f, _c in UPSTREAM_PACKAGES:
        if reg == "crates":
            v = json.loads(fetch("https://crates.io/api/v1/crates/%s" % name, True))["crate"]["max_stable_version"]
        elif reg == "pypi":
            v = json.loads(fetch("https://pypi.org/pypi/%s/json" % name, True))["info"]["version"]
        else:
            v = json.loads(fetch("https://registry.npmjs.org/%s/latest" % name, True))["version"]
        pk["%s:%s" % (reg, name)] = v
    up["packages"] = pk
    return up


def collect_rfc(offline, errors, notes):
    live = {"skill": {}, "sources": {}, "local": {}, "upstream": None,
            "ecosystem_probed": {}, "artifacts": {}, "tests": {}}
    fm = skill_frontmatter(os.path.join(ROOT, "SKILL.md"))
    live["skill"] = {"name": fm.get("name"), "version": fm.get("version")}
    claimed = {}
    src = fm.get("sources", "")
    for rfc, ids in re.findall(r"RFC (\d+) \([^)]*\) \+ errat(?:a|um) ([\d,\s]+)", src):
        claimed["rfc" + rfc] = sorted(re.findall(r"\d+", ids), key=int)
    live["skill"]["claimed_errata"] = claimed

    # network sources
    if offline:
        live["sources"] = None
    else:
        try:
            errata = {}
            for rfc in ("rfc3339", "rfc9557"):
                errata[rfc] = parse_errata(fetch(ERRATA_URL % rfc, True))
            errata = {rfc: dict(sorted(items.items(), key=lambda kv: int(kv[0])))
                      for rfc, items in errata.items()}
            live["sources"] = {"errata": errata, "iana_internet_date_time_format": parse_iana(fetch(IANA_URL, True)),
                               "skill_md_errata_list_matches_live": {
                                   rfc: sorted(items, key=int) == claimed.get(rfc, [])
                                   for rfc, items in errata.items()}}
        except SourceError as exc:
            errors.append(str(exc))
            live["sources"] = None

    # selfcheck: tzdata, leap-seconds file, ICU calendars
    code, out, err = run([sys.executable, "scripts/rfcdt.py", "selfcheck", "--json"])
    try:
        sc = json.loads(out)
        live["local"]["tzdata"] = sc["meta"]["tz"].get("version")
        live["tests"]["selfcheck"] = {"exit": code, "status": sc["status"],
                                      "checks": {c["check"]: c["status"] for c in sc["checks"]}}
        for c in sc["checks"]:
            m = re.search(r"valid until (\d{4}-\d{2}-\d{2})", c.get("detail", ""))
            if c["check"] == "leap-seconds-expiry" and m:
                live["local"]["leap_seconds_file_expires"] = m.group(1)
                days = (_dt.date.fromisoformat(m.group(1)) - _dt.date.today()).days
                if days < 90:
                    notes.append("Local leap-seconds file expires in %d days (%s): update tzdata."
                                 % (days, m.group(1)))
            if c["status"] != "OK":
                notes.append("selfcheck %s: %s: %s" % (c["check"], c["status"], c.get("detail")))
    except (ValueError, KeyError) as exc:
        errors.append("rfcdt selfcheck output unreadable (exit %s): %s %s" % (code, exc, err.strip()[-300:]))

    # local toolchains
    tools = {}
    for name, (cmd, rx, _f, _c) in LOCAL_TOOLS.items():
        if cmd[0] != sys.executable and not shutil.which(cmd[0]):
            tools[name] = "absent"
            continue
        c, o, e = run(cmd, timeout=120)
        m = re.search(rx, o + e, re.M)
        tools[name] = m.group(1) if (c == 0 and m) else "error"
    if tools.get("node") not in ("absent", "error"):
        c, o, _ = run(["node", "-e", "process.stdout.write(typeof Temporal)"], timeout=60)
        tools["node_temporal"] = "native" if o.strip() == "object" else "absent"
    live["local"]["tools"] = tools

    # ecosystem claims
    try:
        probed, tz_claim = parse_file_map(os.path.join(ROOT, "references", "ecosystem", "README.md"))
        live["ecosystem_probed"] = {"files": probed, "tzdata": tz_claim}
    except (OSError, SourceError) as exc:
        errors.append(str(exc))
        probed = {}

    if not offline:
        try:
            live["upstream"] = upstream_versions(probed)
        except (SourceError, ValueError, KeyError, IndexError) as exc:
            errors.append("upstream versions: %s" % exc)
            live["upstream"] = None

    # artifacts
    vec = os.path.join(ROOT, "vectors", "vectors.json")
    live["artifacts"] = {"vectors_sha256": sha256_file(vec),
                         "rfcdt_version": py_version_of(os.path.join(ROOT, "scripts", "rfcdt.py")),
                         "runner_version": py_version_of(os.path.join(ROOT, "scripts", "run_vectors.py"),
                                                         "RUNNER_VERSION")}

    # tests
    live["tests"]["unit"] = unittest_run(["discover", "-s", "scripts", "-p", "test_*.py"], ROOT)
    code, out, err = run([sys.executable, "scripts/run_vectors.py", "--report", "json"])
    try:
        rv = json.loads(out)
        t = rv["totals"]
        live["tests"]["vectors"] = {"exit": code, "count": rv["meta"]["vector_count"],
                                    "pass": t["pass"], "interpretation": t["interpretation"],
                                    "fail": sum(t[k] for k in ("too-lenient", "too-strict", "wrong-value",
                                                                "tz-dependent", "fail-reason", "error")),
                                    "skip": t["skip"]}
        if rv["meta"].get("vectors_sha256") != live["artifacts"]["vectors_sha256"]:
            errors.append("run_vectors reports a different vectors sha256 than the file on disk")
    except (ValueError, KeyError) as exc:
        errors.append("run_vectors output unreadable (exit %s): %s %s" % (code, exc, err.strip()[-300:]))
    code, out, err = run([sys.executable, "tools/gen_vectors.py", "--check"])
    live["tests"]["gen_vectors_check"] = {"exit": code, "up_to_date": code == 0}
    return live


def ecosystem_freshness(live):
    """Rows (file, component, probed, local, upstream, verdict) for the report."""
    rows = []
    probed = (live.get("ecosystem_probed") or {}).get("files", {})
    tools = (live.get("local") or {}).get("tools", {})
    up = live.get("upstream") or {}
    for name, (_cmd, _rx, fname, comp) in LOCAL_TOOLS.items():
        pv = probed.get(fname, {}).get(comp)
        lv = tools.get(name)
        upv = None
        if name == "go":
            upv = up.get("go")
        elif name == "node":
            upv = (up.get("node") or {}).get("latest_in_probed_major")
        elif name == "dotnet":
            upv = (up.get("dotnet") or {}).get("latest_sdk_in_probed_channel")
        rows.append((fname, comp, pv, lv, upv))
    for reg, pkg, fname, comp in UPSTREAM_PACKAGES:
        rows.append((fname, comp, probed.get(fname, {}).get(comp), None,
                     (up.get("packages") or {}).get("%s:%s" % (reg, pkg))))
    rows.append(("README.md", "tzdata", (live.get("ecosystem_probed") or {}).get("tzdata"),
                 (live.get("local") or {}).get("tzdata"), up.get("tzdb")))
    out = []
    for fname, comp, pv, lv, upv in rows:
        verdict = []
        if pv is None:
            verdict.append("no probed version recorded")
        else:
            if lv and lv not in ("absent", "error") and lv != pv:
                verdict.append("local differs")
            if upv and vtuple(upv) > vtuple(pv):
                verdict.append("newer upstream")
        out.append((fname, comp, pv or "-", lv or "-", upv or "-",
                    "; ".join(verdict) if verdict else "current"))
    return out


# ---------------------------------------------------------------------------
# iso999 profile (no network, never opens the licensed PDF)


def collect_iso(offline, errors, notes):
    live = {"skill": {}, "tools": {}, "golden": {}, "tests": {}, "checks": {}}
    fm = skill_frontmatter(os.path.join(ROOT, "SKILL.md"))
    live["skill"] = {"name": fm.get("name"), "version": fm.get("version"),
                     "standard": fm.get("standard")}
    sdir = os.path.join(ROOT, "scripts")
    for tool in ("iso999_lint", "iso999_markup"):
        p = os.path.join(sdir, tool + ".py")
        live["tools"][tool] = {"version": py_version_of(p), "sha256": sha256_file(p)}
    man = os.path.join(ROOT, "evals", "golden", "golden.json")
    try:
        with open(man, encoding="utf-8") as fh:
            cases = json.load(fh)["cases"]
        corpus = {}
        for c in cases:
            p = os.path.join(ROOT, c["path"])
            corpus[c["name"]] = sha256_tree(p) if os.path.exists(p) else "missing"
        live["golden"] = {"golden_json_sha256": sha256_file(man), "cases": len(cases),
                          "corpus_sha256": corpus}
    except (OSError, ValueError, KeyError) as exc:
        errors.append("golden manifest: %s" % exc)
    live["tests"]["unit"] = unittest_run(["discover", "-s", "scripts", "-p", "test_*.py"], ROOT)
    live["tests"]["golden"] = unittest_run(["test_iso999_lint.TestGolden"], sdir)
    code, out, _ = run(["git", "rev-parse", "--git-path", "hooks/pre-push"])
    hook = os.path.join(ROOT, out.strip()) if code == 0 and out.strip() else None
    guard = os.path.join(ROOT, "tools", "pre-push")
    live["checks"]["licence_guard_pre_push_installed"] = bool(
        hook and os.path.isfile(hook) and os.path.isfile(guard)
        and sha256_file(hook) == sha256_file(guard))
    live["checks"]["python"] = "%d.%d.%d" % sys.version_info[:3]
    return live


# ---------------------------------------------------------------------------
# diff, report, main

NETWORK_SECTIONS = {"rfc3339-ixdtf": ("sources", "upstream")}


def flatten(obj, prefix=""):
    if isinstance(obj, dict):
        out = {}
        for k in obj:
            out.update(flatten(obj[k], "%s.%s" % (prefix, k) if prefix else str(k)))
        return out
    return {prefix: obj}


def diff(lock, live, skipped):
    a = {k: v for k, v in lock.items() if k not in ("meta",) + tuple(skipped)}
    b = {k: v for k, v in live.items() if k not in ("meta",) + tuple(skipped)}
    fa, fb = flatten(a), flatten(b)
    rows = []
    for key in sorted(set(fa) | set(fb)):
        if key.startswith("tests.") and key.endswith(".tail"):
            continue
        va, vb = fa.get(key, "(absent)"), fb.get(key, "(absent)")
        if va != vb:
            rows.append((key, va, vb))
    return rows


def summarize(lock, live, skipped):
    """Plain-language lines for the changes a maintainer acts on first."""
    out = []
    if "sources" not in skipped:
        le = ((lock.get("sources") or {}).get("errata") or {})
        ve = ((live.get("sources") or {}).get("errata") or {})
        for rfc in sorted(set(le) | set(ve)):
            a, b = le.get(rfc, {}), ve.get(rfc, {})
            for eid in sorted(set(b) - set(a), key=int):
                out.append("NEW erratum %s #%s (%s, %s, reported %s): review and update SKILL.md sources"
                           % (rfc.upper(), eid, b[eid].get("status"), b[eid].get("type"), b[eid].get("reported")))
            for eid in sorted(set(a) - set(b), key=int):
                out.append("Erratum %s #%s is in the lock but not on the live errata page" % (rfc.upper(), eid))
            for eid in sorted(set(a) & set(b), key=int):
                if a[eid].get("status") != b[eid].get("status"):
                    out.append("Erratum %s #%s status changed: %s -> %s"
                               % (rfc.upper(), eid, a[eid].get("status"), b[eid].get("status")))
        lr = ((lock.get("sources") or {}).get("iana_internet_date_time_format") or {})
        vr = ((live.get("sources") or {}).get("iana_internet_date_time_format") or {})
        if lr.get("updated") != vr.get("updated"):
            out.append("IANA registry last-updated changed: %s -> %s" % (lr.get("updated"), vr.get("updated")))
        lk, vk = lr.get("registries", {}), vr.get("registries", {})
        for reg in sorted(set(lk) | set(vk)):
            a, b = lk.get(reg, {}), vk.get(reg, {})
            for k in sorted(set(b) - set(a)):
                out.append("NEW IANA key %s in %s (%s)" % (k, reg, b[k].get("status")))
            for k in sorted(set(a) - set(b)):
                out.append("IANA key %s in %s is in the lock but not in the live registry" % (k, reg))
            for k in sorted(set(a) & set(b)):
                if a[k] != b[k]:
                    out.append("IANA key %s in %s changed" % (k, reg))
    for sect in ("local", "tools", "golden", "artifacts"):
        la, lb = flatten(lock.get(sect) or {}), flatten(live.get(sect) or {})
        for k in sorted(set(la) | set(lb)):
            if la.get(k) != lb.get(k):
                out.append("%s.%s: %s -> %s" % (sect, k, la.get(k, "(absent)"), lb.get(k, "(absent)")))
    for k, v in sorted((live.get("tests") or {}).items()):
        if (lock.get("tests") or {}).get(k) != v:
            out.append("test suite `%s` result differs from the lock" % k)
    return out


def fmt(v):
    s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    return s.replace("|", "\\|")


def tests_ok(live):
    t = live.get("tests", {})
    ok = all(v.get("result", "OK") == "OK" and v.get("exit") in (0, None)
             for v in t.values() if isinstance(v, dict) and "exit" in v)
    if "selfcheck" in t:
        ok = ok and t["selfcheck"].get("exit") == 0
    if "vectors" in t:
        ok = ok and t["vectors"].get("fail", 1) == 0
    return ok


def render(profile, mode, live, lock_path, rows, errors, notes, skipped, fresh, summary=()):
    state = "ERROR" if errors else ("DRIFT" if rows else "NO DRIFT")
    if mode == "update":
        state = "LOCK WRITTEN" if not errors else "ERROR (lock not written)"
    lines = ["# Skill revalidation: %s" % profile, "",
             "- Date: %s" % _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
             "- Mode: %s%s" % (mode, " (offline: %s skipped)" % ", ".join(skipped) if skipped else ""),
             "- Lock: `%s`" % lock_path,
             "- revalidate.py %s, Python %s" % (__version__, "%d.%d.%d" % sys.version_info[:3]),
             "- **Result: %s**" % state, ""]
    if mode == "check":
        lines += ["## Drift against the lock", ""]
        if summary:
            lines += ["- %s" % x for x in summary] + [""]
        if rows:
            lines += ["| Key | Lock | Live |", "|---|---|---|"]
            lines += ["| `%s` | %s | %s |" % (k, fmt(a), fmt(b)) for k, a, b in rows]
        else:
            lines.append("None.")
        lines.append("")
    lines += ["## Tests", "", "| Suite | Result |", "|---|---|"]
    for name, t in sorted(live.get("tests", {}).items()):
        lines.append("| %s | %s |" % (name, fmt({k: v for k, v in t.items() if k != "tail"})))
    lines.append("")
    for name, t in sorted(live.get("tests", {}).items()):
        if t.get("tail"):
            lines += ["<details><summary>%s output</summary>" % name, "", "```", t["tail"], "```",
                      "</details>", ""]
    if live.get("checks"):
        lines += ["## Checks", "", "| Check | Value |", "|---|---|"]
        lines += ["| %s | %s |" % (k, fmt(v)) for k, v in sorted(live["checks"].items())]
        lines.append("")
    if fresh:
        lines += ["## Ecosystem freshness (probed vs local vs upstream)", "",
                  "Rows marked other than `current` mean the file under `references/ecosystem/` may be "
                  "stale: re-probe before relying on it.", "",
                  "| File | Component | Probed | Local | Upstream latest | Verdict |",
                  "|---|---|---|---|---|---|"]
        lines += ["| %s | %s | %s | %s | %s | %s |" % r for r in fresh]
        lines.append("")
    if notes:
        lines += ["## Notes", ""] + ["- %s" % n for n in notes] + [""]
    if errors:
        lines += ["## Errors", ""] + ["- %s" % e for e in errors] + [""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true", help="compare live state with the lock (default)")
    g.add_argument("--update", action="store_true", help="rewrite the lock from live state")
    ap.add_argument("--offline", action="store_true", help="skip network sources")
    ap.add_argument("--lock", default=os.path.join(ROOT, "SOURCES.lock"), help="lock path (default: repo root)")
    ap.add_argument("--report", metavar="PATH", help="also write the Markdown report here")
    ap.add_argument("--version", action="version", version="revalidate %s" % __version__)
    args = ap.parse_args(argv)
    mode = "update" if args.update else "check"

    errors, notes = [], []
    try:
        profile = skill_frontmatter(os.path.join(ROOT, "SKILL.md")).get("name")
    except (OSError, SourceError) as exc:
        print("revalidate: %s" % exc, file=sys.stderr)
        return 2
    if profile == "rfc3339-ixdtf":
        live = collect_rfc(args.offline, errors, notes)
    elif profile == "iso999":
        live = collect_iso(args.offline, errors, notes)
    else:
        print("revalidate: unknown skill %r" % profile, file=sys.stderr)
        return 2
    net = NETWORK_SECTIONS.get(profile, ())
    skipped = [s for s in net if live.get(s) is None]

    lock = None
    if os.path.exists(args.lock):
        try:
            with open(args.lock, encoding="utf-8") as fh:
                lock = json.load(fh)
        except (OSError, ValueError) as exc:
            errors.append("lock unreadable: %s" % exc)
    elif mode == "check":
        errors.append("no lock at %s (run --update first)" % args.lock)

    rows = []
    if mode == "check" and lock is not None:
        if lock.get("meta", {}).get("schema") != LOCK_SCHEMA:
            errors.append("lock schema %r != %r" % (lock.get("meta", {}).get("schema"), LOCK_SCHEMA))
        rows = diff(lock, live, skipped)
    fresh = ecosystem_freshness(live) if profile == "rfc3339-ixdtf" else None

    if mode == "update":
        if not tests_ok(live):
            errors.append("tests are not green: refusing to write the lock")
        if not errors:
            snap = dict((lock or {}).get("meta", {}).get("snapshots", {}))
            for s in net:
                if live.get(s) is None:  # offline update: keep the previous network sections
                    live[s] = (lock or {}).get(s)
                    notes.append("offline: kept the previous lock's `%s` section" % s)
                else:
                    snap[s] = today()
            snap["local"] = today()
            live["meta"] = {"schema": LOCK_SCHEMA, "skill": profile, "generator":
                            "tools/revalidate.py %s" % __version__, "updated": today(),
                            "snapshots": snap}
            if profile == "rfc3339-ixdtf":
                live["meta"]["baseline_snapshot"] = "2026-09-24 (SKILL.md metadata)"
                live["meta"]["urls"] = {"errata": ERRATA_URL % "<rfc>", "iana": IANA_URL}
            else:
                live["meta"]["privacy"] = ("iso999 lock: local-only; no network sources; the licensed "
                                           "ISO PDF is never read.")
            ordered = {"meta": live.pop("meta")}
            ordered.update(live)
            with open(args.lock, "w", encoding="utf-8") as fh:
                json.dump(ordered, fh, indent=2, sort_keys=False, ensure_ascii=False)
                fh.write("\n")
            live = ordered

    summary = summarize(lock, live, skipped) if (rows and lock) else []
    report = render(profile, mode, live, args.lock, rows, errors, notes, skipped, fresh, summary)
    print(report)
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(report + "\n")
    if errors:
        return 2
    return 1 if rows else 0


if __name__ == "__main__":
    sys.exit(main())
