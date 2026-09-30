"""Load the eval answer-key spec: shared settings plus one file per fixture.

keyspec.json            shared settings (skill, plugin, severity vocabulary,
                        tolerance, no-peek pattern, refusal prompts) and
                        `fixtures`: the list of per-fixture spec files.
specs/<fixture>.json    one seeded fixture: `fixture` (project dir, relative
                        to evals/), `answer_key`, `cases`, `defects`,
                        `decoy_defs`, optional `tolerance` and `no_peek_extra`.

load() returns the shared settings with these merged views added:
  spec["fixture_specs"]  {name: fixture spec}, in keyspec order
  spec["cases"]          {case: case dict + "fixture": name}, in order
  spec["defects"]        every fixture's defects, each + "fixture": name
  spec["decoy_defs"]     every fixture's decoys (IDs must be unique)
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load():
    spec = json.loads((HERE / "keyspec.json").read_text())
    spec["fixture_specs"], spec["cases"], spec["defects"], spec["decoy_defs"] = {}, {}, [], {}
    for rel in spec["fixtures"]:
        fx = json.loads((HERE / rel).read_text())
        name = fx["name"]
        if name in spec["fixture_specs"]:
            raise SystemExit(f"duplicate fixture name {name!r} in {rel}")
        spec["fixture_specs"][name] = fx
        for cname, c in fx["cases"].items():
            if cname in spec["cases"] or cname in spec["refusals"]:
                raise SystemExit(f"duplicate case name {cname!r} in {rel}")
            spec["cases"][cname] = dict(c, fixture=name)
        ids = {d["id"] for d in spec["defects"]} | set(spec["decoy_defs"])
        for d in fx["defects"]:
            if d["id"] in ids or d["case"] not in fx["cases"]:
                raise SystemExit(f"{rel}: defect {d['id']} is a duplicate or names an unknown case")
            spec["defects"].append(dict(d, fixture=name))
        for k, v in fx["decoy_defs"].items():
            if k in ids:
                raise SystemExit(f"{rel}: decoy id {k} is not unique across fixtures")
            spec["decoy_defs"][k] = v
        for cname, c in fx["cases"].items():
            missing = [k for k in c["decoys"] if k not in fx["decoy_defs"]]
            if missing:
                raise SystemExit(f"{rel}: case {cname} lists unknown decoys {missing}")
    return spec
