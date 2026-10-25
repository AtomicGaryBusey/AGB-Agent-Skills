# Fox-IT contribution rules, as read 2026-10-24

Fox-IT's open-source projects (`dissect.*`, `flow.record`, `acquire`, ...) share one set of contribution guides,
published with Dissect's documentation:

- Developing: https://docs.dissect.tools/en/latest/contributing/developing.html
- Style guide: https://docs.dissect.tools/en/latest/contributing/style-guide.html
- Tooling: https://docs.dissect.tools/en/latest/contributing/tooling.html

## Which source wins

The guides lag the repositories. On 2026-10-24 they still named Black and Flake8, while the repositories had moved to
Ruff ("Add stricter Ruff linting", "Harmonize ruff config"). Use, in this order:

1. The target repository's own `tox.ini` and `pyproject.toml` (`[tool.ruff]`, dependency groups): what CI runs.
2. Its `.github/pull_request_template.md`.
3. The three guide pages.

Re-read the target's files every time: they differ between repositories and change over time.

## Rules, with the checker's rule IDs

| Rule ID | Rule | Source |
|---|---|---|
| `repo-target` | The pull request goes to a `fox-it/*` repository | scope of this skill |
| `base-current` | The branch is based on the target's current `main` (the release candidate branch) | Developing: branching |
| `branch-name` | Develop on a branch with a prefix such as `feature/` or `fix/` | Developing: branching |
| `one-change` | One self-contained feature or fix per branch; commits are squashed on acceptance. Several commits must each be self-contained, and a different split is discussed first | Developing: branching |
| `commit-blank-line` | Separate the subject from the body with a blank line | Style guide; PR template |
| `commit-subject-length` | Limit the subject to 50 characters "as much as possible" | Style guide; PR template |
| `commit-capital` | Capitalize the subject | Style guide; PR template |
| `commit-period` | Do not end the subject with a period | Style guide; PR template |
| `commit-imperative` | Imperative mood; the verb says what was accomplished (Create, Add, Fix) | Style guide; PR template |
| `commit-body-wrap` | Wrap the body at 72 characters | Style guide; PR template |
| `pr-description` | A description of the changes and how to test them | Developing: pull requests; PR template |
| `pr-closing-keyword` | Link the issue: `close(s/d)`, `fix(es/ed)` or `resolve(s/d) #<nr>`, or associate it under the PR's Development section | PR template |
| `tox-lint` | Lint passes locally: `tox -e lint` (Ruff check and format, vermin for the minimum Python) | Developing; Tooling; `tox.ini` |
| `tox-tests` | Unit tests pass locally: `tox -e py3` (CI also runs `pypy3`); a failing CI gets no manual review | Developing; `tox.ini` |
| `tests-added` | New code and large refactors come with unit tests | Developing: testing |
| `deps-reason` | Few dependencies; a new one goes in `pyproject.toml` with the reason in the commit message | Developing: dependencies |
| `names` | No single-character names; no variables named after their type (`list`, `dict`, ...) | Style guide: naming |
| `type-hints` | New functions and classes fully type hinted (Ruff's `ANN` rules where the repo selects them) | Style guide: typing |
| `cstruct-split` | A cstruct definition is a separate string, loaded on its own line (`c_obj = cstruct().load(c_def)`); `# noqa: E501` keeps a long original layout | Style guide: cstruct |
| `cla` | The CLA is accepted once per account, by replying to DissectBot's comment on the first PR | Developing: CLA |
| `ai-attribution` | (Local policy, not Fox-IT's) No `Co-Authored-By`/`Claude-Session` trailers or "Generated with" lines: the CLA has the author represent the work as their own | owner's choice |

## Left to judgement (no tool can decide these)

- Is the change really one self-contained fix or feature?
- Does the description say what changed and why, and how to test it?
- Docstrings: Google format, a one-line summary then a blank line; `Args:`, `Returns:`, `Raises:`; types from the
  hints, not the docstring; `References:` for URLs.
- Imports: three groups (standard library; external, other Dissect packages included; the project), alphabetical
  in each. Ruff's `I` rules check this where selected.
- cstruct naming: close to the original structure; Microsoft formats `UPPERCASE_NAME` structures with `CamelCase`
  fields (no `dw`/`cb` prefixes); others `lowercase_name`.
- `dissect.target` plugins return the original parsed `path` in records; resolution happens at query time.
- Tuples: a trailing comma after the last item, so the formatter keeps one item per line.
- Supported Python: the minimum in `tox.ini`'s vermin target (`-t=3.10-` on 2026-10-24) and `pyproject.toml`.

## The CLA

DissectBot posts Fox-IT's Contribution License Agreement on an account's first pull request. The author accepts by
replying `@DissectBot agree` (sole ownership, not made for an employer) or `@DissectBot agree company="..."` (made
for an employer, with its permission). It is a legal agreement: only the author posts that reply, never an agent.
