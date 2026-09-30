#!/usr/bin/env python3
"""Summarize a `claude plugin eval` run of this suite into evals/results/<date>/.

Reads the raw aggregate-result.json (written outside the repo), the key spec
(keyspec.json + specs/<fixture>.json, via spec.py) and, when the run used --keep-temp, each run's trace.jsonl. Writes, with
machine paths scrubbed:
  plugin-eval/aggregate-result.json   scrubbed copy of the raw result
  plugin-eval/summary.json            per-case metrics, overall recall per fixture
  plugin-eval/summary.md              human-readable table
  plugin-eval/replies/<case>.md       each run's final reply (for regrading)

Usage: summarize.py RAW_AGGREGATE_JSON OUT_DIR [LABEL]
"""
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spec as specmod  # noqa: E402

SPEC = specmod.load()
HOME = os.path.expanduser("~")


def scrub(text: str) -> str:
    text = re.sub(r"/private/tmp/e-[A-Za-z0-9]+/home/cwd", "<workspace>", text)
    text = re.sub(r"/private/tmp/e-[A-Za-z0-9]+", "<run-sandbox>", text)
    text = re.sub(r"/(?:private/)?tmp/claude-\d+/[^\s\"']*", "<tmp>", text)
    text = re.sub(r"/(?:private/)?var/folders/[^\s\"']*", "<tmp>", text)
    text = text.replace(str(HERE.parents[1]), "<repo>")  # the skill repo root, wherever it is cloned
    text = text.replace(str(Path(HOME) / ".claude" / "skills"), "~/.claude/skills")
    text = text.replace(HOME, "~")
    text = re.sub(r"/Users/[A-Za-z0-9._-]+", "~", text)
    return text


def last_reply(trace_path):
    last = None
    model = None
    try:
        with open(trace_path) as fh:
            for line in fh:
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if ev.get("type") == "system" and ev.get("subtype") == "init":
                    model = ev.get("model")
                if ev.get("type") == "assistant":
                    texts = [c.get("text", "") for c in ev["message"].get("content", [])
                             if isinstance(c, dict) and c.get("type") == "text"]
                    if any(t.strip() for t in texts):
                        last = "\n".join(texts)
                if ev.get("type") == "result" and ev.get("result"):
                    last = ev["result"]
    except OSError:
        return None, None
    return last, model


def main():
    raw_path, out = Path(sys.argv[1]), Path(sys.argv[2])
    raw = json.loads(raw_path.read_text())
    pe = out / (sys.argv[3] if len(sys.argv) > 3 else "plugin-eval")
    (pe / "replies").mkdir(parents=True, exist_ok=True)
    (pe / "aggregate-result.json").write_text(scrub(json.dumps(raw, indent=2)))

    defects = {d["id"]: d for d in SPEC["defects"]}
    rows, summary = [], {"costUsd": raw.get("costUsd"), "partial": raw.get("partial"),
                         "partialReason": raw.get("partialReason"), "cases": {}}
    for case in raw.get("cases", []):
        name = case["name"]
        for i, run in enumerate(case.get("arms", {}).get("with", [])):
            gs = {g["name"]: g["passed"] for g in run.get("graders", [])}
            reply, model = last_reply(run.get("tracePath") or "")
            if reply is not None:
                (pe / "replies" / f"{name}-run{i + 1}.md").write_text(scrub(reply) + "\n")
            rec = sorted(k[len("recall-"):] for k in gs if k.startswith("recall-"))
            found = [k for k in rec if gs[f"recall-{k}"]]
            sev_ok = [k for k in rec if gs.get(f"severity-{k}")]
            decoy_rx = {k[len("nodecoy-"):]: (not v) for k, v in gs.items()
                        if k.startswith("nodecoy-") and k != "nodecoy-judge"}
            m = {
                "run": i + 1,
                "fixture": SPEC["cases"].get(name, {}).get("fixture"),
                "model": model,
                "error": run.get("error"),
                "costUsd": run.get("costUsd"),
                "turns": run.get("turns"),
                "skill_used": gs.get("skill-used"),
                "skill_not_used": gs.get("skill-not-used"),
                "recall": f"{len(found)}/{len(rec)}" if rec else None,
                "missed": [k for k in rec if k not in found],
                "severity_match": f"{len(sev_ok)}/{len(rec)}" if rec else None,
                "severity_match_of_found": f"{len(sev_ok)}/{len(found)}" if found else None,
                "severity_mismatch": [k for k in found if k not in sev_ok],
                "decoy_rows_flagged_regex": [k for k, v in decoy_rx.items() if v],
                "decoy_judge_pass": gs.get("nodecoy-judge"),
                "decoy_verdicts_pass": gs.get("decoy-verdicts"),
                "no_peek": gs.get("no-peek"),
                "score": run.get("score"),
                "expected_severity": {k: defects[k]["sev"] for k in rec},
            }
            summary["cases"].setdefault(name, []).append(m)
            rows.append((name, m))

    (pe / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    lines = [f"# {SPEC['skill']} plugin eval summary", "",
             f"Total cost (agent + judge): ${summary['costUsd']:.2f}" if summary["costUsd"] is not None else "Total cost: n/a",
             f"Partial: {summary['partial']} {summary['partialReason'] or ''}", "",
             "| Case | Run | Skill used | Recall | Missed | Severity match | Mismatched | Decoy rows flagged (regex) | Decoy judge | Decoy verdicts | No peek | Cost | Turns | Error |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, m in rows:
        used = m["skill_used"] if m["skill_used"] is not None else (
            f"not used: {m['skill_not_used']}" if m["skill_not_used"] is not None else "")
        cost = f"${m['costUsd']:.2f}" if m["costUsd"] is not None else ""
        lines.append(" | ".join([
            f"| {name}", str(m["run"]), str(used), m["recall"] or "-",
            ", ".join(m["missed"]) or "-", m["severity_match"] or "-",
            ", ".join(m["severity_mismatch"]) or "-",
            ", ".join(m["decoy_rows_flagged_regex"]) or "none",
            str(m["decoy_judge_pass"]) if m["decoy_judge_pass"] is not None else "-",
            str(m["decoy_verdicts_pass"]) if m["decoy_verdicts_pass"] is not None else "-",
            str(m["no_peek"]) if m["no_peek"] is not None else "-",
            cost, str(m["turns"] or ""), scrub(m["error"] or "") or "-"]) + " |")
    # Overall recall per fixture across its audit cases (first run of each), by
    # detectability. Only fixtures whose audit cases were all run are totalled
    # (a CASE-filtered run would otherwise count unrun cases as misses).
    summary["overall_recall"] = {}
    lines.append("")
    for fx in SPEC["fixture_specs"]:
        fx_cases = {d["case"] for d in defects.values() if d["fixture"] == fx}
        ran = {n for n, runs in summary["cases"].items() if runs and runs[0]["recall"]}
        if not fx_cases & ran:
            continue
        by_det, found_all = {}, set()
        for name in fx_cases & ran:
            runs = summary["cases"][name]
            found_all |= {k for k in defects if defects[k]["case"] == name
                          and k not in runs[0]["missed"]}
        scored = {k: d for k, d in defects.items() if d["case"] in fx_cases & ran}
        for k, d in scored.items():
            t = by_det.setdefault(d.get("detectability", "?"), [0, 0])
            t[1] += 1
            t[0] += k in found_all
        partial = "" if fx_cases <= ran else f" (partial: only {', '.join(sorted(fx_cases & ran))})"
        summary["overall_recall"][fx] = {
            "found": len(found_all), "total": len(scored), "complete": fx_cases <= ran,
            "by_detectability": {k: f"{a}/{b}" for k, (a, b) in by_det.items()}}
        lines.append(f"Overall recall, {fx} (run 1): {len(found_all)}/{len(scored)} ("
                     + ", ".join(f"{k} {a}/{b}" for k, (a, b) in sorted(by_det.items())) + ")"
                     + partial)
    (pe / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (pe / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
