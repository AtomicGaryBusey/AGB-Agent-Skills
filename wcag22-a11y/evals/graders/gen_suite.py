#!/usr/bin/env python3
"""Generate the `claude plugin eval` suite for this skill from the key spec
(keyspec.json + one specs/<fixture>.json per seeded fixture; see spec.py).

Writes (all under evals/plugin/, which is a generated wrapper plugin):
  .claude-plugin/plugin.json      manifest; experimental.evals = "cases"
  skills/<skill>/                 symlinks to the skill's SKILL.md and folders
                                  (not evals/, so the answer key is not in the
                                  skill's base directory)
  cases/<case>/case.yaml          prompt + run limits
  cases/<case>/scaffold.sh        copies the case's own fixture project (and
                                  nothing else) into the run workspace
                                  (needs --scaffold)
  cases/<case>/graders/*.md       regex / tool_used / llm graders

The answer key content lives only in the spec files and the generated graders/
(which `claude plugin eval` hides from the agent). The workspace gets the
case's fixture project only, never answer-key.md or another fixture.

SKILL.md is linked even when it does not exist yet (a dangling link, with a
warning), so the suite can be generated before the skill is written and works
unchanged once it is.

Env: EVAL_BASH=1 adds Bash to the audit cases' allowed_tools (the runner must
then also pass --allow-tools Bash; run_plugin_eval.sh does this for EVAL_BASH=1).

Usage: python3 evals/graders/gen_suite.py      (run from anywhere)
"""
import json
import os
import re
import shutil
from pathlib import Path

import spec as specmod

HERE = Path(__file__).resolve().parent          # evals/graders
EVALS = HERE.parent                              # evals
REPO = EVALS.parent                              # skill root
PLUGIN = EVALS / "plugin"
SPEC = specmod.load()
SKILL = SPEC["skill"]
TOL = SPEC.get("tolerance", 1)
SEV_RE = SPEC["severity_words"]
FINDING_SEVS = SPEC.get("finding_severities", ["Nonconformity", "Deviation"])
SKIP_TOP = {".git", "evals", "tools", "SOURCES.lock", ".gitignore", "__pycache__", ".DS_Store",
            ".pytest_cache", ".cache", "node_modules"}

AUDIT_TURNS = 50
AUDIT_TIMEOUT = 1800
AUDIT_TOOLS = ["Read", "Glob", "Grep", "Skill"]
if os.environ.get("EVAL_BASH") == "1":
    AUDIT_TOOLS = AUDIT_TOOLS + ["Bash"]


def windows(lines, tol):
    """Seeded lines/ranges widened by the tolerance: [(lo, hi), ...]."""
    out = []
    for item in lines:
        lo, hi = (item, item) if isinstance(item, int) else item
        out.append((max(1, lo - tol), hi + tol))
    return out


def _same_len(lo, hi):
    """Regex for fixed-width digit strings lo..hi (equal length, lo <= hi)."""
    if lo == hi:
        return lo
    if len(lo) == 1:
        return f"[{lo}-{hi}]"
    if lo[0] == hi[0]:
        return lo[0] + _same_len(lo[1:], hi[1:])
    n = len(lo) - 1
    if lo[1:] == "0" * n and hi[1:] == "9" * n:
        return f"[{lo[0]}-{hi[0]}]\\d{{{n}}}"
    parts = [lo[0] + "(?:" + _same_len(lo[1:], "9" * n) + ")"]
    a, b = int(lo[0]) + 1, int(hi[0]) - 1
    if a <= b:
        parts.append((f"[{a}-{b}]" if a < b else str(a)) + f"\\d{{{n}}}")
    parts.append(hi[0] + "(?:" + _same_len("0" * n, hi[1:]) + ")")
    return "(?:" + "|".join(parts) + ")"


def int_range(lo, hi):
    """Regex matching the decimal integers lo..hi (no leading zeros)."""
    parts, lo = [], max(lo, 1)
    while lo <= hi:
        top = min(hi, 10 ** len(str(lo)) - 1)
        parts.append(_same_len(str(lo), str(top)))
        lo = top + 1
    return "(?:" + "|".join(parts) + ")"


def int_ge(lo):
    """Regex matching every decimal integer >= lo."""
    d = len(str(lo))
    return f"(?:{int_range(lo, 10 ** d - 1)}|[1-9]\\d{{{d},}})"


# A cited location is `file` + a first separator + a list of items (N or N-M),
# continued by `, N`, `, :N`, `` `, `:N` `` or `and N` (never across another
# file name, because each item must start with a digit). Examples that match:
# file:38 | file#L38 | file line 38 | file, lines 38-40 | file:2,8 |
# `file:5`, `:7-15`, `:31-40` | file:19-28
DASH = r"[ \t]?[-–][ \t]?"
FIRST_SEP = r"[`'\"]?(?:[:#]L?[ \t]?|,?[ \t]+\(?(?:lines?|l\.|L)[ \t]*)"
NEXT_SEP = r"[`'\"]?[ \t]*(?:,|;|\band\b)[ \t]*[`'\"]?:?[ \t]?"
ITEM = r"\d+(?:" + DASH + r"\d+)?"


def loc_re(fname, lines, tol, mode="defect"):
    """mode "defect": a single line inside a tolerance window, or a range that
    overlaps one. mode "decoy": a single line inside a window, or a range that
    lies entirely inside the hull of this file's seeded lines ± tolerance (so
    a wider range that merely overlaps a decoy's line does not count against
    the auditor)."""
    hits, wins = [], windows(lines, tol)
    for lo, hi in wins:
        hits.append(int_range(lo, hi) + r"(?!\d|" + DASH + r"\d)")
        if mode == "defect":
            hits.append(int_range(1, hi) + DASH + int_ge(lo) + r"(?!\d)")
    if mode == "decoy":  # a range inside the hull of this file's seeded lines
        lo, hi = min(w[0] for w in wins), max(w[1] for w in wins)
        hits.append(int_range(lo, hi) + DASH + int_range(lo, hi) + r"(?!\d)")
    return (re.escape(fname) + FIRST_SEP + "(?:" + ITEM + NEXT_SEP + ")*?"
            + "(?:" + "|".join(hits) + ")")


def location_alt(d, tol_default=TOL, mode="defect"):
    tol = d.get("tol", tol_default)
    parts = [loc_re(f, ls, tol, mode) for f, ls in d.get("locs", [])]
    parts += d.get("anchors", [])
    return "|".join(parts)


def row_pattern(*alts):
    looks = "".join(f"(?=[^\\n]*(?:{a}))" for a in alts if a)
    return "^" + looks + r"\|[^\n]*$"


# Findings table, fixed by SKILL.md:
# | # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
CELL = r"(?:[^|\n\\]|\\.)*"
CELL_LAZY = r"(?:[^|\n\\]|\\.)*?"


def cell_with(x):
    return CELL_LAZY + "(?:" + x + ")" + CELL


def finding_row_pattern(loc, kw, sev):
    """A findings-table row whose Severity cell carries `sev`, whose Location
    cell (6th) cites `loc`, and whose Check ID, Ref or Finding cell carries
    `kw`. Mentions in Target, Evidence or Fix do not count, nor do bullets,
    prose or other tables (they do not have this cell layout)."""
    C = CELL + r"\|"
    kw_look = ""
    if kw:
        kw_look = ("(?=" + cell_with(kw) + r"\||" + C + cell_with(kw) + r"\||"
                   + C * 4 + cell_with(kw) + r"\|)")
    return (r"^\|" + C + cell_with(sev) + r"\|" + kw_look
            + C * 3 + cell_with(loc) + r"\|")


def sev_alt(sevs):
    return r"\b(?:" + "|".join(SEV_RE[s] for s in sevs) + r")\b"


def grader(kind, body, **fm):
    lines = ["---", f"type: {kind}"]
    for k, v in fm.items():
        lines.append(f"{k}: {json.dumps(v)}")
    lines.append("---")
    return "\n".join(lines) + "\n" + body.strip() + "\n"


def skill_input_match():
    return r'"skill"\s*:\s*"(?:[\w-]+:)?' + re.escape(SKILL) + r'"'


SCAFFOLD = """#!/bin/bash
# Generated by evals/graders/gen_suite.py. Runs (with --scaffold) in the run's
# empty workspace. Copies the fixture project in, without the answer key, and
# makes ~/.claude/skills/{skill} resolve inside the run's sandbox HOME so the
# skill's absolute paths work.
set -euo pipefail
case_dir="$(cd "$(dirname "$0")" && pwd -P)"
evals_dir="$(cd "$case_dir/../../.." && pwd -P)"
{copy}
mkdir -p "$HOME/.claude/skills"
ln -sfn "$evals_dir/plugin/skills/{skill}" "$HOME/.claude/skills/{skill}"
"""


def write_case(name, prompt, graders, turns, timeout, tools, fixture_dir, tags):
    cdir = PLUGIN / "cases" / name
    if cdir.exists():
        shutil.rmtree(cdir)
    (cdir / "graders").mkdir(parents=True)
    y = {
        "schema_version": "1.1",
        "name": name,
        "tags": tags,
        "runs": 1,
        "execution": {
            "prompt": prompt,
            "max_turns": turns,
            "timeout_seconds": timeout,
            "allowed_tools": tools,
        },
    }
    if fixture_dir:
        y["context"] = {"scaffold_script": "scaffold.sh"}
        copy = (f'rsync -a --exclude "__pycache__" --exclude ".DS_Store" '
                f'--exclude "answer-key.md" "$evals_dir/{fixture_dir}/" ./')
        (cdir / "scaffold.sh").write_text(SCAFFOLD.format(skill=SKILL, copy=copy))
        os.chmod(cdir / "scaffold.sh", 0o755)
    # case.yaml as JSON-compatible YAML (valid YAML 1.2)
    (cdir / "case.yaml").write_text(
        "# Generated by evals/graders/gen_suite.py; edit graders/keyspec.json or graders/specs/ instead.\n"
        + json.dumps(y, indent=2, ensure_ascii=False) + "\n")
    for gname, text in graders.items():
        (cdir / "graders" / f"{gname}.md").write_text(text)


def build_plugin():
    PLUGIN.mkdir(exist_ok=True)
    (PLUGIN / ".claude-plugin").mkdir(exist_ok=True)
    (PLUGIN / ".claude-plugin" / "plugin.json").write_text(json.dumps({
        "name": SPEC["plugin"],
        "version": "0.0.1",
        "description": f"Eval-only wrapper that loads the {SKILL} skill without its evals/ folder.",
        "experimental": {"evals": "cases"},
    }, indent=2) + "\n")
    sdir = PLUGIN / "skills" / SKILL
    if sdir.exists():
        shutil.rmtree(sdir)
    sdir.mkdir(parents=True)
    names = {e.name for e in REPO.iterdir() if e.name not in SKIP_TOP}
    names.add("SKILL.md")
    for name in sorted(names):
        os.symlink(os.path.relpath(REPO / name, sdir), sdir / name)
    if not (REPO / "SKILL.md").is_file():
        print(f"warning: {SKILL}/SKILL.md does not exist yet; "
              f"plugin/skills/{SKILL}/SKILL.md is a dangling link until it is written")


def no_peek_pattern(fx):
    """Shared pattern (answer keys, spec files, graders/, evals/fixtures) plus
    the fixture's own extras (for example its pre-repo held-out path)."""
    return "|".join(p for p in (SPEC["no_peek"], fx.get("no_peek_extra")) if p)


def audit_graders(cname, c):
    fx = SPEC["fixture_specs"][c["fixture"]]
    tol = fx.get("tolerance", TOL)
    decoys = fx["decoy_defs"]
    g = {"skill-used": grader("tool_used", "", tool="Skill",
                              input_match=skill_input_match(), min=1)}
    for d in SPEC["defects"]:
        if d["case"] != cname:
            continue
        loc = location_alt(d, tol)
        g[f"recall-{d['id']}"] = grader(
            "regex", row_pattern(loc, d.get("kw", "")), flags="mi")
        g[f"severity-{d['id']}"] = grader(
            "regex", row_pattern(loc, d.get("kw", ""), sev_alt(d["sev"])),
            flags="mi")
    for did in c["decoys"]:
        if decoys[did].get("regex") is False:
            continue
        row = decoys[did]["row"]
        g[f"nodecoy-{did}"] = grader(
            "regex", finding_row_pattern(location_alt(row, tol, "decoy"),
                                         row.get("kw", ""), sev_alt(FINDING_SEVS)),
            flags="mi", match="not_contains")
    listed = "\n".join(f"- {did}: {decoys[did]['desc']}" for did in c["decoys"])
    if c["decoys"]:
        g["nodecoy-judge"] = grader("llm", f"""
PASS if none of the properties listed below is reported as a Level A or AA
violation. FAIL if any listed property is itself reported as one: a
findings-table row with severity Nonconformity or Deviation whose subject IS
that property, or a statement that the property violates a Level A or AA
success criterion.

The reply is a WCAG 2.2 Level AA accessibility audit report. Each listed item
is a specific property of the audited project that is known to be COMPLIANT
(a decoy or a non-scored note).

{listed}

How to judge each item:
- Findings about OTHER problems that happen to mention the same file, line or
  success criterion do not count (for example a real defect on a neighbouring
  element, or the same technique used wrongly on a different page).
- Calling the property compliant, passing, excepted or "no finding" is fine.
  So is a best-practice remark, an Advisory or Review note, or a note that it
  matters only at AAA, when it is clearly not presented as a Level A/AA
  violation.

If FAIL, name the decoy.
""", weight=0.001)  # informational (eval rejects 0): see README "Known limits"

    if c.get("decoy_judge_strict"):
        g["decoy-verdicts"] = grader("llm", f"""
The user asked about the queried items listed below; all of them are
COMPLIANT with WCAG 2.2 Level AA.

{listed}

PASS only if the reply gives an explicit verdict for each queried item and
every verdict is "compliant / passes / exception applies / not a Level AA
failure" (a remark that the item could optionally be improved, is best
practice, or would matter only at AAA is acceptable as long as it is not
presented as a Level A/AA failure, nonconformity or deviation).
FAIL if any item is called a Level A/AA failure, nonconformity, deviation or
defect, or if the reply gives no verdict for an item.
""")
    g["no-peek"] = grader("regex", no_peek_pattern(fx),
                          target="trace", match="not_contains")
    return g


def main():
    build_plugin()
    cases_dir = PLUGIN / "cases"
    if cases_dir.exists():
        shutil.rmtree(cases_dir)
    for cname, c in SPEC["cases"].items():
        fx = SPEC["fixture_specs"][c["fixture"]]
        write_case(cname, c["prompt"], audit_graders(cname, c), AUDIT_TURNS,
                   AUDIT_TIMEOUT, AUDIT_TOOLS, fx["fixture"], ["audit"])
    for rname, prompt in SPEC["refusals"].items():
        g = {"skill-not-used": grader("tool_used", "", tool="Skill",
                                      input_match=skill_input_match(),
                                      min=0, max=0)}
        write_case(rname, prompt, g, 4, 300, ["Read", "Glob", "Grep", "Skill"],
                   None, ["refusal"])
    per_fx = ", ".join(f"{n} {sum(c['fixture'] == n for c in SPEC['cases'].values())}"
                       for n in SPEC["fixture_specs"])
    print(f"wrote {len(SPEC['cases'])} audit cases ({per_fx}) and "
          f"{len(SPEC['refusals'])} refusal cases under {PLUGIN.relative_to(REPO)}")


if __name__ == "__main__":
    main()
