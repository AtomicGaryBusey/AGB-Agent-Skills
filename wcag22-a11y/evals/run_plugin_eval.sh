#!/bin/bash
# Run this skill's plugin-eval suite and record scrubbed results under
# evals/results/<date>/plugin-eval/.  Env knobs:
#   RUNS=1  ABLATION=none|with-without  MAX_COST=15  CASE='<glob>'  MODEL=<id>
#   FIXTURE=larkspur|brightwater  only that fixture's cases (its `case_glob`
#                in graders/specs/<fixture>.json; larkspur's 'wcag-*' also
#                matches the two refusal cases). CASE wins if both are set.
#   JUDGE=sonnet  LABEL=plugin-eval (results subfolder)  DATE=YYYY-MM-DD
#   EVAL_BASH=1  also grant Bash to the audit cases (lets the skill run
#                scripts/wcag_scan.py; see README "Known limits" before using it)
# Local only: --no-publish is always passed.
set -euo pipefail
evals="$(cd "$(dirname "$0")" && pwd -P)"
date="${DATE:-$(date +%F)}"
if [ ! -f "$evals/../SKILL.md" ]; then
  echo "SKILL.md does not exist yet; generate and validate only:" >&2
  echo "  python3 $evals/graders/gen_suite.py && claude plugin validate $evals/plugin" >&2
  exit 3
fi
EVAL_BASH="${EVAL_BASH:-0}" python3 "$evals/graders/gen_suite.py"
raw="$(mktemp -d "${TMPDIR:-/tmp}/plugin-eval-raw.XXXXXX")"
args=(plugin eval "$evals/plugin" --runs "${RUNS:-1}" --ablation "${ABLATION:-none}"
      --no-publish --scaffold --trust-plugin --keep-temp
      --max-cost-usd "${MAX_COST:-15}" --threshold 0
      --output-dir "$raw" --report "$raw/report.html" --json "$raw/result.json")
args+=(--judge-model "${JUDGE:-sonnet}")
# Let the run Read the skill's own files (SKILL.md, references/, scripts/, ...)
# at their real paths, and nothing else outside the workspace (so not evals/).
while IFS= read -r g; do args+=(--allow-tools "$g"); done < <(python3 - "$evals/plugin/skills" <<'PY'
import os, sys
root = sys.argv[1]
for skill in sorted(os.listdir(root)):
    for e in sorted(os.listdir(os.path.join(root, skill))):
        real = os.path.realpath(os.path.join(root, skill, e))
        print(f"Read(/{real}/**)" if os.path.isdir(real) else f"Read(/{real})")
PY
)
[ "${EVAL_BASH:-0}" = 1 ] && args+=(--allow-tools Bash)
if [ -z "${CASE:-}" ] && [ -n "${FIXTURE:-}" ]; then
  CASE="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["case_glob"])' \
          "$evals/graders/specs/$FIXTURE.json")" || { echo "unknown FIXTURE=$FIXTURE" >&2; exit 2; }
fi
[ -n "${CASE:-}" ] && args+=(--case "$CASE")
[ -n "${MODEL:-}" ] && args+=(--model "$MODEL")
set +e
claude "${args[@]}" 2>&1 | tee "$raw/console.log"
status=${PIPESTATUS[0]}
set -e
out="$evals/results/$date"
python3 "$evals/graders/summarize.py" "$raw/result.json" "$out" "${LABEL:-plugin-eval}"
python3 -c "
import sys,importlib.util
spec=importlib.util.spec_from_file_location('s','$evals/graders/summarize.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
for src,dst in [('$raw/report.html','$out/${LABEL:-plugin-eval}/report.html'),('$raw/console.log','$out/${LABEL:-plugin-eval}/console.log')]:
    try: open(dst,'w').write(m.scrub(open(src,errors='replace').read()))
    except OSError: pass
"
# Remove the kept run sandboxes (read-only by design) once harvested.
python3 -c "
import json,re
d=json.load(open('$raw/result.json'))
for c in d.get('cases',[]):
    for arm in c.get('arms',{}).values():
        for r in arm:
            m=re.match(r'(/private/tmp/e-[A-Za-z0-9]+)/',r.get('tracePath') or '')
            if m: print(m.group(1))
" | sort -u | while read -r d; do chmod -R u+rwx "$d" 2>/dev/null; rm -rf "$d"; done
echo "raw result kept at $raw (outside the repo); exit status $status"
exit $status
