---
name: foxit-pr-check
description: "Review a branch or pull request prepared for a Fox-IT open-source repository (fox-it/dissect.*, dissect.target, dissect.cstruct, flow.record, acquire, ...) against Fox-IT's contribution rules before it is pushed or opened: the Developing, Style guide and Tooling pages (docs.dissect.tools/en/latest/contributing/), the repository's own tox.ini, pyproject.toml (Ruff) and pull request template. USE FOR: commit message format (50-character imperative subject, 72-column body), fix/ and feature/ branches, one change per branch, the PR description and its closing keyword, running the repo's tox lint and tests, missing unit tests, type hints, names, cstruct definitions, dependency reasons, and whether the CLA (DissectBot) is accepted. DO NOT USE FOR: reviewing what the code does (correctness, design); repositories outside fox-it; accepting the CLA (only the author may)."
metadata:
  author: local
  version: "1.0.0"
  sources: "docs.dissect.tools contributing pages (Developing, Style guide, Tooling) as read 2026-10-24; each target repository's tox.ini, pyproject.toml and .github/pull_request_template.md, read at check time"
---

# Fox-IT pull request check

Fox-IT's projects share one contribution process (Dissect's documentation). This skill checks that a contribution
**conforms** to it, so CI and the reviewers see a pull request that follows the rules. It does not judge whether the
change is right; review that separately.

**Sources, in order of authority** (details and every rule: `references/guides.md`):

1. The target repository's `tox.ini` and `pyproject.toml`: what CI runs. They use **Ruff** (lint and format, line
   length 120, Google docstrings) and **vermin** (the minimum Python). The guide pages still name Black and Flake8.
2. Its `.github/pull_request_template.md` (commit style, description, closing keywords).
3. The Developing, Style guide and Tooling pages.

## Run the checker

`scripts/foxit_pr_check.py` (standard library; needs `git`, and `gh` for `--pr` and `--check-cla`) checks a clone
on the branch to submit, with Fox-IT's repository as a remote (usually `upstream`):

```bash
python3 ~/.claude/skills/foxit-pr-check/scripts/foxit_pr_check.py PATH/TO/CLONE \
    --pr-body pr.md --run-tox            # before opening: the description as a file, and the repo's own tox
python3 ~/.claude/skills/foxit-pr-check/scripts/foxit_pr_check.py PATH/TO/CLONE --pr 42 --check-cla   # once opened
```

- `git fetch upstream` first: "based on main" is checked against the last fetch.
- `--run-tox` runs the repo's `tox -e lint` and `tox -e py3` (tox 4.27 or later provisions Ruff, vermin and pytest
  itself; `--tox PATH` for a tox outside `PATH`). CI also runs `pypy3`, and a failing CI gets no manual review.
- Exit status 0 with no FAIL, 1 with any, 2 when the check could not run. `--json` for the findings as data.

| Level | Meaning |
|---|---|
| **FAIL** | Breaks a stated rule (a lower-case or full-stop subject, no blank line after it, no fox-it remote, working on `main`, tox failing, an AI attribution trailer) |
| **WARN** | A rule stated loosely ("as much as possible"), or a heuristic: subject over 50, not imperative, body over 72, no `fix/` prefix, several commits, no test, names, hints, an inline cstruct, a dependency without a reason, no closing keyword |
| **PASS** / **INFO** | Checked and fine; or not checked, with why |

## Then judge what no tool can

Work through the "Left to judgement" list in `references/guides.md`: one self-contained change; a description that
says what and why and how to test; Google docstrings (summary line, blank line, `Args:`/`Returns:`/`Raises:`, no
types); import groups; cstruct naming close to the original; `dissect.target`'s path rule. Confirm each WARN or
dismiss it with a reason.

## Report

List FAIL first, then WARN, each with its rule ID, the file or commit, and the fix. Say what ran (`--run-tox` or not,
the tox environments, the CLA check) and what did not. Do not push, open the pull request, or comment on it unless
the user asks for that step.

## The CLA and attribution

- DissectBot posts Fox-IT's Contribution License Agreement on an account's first pull request. Accepting it is a
  legal act: tell the author the exact reply (`@DissectBot agree`, or `@DissectBot agree company="..."` for work
  made for an employer), and never post it for them.
- `ai-attribution` is this skill's local policy, not Fox-IT's: the CLA has the author represent each contribution
  as their own creation, so commits and the description carry no `Co-Authored-By: Claude`, `Claude-Session:` or
  "Generated with" lines. Remove them before pushing.
