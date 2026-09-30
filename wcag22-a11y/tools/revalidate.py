#!/usr/bin/env python3
"""Re-validate the wcag22-a11y skill against its SOURCES.lock.

Modelled on tools/revalidate.py in the rfc3339-ixdtf, iso999 and ste100 repos
(same flags, same exit codes, same lock layout ideas), with one wcag22-a11y
profile:

  local     the WCAG 2.2 HTML that tools/catalogue/ built from (sha256, status
            line, dated-version URL); the cached Understanding pages (sha256 and
            "Updated" date of each); the catalogue inputs and generated outputs;
            an offline rebuild of the catalogue in a temporary copy of the repo
            (tools/catalogue/rebuild.sh --offline) that must reproduce
            references/ byte for byte; the Playwright, axe-core and Chromium
            headless-shell versions pinned by scripts/setup_page_runner.sh and
            installed in .cache/; the installed axe-core rules and their
            WCAG SC tags against tools/catalogue/axe_map.json.
  tests     (only with --run-tests or --update) the unit suite in scripts/, the
            rendered-page runner suite (node --test, under `caffeinate -d` on
            macOS), gen_check_index --check, the grader self-test in evals/ and
            the unit tests of this script.
  network   (skipped with --offline) the WCAG 2.2 Recommendation page (dated
            version, status, sha256 against the catalogue cache), the WCAG 2.2
            errata page (every entry), the status lines of WCAG 2.1, WCAG 2.0 and
            WCAG 3.0, and the latest npm releases of playwright and axe-core
            ("update available" advice; nothing is ever installed).
  deep      (only with --deep; network) the "Updated" date of every live
            Understanding page the catalogue used (87 requests, one per second).

Every request sends only a neutral User-Agent (UA below) and uses a timeout.
No request carries a name, email address or user name.

Usage:
  python3 tools/revalidate.py                 # --check (default)
  python3 tools/revalidate.py --run-tests     # also run the test suites
  python3 tools/revalidate.py --update        # rewrite SOURCES.lock (runs the tests; refused unless green)
  python3 tools/revalidate.py --offline       # skip network sources
  python3 tools/revalidate.py --deep          # also check every live Understanding page
  python3 tools/revalidate.py --lock PATH --report PATH

Exit status: 0 = no change against the lock, 1 = drift, 2 = error (a source
could not be read, a lock is missing or unreadable, or --update refused).
Standard library only.
"""

import argparse
import datetime as _dt
import glob
import hashlib
import html as _html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

__version__ = "1.0.0"

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
UA = "wcag22-a11y-revalidate/%s (+https://www.w3.org/WAI/WCAG22/)" % __version__
NET_TIMEOUT = 30
DEEP_DELAY = 1.0
LOCK_SCHEMA = 1
PROFILE = "wcag22-a11y"

WCAG22_URL = "https://www.w3.org/TR/WCAG22/"
ERRATA_URL = "https://www.w3.org/WAI/WCAG22/errata/"
OTHER_SPECS = {  # key -> latest-version URL (status line only)
    "wcag21": "https://www.w3.org/TR/WCAG21/",
    "wcag20": "https://www.w3.org/TR/WCAG20/",
    "wcag30": "https://www.w3.org/TR/wcag-3.0/",
}
NPM_LATEST = "https://registry.npmjs.org/%s/latest"
NPM_PACKAGES = ("playwright", "axe-core")
HEAD_BYTES = 400_000      # the status block sits at the top of a TR page
MAX_BYTES = 8_000_000

CAT = os.path.join(ROOT, "tools", "catalogue")
CAT_CACHE = os.path.join(CAT, ".cache")
SPEC_CACHE = os.path.join(CAT_CACHE, "wcag22.html")
UND_CACHE = os.path.join(CAT_CACHE, "understanding")
UND_URLS = os.path.join(CAT, "und_urls.txt")
AXE_MAP = os.path.join(CAT, "axe_map.json")
SETUP = os.path.join(ROOT, "scripts", "setup_page_runner.sh")
ENGINE_CACHE = os.environ.get("WCAG22_CACHE_DIR") or os.path.join(ROOT, ".cache")  # as setup_page_runner.sh
NODE_PREFIX = os.path.join(ENGINE_CACHE, "node")
BROWSERS = os.path.join(ENGINE_CACHE, "ms-playwright")
GENERATED = ("sc-*.md", "glossary.md", "conformance.md", "check-index.md")  # under references/

NEW_VERSION_MSG = "new dated version of WCAG 2.2 published: re-run tools/catalogue/rebuild.sh (online) and review references/"


def rel(path):
    """Repo-relative path for anything under ROOT (keeps machine paths out of locks and reports)."""
    p = os.path.abspath(path)
    return os.path.relpath(p, ROOT) if p == ROOT or p.startswith(ROOT + os.sep) else os.path.basename(p)


TESTS = {  # name -> the command recorded in the lock (run from the repo root)
    "unit_scripts": 'python3 -m unittest discover -s scripts -p "test_*.py"',
    "page_runner": "caffeinate -d node --test scripts/test_wcag_page.mjs  (caffeinate on macOS only)",
    "gen_check_index_check": "python3 tools/gen_check_index.py --check",
    "grader_selftest": "python3 evals/graders/selftest.py",
    "unit_revalidate": 'python3 -m unittest discover -s tools -p "test_*.py"',
}

# ---------------------------------------------------------------------------
# helpers


class SourceError(Exception):
    pass


def today():
    return _dt.date.today().isoformat()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_tree(path, skip=("__pycache__", ".cache", ".DS_Store")):
    """sha256 of a directory's sorted (relpath, file sha) list, skipping caches."""
    h = hashlib.sha256()
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = sorted(d for d in dirnames if d not in skip)
        for name in sorted(filenames):
            if name in skip or name.endswith(".pyc"):
                continue
            full = os.path.join(dirpath, name)
            h.update(("%s\0%s\n" % (os.path.relpath(full, path), sha256_file(full))).encode())
    return h.hexdigest()


def run(cmd, cwd=None, timeout=900, env=None):
    """Run a command; return (exit code, stdout, stderr). Missing binary -> None code."""
    try:
        cp = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True,
                            timeout=timeout, stdin=subprocess.DEVNULL, env=env)
        return cp.returncode, cp.stdout, cp.stderr
    except FileNotFoundError:
        return None, "", "not found: %s" % cmd[0]
    except subprocess.TimeoutExpired:
        return None, "", "timeout after %ss: %s" % (timeout, " ".join(cmd))


def fetch(url, max_bytes=MAX_BYTES):
    """GET url with the neutral UA and a timeout; return (status, bytes). Raises SourceError."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=NET_TIMEOUT) as resp:
            return resp.status, resp.read(max_bytes)
    except urllib.error.HTTPError as exc:
        raise SourceError("fetch failed: GET %s: HTTP %s" % (url, exc.code))
    except Exception as exc:  # noqa: BLE001 - any network failure is a source error
        raise SourceError("fetch failed: GET %s: %s" % (url, exc))


def fetch_text(url, max_bytes=MAX_BYTES):
    return fetch(url, max_bytes)[1].decode("utf-8", errors="replace")


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


def vtuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v or ""))


def strip_tags(fragment):
    text = re.sub(r"(?s)<(script|style)\b.*?</\1>", " ", fragment)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", _html.unescape(text)).strip()
    return re.sub(r"\s+([,.;:)])", r"\1", text)


# ---------------------------------------------------------------------------
# parsers (pure functions; unit-tested against fixtures)

TR_STATUS = (r"W3C\s+((?:Superseded\s+|Obsolete\s+|Rescinded\s+)?Recommendation|Proposed\s+Recommendation|"
             r"Candidate\s+Recommendation(?:\s+Snapshot|\s+Draft)?|Working\s+Draft|Group\s+(?:Draft\s+)?Note|"
             r"Statement|Discontinued\s+Draft|Editor'?s\s+Draft)")
MONTHS = ("January February March April May June July August September October November December").split()


def parse_tr_head(html):
    """Status line and version links of a W3C TR page (ReSpec or older format)."""
    head = html[:HEAD_BYTES]
    text = strip_tags(head)
    m = re.search(TR_STATUS + r"\s*,?\s+(\d{1,2}\s+(?:%s)\s+\d{4})" % "|".join(MONTHS), text)
    if not m:
        raise SourceError("TR page: no 'W3C <status> <date>' line (layout change?)")

    def link(label):
        mm = re.search(r"%s:?\s*</dt>\s*<dd[^>]*>\s*<a[^>]+href=\"([^\"]+)\"" % re.escape(label), head, re.I)
        return mm.group(1) if mm else None
    title = re.search(r"<title>(.*?)</title>", head, re.S | re.I)
    return {"title": strip_tags(title.group(1)) if title else None,
            "status": re.sub(r"\s+", " ", "W3C " + m.group(1)),
            "date": re.sub(r"\s+", " ", m.group(2)),
            "this_version": link("This version") or link("This Version"),
            "latest_version": link("Latest published version") or link("Latest version")}


def parse_errata(html):
    """WCAG 2.2 errata page -> {last_modified, publications, entries}."""
    lm = re.search(r"\$Date:\s*([\d/]+)", html)
    out = {"last_modified": lm.group(1).replace("/", "-") if lm else None,
           "publications": {}, "entries": {}}
    parts = re.split(r'<section id="(since-[^"]+)">', html)
    for i in range(1, len(parts), 2):
        pub, body = parts[i], parts[i + 1]
        h2 = re.search(r"<h2[^>]*>(.*?)</h2>", body, re.S)
        href = re.search(r'<h2[^>]*>.*?<a[^>]+href="([^"]+)"', body, re.S)
        out["publications"][pub] = {"label": strip_tags(h2.group(1)) if h2 else None,
                                    "applies_to": href.group(1) if href else None}
        for sub in re.split(r"<h3[^>]*>", body)[1:]:
            cls_m = re.match(r"(.*?)</h3>", sub, re.S)
            cls = strip_tags(cls_m.group(1)).lower().split()[0] if cls_m else "unknown"
            for li in re.findall(r"<li>(.*?)</li>", sub, re.S):
                text = strip_tags(li)
                dm = re.match(r"(\d{4}-\d{2}-\d{2}):\s*(.*)", text)
                if not dm:
                    continue
                prs = re.findall(r"/pull/(\d+)", li)
                summary = re.sub(r"\s*\((?:\s*#\d+\s*,?)+\)\s*", " ", dm.group(2)).strip()
                key = "%s#%s" % (dm.group(1), "+".join(prs) if prs else sha256_bytes(text.encode())[:8])
                n, base = 2, key
                while key in out["entries"]:
                    key, n = "%s~%d" % (base, n), n + 1
                out["entries"][key] = {"date": dm.group(1), "class": cls, "publication": pub,
                                       "summary": summary[:140]}
    if not out["entries"] and "Errata since" not in html:
        raise SourceError("errata page parsed to zero entries (layout change?)")
    return out


def errata_counts(errata):
    counts = {}
    for e in errata["entries"].values():
        counts[e["class"]] = counts.get(e["class"], 0) + 1
    counts["total"] = len(errata["entries"])
    for pub in errata.get("publications", {}):
        counts[pub] = sum(1 for e in errata["entries"].values() if e["publication"] == pub)
    return counts


UPDATED_RX = re.compile(r"Updated\s+(\d{1,2})\s+(%s)\s+(\d{4})" % "|".join(MONTHS))


def understanding_updated(html):
    m = UPDATED_RX.search(html)
    if not m:
        return None
    return "%s-%02d-%02d" % (m.group(3), MONTHS.index(m.group(2)) + 1, int(m.group(1)))


def parse_setup_pins(text):
    pins = {}
    for var, pkg in (("PLAYWRIGHT_VERSION", "playwright"), ("AXE_CORE_VERSION", "axe-core")):
        m = re.search(r'^%s="([^"]+)"' % var, text, re.M)
        pins[pkg] = m.group(1) if m else None
    return pins


def axe_sc_map(rules):
    """[(ruleId, tags)] -> {"1.1.1": ["image-alt", "x(deprecated)"]}, the axe_map.json convention."""
    out = {}
    for rid, tags in rules:
        suffix = "(deprecated)" if "deprecated" in tags else "(experimental)" if "experimental" in tags else ""
        for t in tags:
            m = re.fullmatch(r"wcag(\d)(\d)(\d+)", t)
            if m:
                out.setdefault("%s.%s.%s" % m.groups(), []).append(rid + suffix)
    return {k: sorted(v) for k, v in sorted(out.items(), key=lambda kv: vtuple(kv[0]))}


def axe_map_diff(installed, authored):
    """Lines describing where axe_map.json and the installed axe-core tags disagree."""
    out = []
    for sc in sorted(set(installed) | set(authored), key=vtuple):
        a, b = set(authored.get(sc, [])), set(installed.get(sc, []))
        if b - a:
            out.append("%s: installed axe-core tags %s, not in axe_map.json" % (sc, ", ".join(sorted(b - a))))
        if a - b:
            out.append("%s: axe_map.json lists %s, not tagged by installed axe-core" % (sc, ", ".join(sorted(a - b))))
    return out


def node_test_summary(text):
    res = {}
    for k, v in re.findall(r"^[ℹ#]\s*(tests|pass|fail|skipped|cancelled|todo)\s+(\d+)\s*$", text, re.M):
        res[k] = int(v)
    return res


def unittest_summary(text, code):
    ran = re.findall(r"^Ran (\d+) tests?", text, re.M)
    tail = re.findall(r"^(OK|FAILED)(?: \(([^)]*)\))?\s*$", text, re.M)
    res = {"exit": code, "ran": int(ran[-1]) if ran else None,
           "result": tail[-1][0] if tail else "UNKNOWN"}
    for part in (tail[-1][1].split(", ") if tail and tail[-1][1] else []):
        k, _, v = part.partition("=")
        if v.isdigit():
            res[k] = int(v)
    return res


# ---------------------------------------------------------------------------
# local collection


def collect_spec(fm, errors):
    spec = {"recommendation_url": WCAG22_URL, "errata_url": ERRATA_URL}
    if not os.path.isfile(SPEC_CACHE):
        errors.append("catalogue source missing: %s (run tools/catalogue/rebuild.sh)" % rel(SPEC_CACHE))
        return spec
    with open(SPEC_CACHE, "rb") as fh:
        raw = fh.read()
    try:
        head = parse_tr_head(raw.decode("utf-8", errors="replace"))
    except SourceError as exc:
        errors.append("%s: %s" % (rel(SPEC_CACHE), exc))
        head = {}
    errata_links = re.findall(rb'href="(https://www\.w3\.org/WAI/WCAG22/errata/?)"', raw)
    spec.update({"status": head.get("status"), "dated_version": head.get("date"),
                 "dated_version_url": head.get("this_version"),
                 "cached_html": {"path": rel(SPEC_CACHE), "sha256": sha256_bytes(raw), "bytes": len(raw)},
                 "cached_html_links_errata_page": bool(errata_links),
                 "skill_md_standard": fm.get("standard"),
                 "skill_md_standard_names_dated_version": bool(head.get("date") and head["date"] in (fm.get("standard") or ""))})
    return spec


def collect_catalogue(errors):
    cat = {"understanding": {}, "derived": {}, "inputs": {}, "outputs": {}}
    urls = []
    if os.path.isfile(UND_URLS):
        with open(UND_URLS, encoding="utf-8") as fh:
            urls = [u.strip() for u in fh if u.strip()]
    files = {}
    missing = []
    for u in urls:
        name = u.rstrip("/").rsplit("/", 1)[-1]
        p = os.path.join(UND_CACHE, name)
        if not os.path.isfile(p):
            missing.append(name)
            continue
        with open(p, "rb") as fh:
            raw = fh.read()
        files[name] = {"sha256": sha256_bytes(raw),
                       "updated": understanding_updated(raw.decode("utf-8", errors="replace"))}
    if missing:
        errors.append("%d cached Understanding page(s) missing (run tools/catalogue/rebuild.sh): %s"
                      % (len(missing), ", ".join(missing[:5])))
    cat["understanding"] = {"urls": len(urls), "cached": len(files),
                            "und_urls_txt_sha256": sha256_file(UND_URLS) if os.path.isfile(UND_URLS) else "absent",
                            "files": dict(sorted(files.items()))}
    techniques = None
    for name in ("wcag.json", "techs.json"):
        p = os.path.join(CAT_CACHE, name)
        cat["derived"][name] = sha256_file(p) if os.path.isfile(p) else "absent"
        if name == "techs.json" and os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as fh:
                    tj = json.load(fh)
                ids = set()
                for v in tj.values():
                    for k in ("sufficient", "advisory", "failure"):
                        ids |= set((v or {}).get(k) or {})
                techniques = {"sc_with_techniques": len(tj), "technique_ids": len(ids)}
            except (OSError, ValueError, AttributeError) as exc:
                errors.append("techs.json unreadable: %s" % exc)
    cat["techniques"] = techniques or "absent"
    cat["inputs"] = {"builder_tree_sha256": sha256_tree(CAT),
                     "axe_map_json_sha256": sha256_file(AXE_MAP) if os.path.isfile(AXE_MAP) else "absent"}
    refs = os.path.join(ROOT, "references")
    for pat in GENERATED:
        for p in sorted(glob.glob(os.path.join(refs, pat))):
            cat["outputs"]["references/" + os.path.basename(p)] = sha256_file(p)
    return cat


def rebuild_offline(errors, notes):
    """Run tools/catalogue/rebuild.sh --offline in a temp copy; compare references/ byte for byte."""
    if not os.path.isfile(SPEC_CACHE):
        return {"ran": False, "reproduces": None, "differs": []}
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")
    with tempfile.TemporaryDirectory(prefix="wcag22-rebuild-") as tmp:
        dst = os.path.join(tmp, "repo")
        os.makedirs(dst)
        shutil.copytree(os.path.join(ROOT, "tools"), os.path.join(dst, "tools"), ignore=ignore)
        shutil.copytree(os.path.join(ROOT, "references"), os.path.join(dst, "references"), ignore=ignore)
        env = dict(os.environ)
        env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        code, out, err = run(["sh", os.path.join(dst, "tools", "catalogue", "rebuild.sh"), "--offline"],
                             cwd=dst, timeout=600, env=env)
        if code != 0:
            errors.append("offline catalogue rebuild failed (exit %s): %s" % (code, (err or out).strip()[-300:]))
            return {"ran": True, "exit": code, "reproduces": False, "differs": []}
        differs = []
        a_refs, b_refs = os.path.join(ROOT, "references"), os.path.join(dst, "references")
        names = sorted(set(os.listdir(a_refs)) | set(os.listdir(b_refs)))
        for n in names:
            if n.startswith(".") or n == "__pycache__":
                continue
            a, b = os.path.join(a_refs, n), os.path.join(b_refs, n)
            if not os.path.isfile(a) or not os.path.isfile(b) or sha256_file(a) != sha256_file(b):
                differs.append("references/" + n)
        for n in ("wcag.json", "techs.json"):
            a, b = os.path.join(CAT_CACHE, n), os.path.join(dst, "tools", "catalogue", ".cache", n)
            if os.path.isfile(a) and os.path.isfile(b) and sha256_file(a) != sha256_file(b):
                notes.append("offline rebuild regenerated a different tools/catalogue/.cache/%s "
                             "(the cache is stale against the builder)" % n)
    return {"ran": True, "exit": 0, "reproduces": not differs, "differs": differs}


def installed_pkg(name):
    p = os.path.join(NODE_PREFIX, "node_modules", name, "package.json")
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh).get("version")
    except (OSError, ValueError):
        return "absent"


AXE_RULES_JS = ('const a=require("axe-core");process.stdout.write(JSON.stringify('
                '{version:a.version,rules:a.getRules().map(r=>[r.ruleId,r.tags])}))')


def collect_engines(errors, notes):
    eng = {}
    try:
        with open(SETUP, encoding="utf-8") as fh:
            eng["pinned"] = parse_setup_pins(fh.read())
    except OSError as exc:
        errors.append("setup_page_runner.sh unreadable: %s" % exc)
        eng["pinned"] = {}
    inst = {p: installed_pkg(p) for p in ("playwright", "playwright-core", "axe-core")}
    chromium = {"revision": None, "browser_version": None, "installed": False}
    bj = os.path.join(NODE_PREFIX, "node_modules", "playwright-core", "browsers.json")
    try:
        with open(bj, encoding="utf-8") as fh:
            for b in json.load(fh).get("browsers", []):
                if b.get("name") == "chromium-headless-shell":
                    chromium["revision"] = b.get("revision")
                    chromium["browser_version"] = b.get("browserVersion")
    except (OSError, ValueError):
        pass
    if chromium["revision"]:
        chromium["installed"] = os.path.isfile(os.path.join(
            BROWSERS, "chromium_headless_shell-%s" % chromium["revision"], "INSTALLATION_COMPLETE"))
    inst["chromium_headless_shell"] = chromium
    inst["browser_dirs"] = sorted(d for d in os.listdir(BROWSERS) if not d.startswith(".")) if os.path.isdir(BROWSERS) else []
    eng["installed"] = inst
    for pkg, want in eng["pinned"].items():
        if inst.get(pkg) != want:
            notes.append("%s installed %s, pinned %s: run scripts/setup_page_runner.sh" % (pkg, inst.get(pkg), want))
    if not chromium["installed"]:
        notes.append("Chromium headless shell not installed in .cache/: run scripts/setup_page_runner.sh")

    code, out, _ = run(["node", "--version"], timeout=60)
    eng["node"] = out.strip().lstrip("v") if code == 0 else "absent"

    axe = {"version": None, "rule_count": None, "rules": [], "axe_map_json_matches_installed": None}
    if inst["axe-core"] != "absent" and eng["node"] != "absent":
        code, out, err = run(["node", "-e", AXE_RULES_JS], cwd=NODE_PREFIX, timeout=120)
        try:
            data = json.loads(out)
            rules = [(r[0], r[1]) for r in data["rules"]]
            suffix = lambda tags: "(deprecated)" if "deprecated" in tags else "(experimental)" if "experimental" in tags else ""
            axe = {"version": data["version"], "rule_count": len(rules),
                   "rules": sorted(r + suffix(t) for r, t in rules)}
            with open(AXE_MAP, encoding="utf-8") as fh:
                authored = json.load(fh)
            mism = axe_map_diff(axe_sc_map(rules), authored)
            axe["axe_map_json_matches_installed"] = not mism
            for line in mism:
                notes.append("axe_map.json: " + line)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            errors.append("axe-core rule list unreadable (exit %s): %s %s" % (code, exc, (err or "").strip()[-200:]))
    eng["axe"] = axe
    return eng


def collect_tests():
    darwin = sys.platform == "darwin" and shutil.which("caffeinate")
    t = {}
    for name, cmd_str in TESTS.items():
        t[name] = {"command": cmd_str}
    code, out, err = run([sys.executable, "-m", "unittest", "discover", "-s", "scripts", "-p", "test_*.py"])
    t["unit_scripts"].update(unittest_summary(out + err, code))
    if t["unit_scripts"]["result"] != "OK":
        t["unit_scripts"]["tail"] = "\n".join((out + err).strip().splitlines()[-25:])
    node_cmd = ["node", "--test", "scripts/test_wcag_page.mjs"]
    code, out, err = run((["caffeinate", "-d"] if darwin else []) + node_cmd, timeout=1800)
    s = node_test_summary(out + err)
    t["page_runner"].update({"exit": code, "tests": s.get("tests"), "pass": s.get("pass"),
                             "fail": s.get("fail"), "skipped": s.get("skipped"),
                             "result": "OK" if code == 0 and s.get("fail") == 0 else "FAILED"})
    if t["page_runner"]["result"] != "OK":
        t["page_runner"]["tail"] = "\n".join((out + err).strip().splitlines()[-25:])
    code, out, err = run([sys.executable, "tools/gen_check_index.py", "--check"])
    m = re.search(r"(\d+) SC sections \(A (\d+), AA (\d+), AAA (\d+), obsolete (\d+)\)", out + err)
    t["gen_check_index_check"].update({"exit": code, "result": "OK" if code == 0 else "FAILED"})
    if m:
        t["gen_check_index_check"]["sc_sections"] = dict(zip(("total", "A", "AA", "AAA", "obsolete"),
                                                             map(int, m.groups())))
    code, out, err = run([sys.executable, "evals/graders/selftest.py"])
    m = re.search(r"mismatches:\s*(\d+)", out + err)
    t["grader_selftest"].update({"exit": code, "mismatches": int(m.group(1)) if m else None,
                                 "result": "OK" if code == 0 else "FAILED"})
    if code != 0:
        t["grader_selftest"]["tail"] = "\n".join((out + err).strip().splitlines()[-25:])
    code, out, err = run([sys.executable, "-m", "unittest", "discover", "-s", "tools", "-p", "test_*.py"])
    t["unit_revalidate"].update(unittest_summary(out + err, code))
    return t


# ---------------------------------------------------------------------------
# network collection


def collect_sources(errors, local_spec):
    try:
        status, raw = fetch(WCAG22_URL)
        head = parse_tr_head(raw.decode("utf-8", errors="replace"))
        src = {"wcag22": {"status": head["status"], "date": head["date"],
                          "this_version": head["this_version"], "latest_version": head["latest_version"],
                          "html_sha256": sha256_bytes(raw),
                          "matches_catalogue_cache": sha256_bytes(raw) == (local_spec.get("cached_html") or {}).get("sha256")}}
        errata = parse_errata(fetch_text(ERRATA_URL))
        errata["counts"] = errata_counts(errata)
        src["errata"] = errata
        for key, url in OTHER_SPECS.items():
            h = parse_tr_head(fetch_text(url, HEAD_BYTES))
            src[key] = {"status": h["status"], "date": h["date"], "this_version": h["this_version"]}
        return src
    except SourceError as exc:
        errors.append(str(exc))
        return None


def collect_upstream(errors):
    try:
        npm = {}
        for pkg in NPM_PACKAGES:
            npm[pkg] = json.loads(fetch_text(NPM_LATEST % pkg, 2_000_000))["version"]
        return {"npm": npm}
    except (SourceError, ValueError, KeyError) as exc:
        errors.append("npm latest versions: %s" % exc)
        return None


def collect_understanding_live(errors, sleep=time.sleep):
    try:
        with open(UND_URLS, encoding="utf-8") as fh:
            urls = [u.strip() for u in fh if u.strip()]
    except OSError as exc:
        errors.append("und_urls.txt unreadable: %s" % exc)
        return None
    out = {}
    for i, u in enumerate(urls):
        if i:
            sleep(DEEP_DELAY)
        try:
            out[u.rstrip("/").rsplit("/", 1)[-1]] = understanding_updated(fetch_text(u))
        except SourceError as exc:
            errors.append(str(exc))
            return None
    return {"updated": dict(sorted(out.items()))}


def collect(offline, run_tests, deep, errors, notes):
    fm = skill_frontmatter(os.path.join(ROOT, "SKILL.md"))
    live = {"skill": {"name": fm.get("name"), "version": fm.get("version"), "standard": fm.get("standard")}}
    live["spec"] = collect_spec(fm, errors)
    live["catalogue"] = collect_catalogue(errors)
    live["catalogue"]["offline_rebuild"] = rebuild_offline(errors, notes)
    live["engines"] = collect_engines(errors, notes)
    live["tests"] = collect_tests() if run_tests else None
    live["sources"] = None if offline else collect_sources(errors, live["spec"])
    live["upstream"] = None if offline else collect_upstream(errors)
    live["understanding_live"] = collect_understanding_live(errors) if (deep and not offline) else None
    return live


# ---------------------------------------------------------------------------
# diff, report, main

NETWORK_SECTIONS = ("sources", "upstream", "understanding_live")
OPTIONAL_SECTIONS = NETWORK_SECTIONS + ("tests",)


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
    ls, vs = lock.get("sources") or {}, live.get("sources") or {}
    if "sources" not in skipped:
        lw, vw = ls.get("wcag22") or {}, vs.get("wcag22") or {}
        pinned = (lock.get("spec") or {}).get("dated_version_url")
        if vw.get("this_version") and vw.get("this_version") != pinned:
            out.append("%s (live: %s, %s; pinned: %s)" % (NEW_VERSION_MSG, vw.get("this_version"),
                                                         vw.get("date"), pinned))
        elif lw.get("html_sha256") != vw.get("html_sha256"):
            out.append("WCAG 2.2 page bytes changed without a new dated version: diff it against "
                       "tools/catalogue/.cache/wcag22.html before rebuilding")
        if lw.get("status") != vw.get("status"):
            out.append("WCAG 2.2 status changed: %s -> %s" % (lw.get("status"), vw.get("status")))
        le, ve = (ls.get("errata") or {}).get("entries") or {}, (vs.get("errata") or {}).get("entries") or {}
        for k in sorted(set(ve) - set(le)):
            e = ve[k]
            tag = "SUBSTANTIVE erratum" if e.get("class") == "substantive" else "NEW %s erratum" % e.get("class")
            out.append("%s %s: %s (review references/ and SKILL.md; the SC text in references/ follows the "
                       "dated Recommendation, not the errata)" % (tag, k, e.get("summary")))
        for k in sorted(set(le) - set(ve)):
            out.append("Erratum %s is in the lock but no longer on the errata page (folded into a new version?)" % k)
        for key, label in (("wcag21", "WCAG 2.1"), ("wcag20", "WCAG 2.0"), ("wcag30", "WCAG 3.0")):
            a, b = ls.get(key) or {}, vs.get(key) or {}
            if (a.get("status"), a.get("date")) != (b.get("status"), b.get("date")):
                out.append("%s status changed: %s %s -> %s %s" % (label, a.get("status"), a.get("date"),
                                                                  b.get("status"), b.get("date")))
    if "upstream" not in skipped:
        la, lb = ((lock.get("upstream") or {}).get("npm") or {}), ((live.get("upstream") or {}).get("npm") or {})
        for pkg in sorted(set(la) | set(lb)):
            if la.get(pkg) != lb.get(pkg):
                out.append("npm %s latest release changed: %s -> %s (advice only; nothing is installed)"
                           % (pkg, la.get(pkg), lb.get(pkg)))
    if "understanding_live" not in skipped:
        cached = ((live.get("catalogue") or {}).get("understanding") or {}).get("files") or {}
        for name, d in sorted(((live.get("understanding_live") or {}).get("updated") or {}).items()):
            c = (cached.get(name) or {}).get("updated")
            if d != c:
                out.append("Understanding page %s updated upstream (cached %s, live %s): delete the cached copy "
                           "and re-run tools/catalogue/rebuild.sh" % (name, c, d))
    lsp, vsp = lock.get("spec") or {}, live.get("spec") or {}
    if (lsp.get("cached_html") or {}).get("sha256") != (vsp.get("cached_html") or {}).get("sha256"):
        out.append("Catalogue source tools/catalogue/.cache/wcag22.html changed (%s -> %s)"
                   % (lsp.get("dated_version_url"), vsp.get("dated_version_url")))
    lc, vc = lock.get("catalogue") or {}, live.get("catalogue") or {}
    lf = (lc.get("understanding") or {}).get("files") or {}
    vf = (vc.get("understanding") or {}).get("files") or {}
    changed = sorted(n for n in set(lf) | set(vf) if lf.get(n) != vf.get(n))
    if changed:
        out.append("Cached Understanding pages changed: %s" % ", ".join(changed[:10])
                   + (" (+%d more)" % (len(changed) - 10) if len(changed) > 10 else ""))
    reb = vc.get("offline_rebuild") or {}
    if reb.get("reproduces") is False:
        out.append("Offline catalogue rebuild does NOT reproduce references/: %s" % ", ".join(reb.get("differs") or ["(build failed)"]))
    lo, vo = lc.get("outputs") or {}, vc.get("outputs") or {}
    for n in sorted(set(lo) | set(vo)):
        if lo.get(n) != vo.get(n):
            out.append("Generated %s changed since the lock" % n)
    if (lc.get("inputs") or {}) != (vc.get("inputs") or {}):
        out.append("Catalogue builder or axe_map.json changed since the lock")
    le_, ve_ = lock.get("engines") or {}, live.get("engines") or {}
    for part in ("pinned", "installed"):
        a, b = flatten(le_.get(part) or {}), flatten(ve_.get(part) or {})
        for k in sorted(set(a) | set(b)):
            if a.get(k) != b.get(k):
                out.append("engines.%s.%s: %s -> %s" % (part, k, a.get(k, "(absent)"), b.get(k, "(absent)")))
    if le_.get("node") != ve_.get("node"):
        out.append("Node changed: %s -> %s" % (le_.get("node"), ve_.get("node")))
    la, lb = set((le_.get("axe") or {}).get("rules") or []), set((ve_.get("axe") or {}).get("rules") or [])
    if lb - la:
        out.append("NEW axe-core rules: %s (map any WCAG tags in tools/catalogue/axe_map.json)" % ", ".join(sorted(lb - la)))
    if la - lb:
        out.append("REMOVED axe-core rules: %s" % ", ".join(sorted(la - lb)))
    if (ve_.get("axe") or {}).get("axe_map_json_matches_installed") is False:
        out.append("tools/catalogue/axe_map.json no longer matches the installed axe-core SC tags (see Notes)")
    if "tests" not in skipped:
        for k, v in sorted((live.get("tests") or {}).items()):
            lv = dict((lock.get("tests") or {}).get(k) or {})
            vv = {x: y for x, y in v.items() if x != "tail"}
            lv.pop("tail", None)
            if lv != vv:
                out.append("test `%s` result differs from the lock: %s -> %s" % (k, json.dumps(lv), json.dumps(vv)))
    return out


def engine_freshness(live):
    """Rows (component, pinned, installed, latest, verdict) for the report."""
    eng = live.get("engines") or {}
    npm = (live.get("upstream") or {}).get("npm") or {}
    rows = []
    for pkg in NPM_PACKAGES:
        pv, iv, uv = (eng.get("pinned") or {}).get(pkg), (eng.get("installed") or {}).get(pkg), npm.get(pkg)
        verdict = []
        if iv != pv:
            verdict.append("installed differs from pin")
        if uv and pv and vtuple(uv) > vtuple(pv):
            verdict.append("update available")
        rows.append((pkg, pv or "-", iv or "-", uv or "(offline)", "; ".join(verdict) or "current"))
    ch = (eng.get("installed") or {}).get("chromium_headless_shell") or {}
    rows.append(("chromium-headless-shell", "r%s (via playwright pin)" % ch.get("revision"),
                 ch.get("browser_version") if ch.get("installed") else "absent", "-",
                 "current" if ch.get("installed") else "not installed"))
    return rows


def fmt(v):
    s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    if len(s) > 400:
        s = s[:400] + "..."
    return s.replace("|", "\\|")


def tests_ok(live):
    t = live.get("tests") or {}
    return bool(t) and all(v.get("result") == "OK" and v.get("exit") == 0 for v in t.values())


def render(mode, live, lock_path, rows, errors, notes, skipped, summary=()):
    state = "ERROR" if errors else ("DRIFT" if rows else "NO DRIFT")
    if mode == "update":
        state = "LOCK WRITTEN" if not errors else "ERROR (lock not written)"
    lines = ["# Skill revalidation: %s" % PROFILE, "",
             "- Date: %s" % _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
             "- Mode: %s%s" % (mode, " (not checked: %s)" % ", ".join(skipped) if skipped else ""),
             "- Lock: `%s`" % rel(lock_path),
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
    spec, src = live.get("spec") or {}, live.get("sources") or {}
    lines += ["## WCAG sources", "",
              "- Catalogue built from: %s (%s, %s)" % (spec.get("dated_version_url"), spec.get("status"),
                                                      spec.get("dated_version"))]
    if src:
        w = src.get("wcag22") or {}
        lines.append("- Live %s: %s %s, this version %s; bytes match the catalogue cache: %s"
                     % (WCAG22_URL, w.get("status"), w.get("date"), w.get("this_version"),
                        w.get("matches_catalogue_cache")))
        e = src.get("errata") or {}
        lines.append("- Errata page (last modified %s): %s" % (e.get("last_modified"), fmt(e.get("counts"))))
        for key, label in (("wcag21", "WCAG 2.1"), ("wcag20", "WCAG 2.0"), ("wcag30", "WCAG 3.0")):
            s = src.get(key) or {}
            lines.append("- %s: %s %s (%s)" % (label, s.get("status"), s.get("date"), s.get("this_version")))
    else:
        lines.append("- Network sources not checked.")
    reb = (live.get("catalogue") or {}).get("offline_rebuild") or {}
    lines += ["- Offline catalogue rebuild reproduces references/: %s%s"
              % (reb.get("reproduces"), (" (differs: %s)" % ", ".join(reb["differs"])) if reb.get("differs") else ""), ""]
    lines += ["## Engines", "", "| Component | Pinned | Installed | Latest on npm | Verdict |", "|---|---|---|---|---|"]
    lines += ["| %s | %s | %s | %s | %s |" % r for r in engine_freshness(live)]
    axe = (live.get("engines") or {}).get("axe") or {}
    lines += ["", "axe-core %s: %s rules; axe_map.json matches installed SC tags: %s. Node %s."
              % (axe.get("version"), axe.get("rule_count"), axe.get("axe_map_json_matches_installed"),
                 (live.get("engines") or {}).get("node")),
              "", "\"update available\" is advice: change the pins in scripts/setup_page_runner.sh, re-run it, "
              "run the suites, then --update. This script never installs anything.", ""]
    lines += ["## Tests", ""]
    tests = live.get("tests")
    if tests:
        lines += ["| Suite | Result |", "|---|---|"]
        for name, t in sorted(tests.items()):
            lines.append("| %s | %s |" % (name, fmt({k: v for k, v in t.items() if k != "tail"})))
        lines.append("")
        for name, t in sorted(tests.items()):
            if t.get("tail"):
                lines += ["<details><summary>%s output</summary>" % name, "", "```", t["tail"], "```",
                          "</details>", ""]
    else:
        lines += ["Not run (add --run-tests). Commands:", ""]
        lines += ["- `%s`" % c for c in TESTS.values()] + [""]
    if notes:
        lines += ["## Notes", ""] + ["- %s" % n for n in notes] + [""]
    if errors:
        lines += ["## Errors", ""] + ["- %s" % e for e in errors] + [""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true", help="compare live state with the lock (default)")
    g.add_argument("--update", action="store_true",
                   help="rewrite the lock from live state (runs the tests; refused unless green)")
    ap.add_argument("--offline", action="store_true", help="skip network sources")
    ap.add_argument("--run-tests", action="store_true", help="also run the test suites and compare their counts")
    ap.add_argument("--deep", action="store_true",
                    help="also fetch every live Understanding page (87 requests) and compare its Updated date")
    ap.add_argument("--lock", default=os.path.join(ROOT, "SOURCES.lock"), help="lock path (default: repo root)")
    ap.add_argument("--report", metavar="PATH", help="also write the Markdown report here")
    ap.add_argument("--version", action="version", version="revalidate %s" % __version__)
    args = ap.parse_args(argv)
    mode = "update" if args.update else "check"
    run_tests = args.run_tests or args.update

    errors, notes = [], []
    try:
        profile = skill_frontmatter(os.path.join(ROOT, "SKILL.md")).get("name")
    except (OSError, SourceError) as exc:
        print("revalidate: %s" % exc, file=sys.stderr)
        return 2
    if profile != PROFILE:
        print("revalidate: unknown skill %r (this script serves %s)" % (profile, PROFILE), file=sys.stderr)
        return 2

    lock = None
    if os.path.exists(args.lock):
        try:
            with open(args.lock, encoding="utf-8") as fh:
                lock = json.load(fh)
            if not isinstance(lock, dict):
                raise ValueError("top level is not an object")
        except (OSError, ValueError) as exc:
            errors.append("lock unreadable: %s" % exc)
            lock = None
    elif mode == "check":
        errors.append("no lock at %s (run --update first)" % rel(args.lock))

    live = collect(args.offline, run_tests, args.deep, errors, notes)
    skipped = [s for s in OPTIONAL_SECTIONS if live.get(s) is None]

    rows = []
    if mode == "check" and lock is not None:
        if lock.get("meta", {}).get("schema") != LOCK_SCHEMA:
            errors.append("lock schema %r != %r" % (lock.get("meta", {}).get("schema"), LOCK_SCHEMA))
        rows = diff(lock, live, skipped)

    if mode == "update":
        if not tests_ok(live):
            errors.append("tests are not green: refusing to write the lock")
        if not errors:
            snap = dict((lock or {}).get("meta", {}).get("snapshots", {}))
            for s in NETWORK_SECTIONS:
                if live.get(s) is None:  # offline (or no --deep) update: keep the previous section
                    live[s] = (lock or {}).get(s)
                    if live[s] is not None:
                        notes.append("kept the previous lock's `%s` section" % s)
                else:
                    snap[s] = today()
            snap["local"] = snap["tests"] = today()
            live["meta"] = {
                "schema": LOCK_SCHEMA, "skill": PROFILE,
                "generator": "tools/revalidate.py %s" % __version__,
                "updated": today(), "python": "%d.%d.%d" % sys.version_info[:3],
                "snapshots": snap,
                "user_agent": UA,
                "urls": {"recommendation": WCAG22_URL, "errata": ERRATA_URL,
                         "understanding": "https://www.w3.org/WAI/WCAG22/Understanding/",
                         "techniques": "https://www.w3.org/WAI/WCAG22/Techniques/",
                         "wcag21": OTHER_SPECS["wcag21"], "wcag20": OTHER_SPECS["wcag20"],
                         "wcag30": OTHER_SPECS["wcag30"], "npm": NPM_LATEST % "<package>"},
                "licence": ("WCAG 2.2 and its Understanding documents are W3C documents (W3C Document "
                            "License). This lock holds hashes, dates, versions, counts, URLs and "
                            "one-line errata summaries only."),
            }
            for k in list(live["tests"] or {}):  # never store test output in the lock
                live["tests"][k].pop("tail", None)
            ordered = {"meta": live.pop("meta")}
            ordered.update(live)
            tmp = args.lock + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(ordered, fh, indent=2, sort_keys=False, ensure_ascii=False)
                fh.write("\n")
            os.replace(tmp, args.lock)
            live = ordered

    summary = summarize(lock, live, skipped) if (rows and lock) else []
    report = render(mode, live, args.lock, rows, errors, notes, skipped, summary)
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
