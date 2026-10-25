#!/usr/bin/env python3
"""Check a branch prepared for a Fox-IT repository (dissect.*, flow.record, acquire, ...) against Fox-IT's
contribution rules: the target, the branch, each commit message, the pull request description, the added code, and
(with --run-tox) the repository's own lint and tests. Rules and their sources: references/guides.md.

Standard library only; Python 3.9 or later; needs git, and gh for --pr and --check-cla.

    foxit_pr_check.py [REPO] [--base REF] [--pr-body FILE | --pr N] [--run-tox] [--check-cla] [--json]

Exit status: 0 with no FAIL, 1 with one or more, 2 when the check itself could not run.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass

SUBJECT_SOFT = 50                   # "as much as possible"
SUBJECT_HARD = 72
BODY_WRAP = 72
BRANCH_PREFIXES = ("fix/", "feature/")
CLOSING = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+(?:[\w.-]+/[\w.-]+)?#\d+", re.IGNORECASE)
ATTRIBUTION = re.compile(r"^(?:co-authored-by:.*\b(?:claude|anthropic)\b|claude-session:|.*generated with \[?claude)",
                         re.IGNORECASE | re.MULTILINE)
TYPE_NAMES = {"list", "dict", "set", "tuple", "str", "int", "bytes", "bytearray", "float", "bool", "type", "object"}
NON_IMPERATIVE = re.compile(r"^(?:[A-Z][a-z]+(?:ed|ing)|[A-Z][a-z]+[^s]s|Fixes|Adds|Updates|Removes|Creates)\b")
IMPERATIVE_EXCEPTIONS = {"Address", "Process", "Pass", "Access", "Bypass", "Express", "Focus", "Embed", "Need",
                         "Feed", "Speed", "Seed", "Shed", "Bring", "String", "Ring", "Wing"}


@dataclass
class Finding:
    level: str          # FAIL, WARN, PASS, INFO
    rule: str
    message: str


class CheckError(Exception):
    pass


def git(repo: str, *args: str, check: bool = True) -> str:
    done = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    if check and done.returncode:
        raise CheckError(f"git {' '.join(args)}: {done.stderr.strip()}")
    return done.stdout


# -- the target and the branch ----------------------------------------------------------------------------------

def fox_it_remote(repo: str) -> tuple[str, str] | None:
    """(remote name, owner/name) of the remote that points at a fox-it repository, or None."""
    for line in git(repo, "remote", "-v").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            match = re.search(r"github\.com[:/](fox-it/[\w.-]+?)(?:\.git)?$", parts[1], re.IGNORECASE)
            if match:
                return parts[0], match.group(1)
    return None


def check_target(repo: str, base: str | None) -> tuple[list[Finding], str | None]:
    found = fox_it_remote(repo)
    if found is None:
        return [Finding("FAIL", "repo-target", "no remote points at a github.com/fox-it/ repository; add Fox-IT's "
                                               "as `upstream`")], None
    remote, name = found
    base = base or f"{remote}/main"
    out = [Finding("PASS", "repo-target", f"targets {name} (remote {remote})")]
    if not git(repo, "rev-parse", "--verify", "--quiet", base, check=False).strip():
        out.append(Finding("FAIL", "base-current", f"{base} is not known here: `git fetch {remote}` first"))
        return out, None
    if subprocess.run(["git", "-C", repo, "merge-base", "--is-ancestor", base, "HEAD"]).returncode:
        out.append(Finding("WARN", "base-current", f"the branch is not based on {base}'s tip: rebase onto it (and "
                                                   f"`git fetch {remote}` for the latest)"))
    else:
        out.append(Finding("PASS", "base-current", f"based on {base} (as last fetched)"))
    return out, base


def check_branch(repo: str) -> list[Finding]:
    branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if branch in ("main", "master", "HEAD"):
        return [Finding("FAIL", "branch-name", f"working on {branch!r}: use a branch such as fix/... or feature/...")]
    if not branch.startswith(BRANCH_PREFIXES):
        return [Finding("WARN", "branch-name", f"branch {branch!r} has no fix/ or feature/ prefix")]
    return [Finding("PASS", "branch-name", f"branch {branch!r}")]


# -- commit messages ------------------------------------------------------------------------------------------------

def check_message(message: str, label: str = "commit") -> list[Finding]:
    """The commit message rules, for one message."""
    out = []
    lines = message.rstrip("\n").split("\n")
    subject = lines[0] if lines else ""
    where = f"{label}: {subject[:60]!r}"
    if len(subject) > SUBJECT_HARD:
        out.append(Finding("FAIL", "commit-subject-length", f"{where}: subject is {len(subject)} characters (limit "
                                                            f"{SUBJECT_SOFT}, at most {SUBJECT_HARD})"))
    elif len(subject) > SUBJECT_SOFT:
        out.append(Finding("WARN", "commit-subject-length", f"{where}: subject is {len(subject)} characters (limit "
                                                            f"{SUBJECT_SOFT} as much as possible)"))
    if subject and not subject[0].isupper():
        out.append(Finding("FAIL", "commit-capital", f"{where}: subject does not start with a capital letter"))
    if subject.endswith("."):
        out.append(Finding("FAIL", "commit-period", f"{where}: subject ends with a period"))
    first = subject.split(" ", 1)[0] if subject else ""
    if first and first not in IMPERATIVE_EXCEPTIONS and NON_IMPERATIVE.match(first):
        out.append(Finding("WARN", "commit-imperative", f"{where}: {first!r} is not the imperative mood (Fix, Add, "
                                                        f"Create)?"))
    if len(lines) > 1 and lines[1].strip():
        out.append(Finding("FAIL", "commit-blank-line", f"{where}: no blank line between the subject and the body"))
    long_lines = [n for n, line in enumerate(lines[2:], 3) if len(line) > BODY_WRAP
                  and not re.search(r"https?://\S{40,}", line) and not line.startswith(("    ", "\t"))]
    if long_lines:
        out.append(Finding("WARN", "commit-body-wrap", f"{where}: body lines {', '.join(map(str, long_lines[:8]))} "
                                                       f"are longer than {BODY_WRAP} characters"))
    if ATTRIBUTION.search(message):
        out.append(Finding("FAIL", "ai-attribution", f"{where}: carries an AI attribution trailer (local policy: the "
                                                     f"CLA has the author represent the work as their own)"))
    if not any(f.level == "FAIL" for f in out) and not out:
        out.append(Finding("PASS", "commit-message", f"{where}"))
    return out


def commits(repo: str, base: str) -> list[tuple[str, str]]:
    raw = git(repo, "log", "--format=%H%x00%B%x1e", f"{base}..HEAD")
    out = []
    for record in raw.split("\x1e"):
        record = record.strip("\n")
        if record:
            sha, _, message = record.partition("\x00")
            out.append((sha, message))
    return out


def check_commits(repo: str, base: str) -> list[Finding]:
    found = commits(repo, base)
    if not found:
        return [Finding("FAIL", "one-change", f"no commits on top of {base}")]
    out = []
    if len(found) > 1:
        out.append(Finding("WARN", "one-change", f"{len(found)} commits: one fix per branch is squashed on "
                                                 f"acceptance; several must each stand alone (discuss first)"))
    for sha, message in reversed(found):
        out += check_message(message, f"commit {sha[:8]}")
    return out


# -- the pull request description ----------------------------------------------------------------------------------

def check_pr_body(body: str) -> list[Finding]:
    text = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL).strip()      # the template's own comment
    out = []
    words = re.sub(r"\s+", " ", CLOSING.sub("", text)).strip()
    if len(words) < 40:
        out.append(Finding("FAIL", "pr-description", "the description says too little: what changed and why"))
    else:
        out.append(Finding("PASS", "pr-description", "a description is present"))
    if not re.search(r"\b(?:test|tests|tested|testing|tox|pytest|reproduc\w*)\b", text, re.IGNORECASE):
        out.append(Finding("WARN", "pr-description", "nothing says how to test the change"))
    if CLOSING.search(text):
        out.append(Finding("PASS", "pr-closing-keyword", f"links its issue ({CLOSING.search(text).group(0)})"))
    else:
        out.append(Finding("WARN", "pr-closing-keyword", "no closing keyword (fixes #N, closes #N, resolves #N): link "
                                                         "the issue here or under the PR's Development section"))
    if ATTRIBUTION.search(text):
        out.append(Finding("FAIL", "ai-attribution", "the description carries an AI attribution line (local policy)"))
    return out


# -- the changed code ---------------------------------------------------------------------------------------------

def changed_files(repo: str, base: str) -> list[str]:
    return [line for line in git(repo, "diff", "--name-only", "--diff-filter=AMR", f"{base}...HEAD").splitlines()
            if line]


def added_lines(repo: str, base: str, path: str) -> set[int]:
    """Line numbers (in the new file) the branch added or changed."""
    out, line = set(), 0
    for row in git(repo, "diff", "--unified=0", f"{base}...HEAD", "--", path).splitlines():
        hunk = re.match(r"@@ -\S+ \+(\d+)(?:,(\d+))? @@", row)
        if hunk:
            start, count = int(hunk.group(1)), int(hunk.group(2) or "1")
            out.update(range(start, start + count))
    return out


def check_code(repo: str, base: str) -> list[Finding]:
    out = []
    files = changed_files(repo, base)
    package = [f for f in files if f.endswith(".py") and not f.startswith(("tests/", "test/"))
               and "/_docs/" not in f]
    tests = [f for f in files if f.startswith(("tests/", "test/"))]
    if package and not tests:
        out.append(Finding("WARN", "tests-added", f"code changed ({', '.join(package[:4])}) but no test: new code "
                                                  f"and large refactors come with unit tests"))
    elif package:
        out.append(Finding("PASS", "tests-added", f"tests changed too ({', '.join(tests[:4])})"))
    if "pyproject.toml" in files:
        diff = git(repo, "diff", f"{base}...HEAD", "--", "pyproject.toml")
        if re.search(r"^[+-].*(?:dependencies|\b[a-z0-9_.-]+\s*[<>=~!]=)", diff, re.MULTILINE | re.IGNORECASE):
            messages = " ".join(m for _, m in commits(repo, base))
            if not re.search(r"depend", messages, re.IGNORECASE):
                out.append(Finding("WARN", "deps-reason", "pyproject.toml's dependencies changed: give the reason in "
                                                          "the commit message"))
    for path in package + [f for f in tests if f.endswith(".py")]:
        full = os.path.join(repo, path)
        try:
            with open(full, encoding="utf-8") as handle:
                source = handle.read()
            tree = ast.parse(source)
        except (OSError, SyntaxError, ValueError):
            continue
        out += check_ast(path, tree, added_lines(repo, base, path), is_test=path in tests)
    return out


def check_ast(path: str, tree: ast.AST, added: set[int], is_test: bool = False) -> list[Finding]:
    """Names, type hints and cstruct loading, in the lines the branch added."""
    out = []

    def where(node: ast.AST) -> str:
        return f"{path}:{getattr(node, 'lineno', '?')}"

    for node in ast.walk(tree):
        line = getattr(node, "lineno", None)
        if line not in added:
            continue
        names = []
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.append(node.id)
        elif isinstance(node, ast.arg) and node.arg not in ("self", "cls"):
            names.append(node.arg)
        for name in names:
            if len(name) == 1 and name != "_":
                out.append(Finding("WARN", "names", f"{where(node)}: single-character name {name!r}"))
            elif name in TYPE_NAMES:
                out.append(Finding("WARN", "names", f"{where(node)}: {name!r} is named after its type"))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not is_test:
            unhinted = [a.arg for a in node.args.posonlyargs + node.args.args + node.args.kwonlyargs
                        if a.annotation is None and a.arg not in ("self", "cls")]
            if unhinted or node.returns is None:
                missing = (f"arguments {', '.join(unhinted)}" if unhinted else "") + (
                    (" and " if unhinted else "") + "return type" if node.returns is None else "")
                out.append(Finding("WARN", "type-hints", f"{where(node)}: {node.name}() has no {missing} hint"))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "load" \
                and node.args and isinstance(node.args[0], (ast.Constant, ast.JoinedStr)) \
                and isinstance(getattr(node.args[0], "value", ""), str):
            out.append(Finding("WARN", "cstruct-split", f"{where(node)}: a cstruct definition loaded inline; keep the "
                                                        f"definition in its own string (c_obj = cstruct().load(c_def))"))
    return out


# -- tox and the CLA ----------------------------------------------------------------------------------------------

def tox_envs(repo: str) -> list[str]:
    try:
        with open(os.path.join(repo, "tox.ini"), encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        return []
    match = re.search(r"^envlist\s*=\s*(.+)$", text, re.MULTILINE)
    return [e.strip() for e in match.group(1).split(",")] if match else []


def run_tox(repo: str, tox: str) -> list[Finding]:
    envs = tox_envs(repo)
    if not envs:
        return [Finding("WARN", "tox-lint", "no tox.ini envlist: run the repository's lint and tests by hand")]
    out = []
    for env in [e for e in envs if e == "lint"] + [e for e in envs if re.fullmatch(r"py3\d*", e)][:1]:
        done = subprocess.run([tox, "-e", env], cwd=repo, capture_output=True, text=True, encoding="utf-8",
                              errors="replace")
        rule = "tox-lint" if env == "lint" else "tox-tests"
        tail = " | ".join(line for line in done.stdout.splitlines()[-3:] if line.strip())
        out.append(Finding("PASS" if done.returncode == 0 else "FAIL", rule,
                           f"tox -e {env}: {'passed' if done.returncode == 0 else 'failed'} ({tail[:200]})"))
    if "pypy3" in envs:
        out.append(Finding("INFO", "tox-tests", "pypy3 not run here; CI runs it"))
    return out


def gh(*args: str) -> str:
    done = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if done.returncode:
        raise CheckError(f"gh {' '.join(args[:3])}: {done.stderr.strip()[:200]}")
    return done.stdout


def check_cla(target: str, pr: int) -> list[Finding]:
    """Whether DissectBot asked for the CLA on this PR and the author agreed (read-only)."""
    comments = json.loads(gh("api", f"repos/{target}/issues/{pr}/comments", "--paginate"))
    asked = any(c["user"]["login"] == "DissectBot" and "License Agreement" in c["body"] for c in comments)
    agreed = any(re.search(r"@DissectBot\s+agree", c["body"]) for c in comments)
    if agreed:
        return [Finding("PASS", "cla", "the author has replied @DissectBot agree")]
    if asked:
        return [Finding("INFO", "cla", "DissectBot asks for the CLA: the author (never an agent) replies "
                                       "`@DissectBot agree` or `@DissectBot agree company=\"...\"`")]
    return [Finding("INFO", "cla", "no CLA request on this PR (already accepted on an earlier one, or not yet asked)")]


# -- running ------------------------------------------------------------------------------------------------------

def run(args) -> list[Finding]:
    repo = os.path.abspath(args.repo)
    if not os.path.isdir(os.path.join(repo, ".git")) and not git(repo, "rev-parse", "--git-dir", check=False).strip():
        raise CheckError(f"{repo} is not a git repository")
    findings, base = check_target(repo, args.base)
    findings += check_branch(repo)
    if base:
        findings += check_commits(repo, base)
        findings += check_code(repo, base)
    body = None
    target = (fox_it_remote(repo) or (None, None))[1]
    if args.pr_body:
        with open(args.pr_body, encoding="utf-8") as handle:
            body = handle.read()
    elif args.pr is not None and target:
        body = json.loads(gh("pr", "view", str(args.pr), "--repo", target, "--json", "body"))["body"]
    if body is not None:
        findings += check_pr_body(body)
    else:
        findings.append(Finding("INFO", "pr-description", "no PR description given (--pr-body FILE or --pr N)"))
    if args.run_tox:
        tox = args.tox or shutil.which("tox")
        findings += run_tox(repo, tox) if tox else [Finding("WARN", "tox-lint", "tox not found: install tox, or "
                                                                                 "pass --tox PATH")]
    else:
        findings.append(Finding("INFO", "tox-lint", "lint and tests not run (--run-tox): CI rejects a failing PR "
                                                    "before review"))
    if args.check_cla and args.pr is not None and target:
        findings += check_cla(target, args.pr)
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a branch prepared for a Fox-IT repository against Fox-IT's "
                                                 "contribution rules (references/guides.md).")
    parser.add_argument("repo", nargs="?", default=".", help="the clone, on the branch to check (default: here)")
    parser.add_argument("--base", help="what the branch is based on (default: the fox-it remote's main)")
    parser.add_argument("--pr-body", metavar="FILE", help="the pull request description, as a file")
    parser.add_argument("--pr", type=int, metavar="N", help="an opened pull request: its description (and CLA) by gh")
    parser.add_argument("--run-tox", action="store_true", help="run the repository's tox lint and py3 environments")
    parser.add_argument("--tox", metavar="PATH", help="the tox to run (default: tox on PATH)")
    parser.add_argument("--check-cla", action="store_true", help="with --pr: whether the CLA is accepted")
    parser.add_argument("--json", action="store_true", help="the findings as JSON")
    args = parser.parse_args(argv)
    try:
        findings = run(args)
    except CheckError as exc:
        print(f"foxit_pr_check: {exc}", file=sys.stderr)
        return 2
    utf8 = (getattr(sys.stdout, "encoding", "") or "").lower().replace("-", "") == "utf8"
    if args.json:     # ASCII JSON (lossless \uXXXX escapes) where stdout is not UTF-8, as the repo's other CLIs do
        print(json.dumps([asdict(f) for f in findings], indent=1, ensure_ascii=not utf8))
    else:
        for f in findings:
            print(f"{f.level:<4}  {f.rule:<22} {f.message}")
        counts = {level: sum(1 for f in findings if f.level == level) for level in ("FAIL", "WARN", "PASS")}
        print(f"\n{counts['FAIL']} FAIL, {counts['WARN']} WARN, {counts['PASS']} PASS")
    return 1 if any(f.level == "FAIL" for f in findings) else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")     # a Windows cp1252 console or pipe (as ef28398)
    sys.exit(main())
