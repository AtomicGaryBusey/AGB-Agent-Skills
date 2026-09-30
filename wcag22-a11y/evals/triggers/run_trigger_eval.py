#!/usr/bin/env python3
"""Trigger eval for this skill, using skill-creator's run_eval.py.

The eval set (trigger-eval.json) is in the format run_eval.py / run_loop.py
expect: [{"query": ..., "should_trigger": bool}, ...].

Why a wrapper: run_eval.py registers a temporary command named
"<skill>-skill-<uuid>" with the skill's description and counts a trigger only
when that temporary name is invoked. On this machine the real skill is also
installed in ~/.claude/skills with the SAME description, so the model can pick
the real skill instead and run_eval.py would score a false negative. This
wrapper keeps run_eval.py's CLI, aggregation and output format, and replaces
only the per-query detector so that invoking EITHER the temporary command OR
the installed skill (Skill tool, or a Read of its SKILL.md) counts as a
trigger. Which one fired is logged to stderr.

Usage (from anywhere):
  python3 evals/triggers/run_trigger_eval.py [--runs-per-query 1] [--model M] \
      [--out evals/results/<date>/triggers.json]
Runs `claude -p` once per query per run, from an empty scratch project
directory (so no repo CLAUDE.md or project skills interfere).
"""
import argparse
import glob
import json
import os
import re
import select
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent.parent


def _skill_creator_dir():
    env = os.environ.get("SKILL_CREATOR_DIR")
    if env:
        return env
    hits = sorted(glob.glob(os.path.expanduser("~/.claude/skills/synced/*/skill-creator")))
    if not hits:
        sys.exit("skill-creator not found; set SKILL_CREATOR_DIR")
    return hits[0]


sys.path.insert(0, _skill_creator_dir())
import scripts.run_eval as run_eval_mod  # noqa: E402
from scripts.utils import parse_skill_md  # noqa: E402


def run_single_query_either(query, skill_name, skill_description, timeout,
                            project_root, model=None):
    """Same protocol as run_eval.run_single_query, but the installed skill
    (name == skill_name) also counts as a trigger."""
    unique_id = uuid.uuid4().hex[:8]
    clean_name = f"{skill_name}-skill-{unique_id}"
    real_skill = re.compile(r'"skill"\s*:\s*"(?:[\w-]+:)?' + re.escape(skill_name) + r'"')
    real_read = f"/skills/{skill_name}/"
    commands_dir = Path(project_root) / ".claude" / "commands"
    command_file = commands_dir / f"{clean_name}.md"

    def fired(acc):
        if clean_name in acc:
            return "temp"
        if real_skill.search(acc) or real_read in acc:
            return "installed"
        return None

    def done(result, which):
        print(f"  [{'TRIGGER' if result else 'no'}{'/' + which if which else ''}] {query[:70]}",
              file=sys.stderr)
        return result

    try:
        commands_dir.mkdir(parents=True, exist_ok=True)
        indented = "\n  ".join(skill_description.split("\n"))
        command_file.write_text(
            f"---\ndescription: |\n  {indented}\n---\n\n# {skill_name}\n\n"
            f"This skill handles: {skill_description}\n")
        cmd = ["claude", "-p", query, "--output-format", "stream-json",
               "--verbose", "--include-partial-messages"]
        if model:
            cmd += ["--model", model]
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                cwd=project_root, env=env)
        buf, pending, acc = "", None, ""
        start = time.time()
        try:
            while time.time() - start < timeout:
                if proc.poll() is not None:
                    rest = proc.stdout.read()
                    if rest:
                        buf += rest.decode("utf-8", errors="replace")
                    break
                ready, _, _ = select.select([proc.stdout], [], [], 1.0)
                if not ready:
                    continue
                chunk = os.read(proc.stdout.fileno(), 8192)
                if not chunk:
                    break
                buf += chunk.decode("utf-8", errors="replace")
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    try:
                        ev = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if ev.get("type") == "stream_event":
                        se = ev.get("event", {})
                        t = se.get("type", "")
                        if t == "content_block_start":
                            cb = se.get("content_block", {})
                            if cb.get("type") == "tool_use":
                                if cb.get("name") in ("Skill", "Read"):
                                    pending, acc = cb.get("name"), ""
                                else:
                                    return done(False, "other-tool:" + cb.get("name", ""))
                        elif t == "content_block_delta" and pending:
                            d = se.get("delta", {})
                            if d.get("type") == "input_json_delta":
                                acc += d.get("partial_json", "")
                        elif t in ("content_block_stop", "message_stop"):
                            if pending:
                                which = fired(acc)
                                if which:
                                    return done(True, which)
                                if pending == "Skill":
                                    return done(False, "other-skill")
                                pending, acc = None, ""   # unrelated Read: keep watching
                            elif t == "message_stop":
                                return done(False, None)
                    elif ev.get("type") == "result":
                        return done(False, None)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
        return done(False, "timeout")
    finally:
        if command_file.exists():
            command_file.unlink()


run_eval_mod.run_single_query = run_single_query_either


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-set", default=str(HERE / "trigger-eval.json"))
    ap.add_argument("--runs-per-query", type=int, default=1)
    ap.add_argument("--num-workers", type=int, default=5)
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--model", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    eval_set = json.loads(Path(a.eval_set).read_text())
    if not (SKILL_ROOT / "SKILL.md").is_file():
        sys.exit(f"{SKILL_ROOT / 'SKILL.md'} does not exist yet; the trigger eval "
                 "reads the skill's name and description from it")
    name, desc, _ = parse_skill_md(SKILL_ROOT)
    with tempfile.TemporaryDirectory(prefix="trigger-eval-") as proj:
        (Path(proj) / ".claude").mkdir()
        out = run_eval_mod.run_eval(eval_set=eval_set, skill_name=name, description=desc,
                                    num_workers=a.num_workers, timeout=a.timeout,
                                    project_root=Path(proj), runs_per_query=a.runs_per_query,
                                    model=a.model)
    res = out["results"]
    tp = sum(1 for r in res if r["should_trigger"] and r["pass"])
    fn = sum(1 for r in res if r["should_trigger"] and not r["pass"])
    fp = sum(1 for r in res if not r["should_trigger"] and not r["pass"])
    tn = sum(1 for r in res if not r["should_trigger"] and r["pass"])
    out["metrics"] = {
        "tp": tp, "fn": fn, "fp": fp, "tn": tn,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "accuracy": (tp + tn) / len(res) if res else None,
        "runs_per_query": a.runs_per_query, "model": a.model or "default",
    }
    text = json.dumps(out, indent=2, ensure_ascii=False)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
