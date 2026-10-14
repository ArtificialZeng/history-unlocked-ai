"""MIT: adversarial fixtures exercise the public retained-evidence gates."""
import json
import shutil
import tempfile
import hashlib
from pathlib import Path
from verify_retained_trial import check, InvalidEvidence, ROOT


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=True) + "\n")


def rehash(root):
    dump(root / "MODULE_SHA256.json", {"schema": "HC1527_MODULE_SHA256_v1", "files": {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*")) if p.is_file() and str(p.relative_to(root)) != "MODULE_SHA256.json"}})


def run():
    baseline = check()
    fixtures = [
        ("winner score", "calls.json", lambda j: j["calls"][0].update(score=-1)),
        ("restart maximum", "calls.json", lambda j: j["calls"][0]["restart_scores"][0].update(score=1)),
        ("first tie rule", "calls.json", lambda j: j["calls"][0].update(winner_restart=1)),
        ("maximum tie count", "calls.json", lambda j: j["calls"][0].update(maximum_score_ties=1)),
        ("shuffle seed", "calls.json", lambda j: j["calls"][1].update(shuffle_seed=2026101502)),
        ("solver seed", "calls.json", lambda j: j["calls"][1].update(seed=0)),
        ("restart count", "calls.json", lambda j: j["calls"][1]["restart_scores"].pop()),
        ("step budget", "calls.json", lambda j: j["calls"][0].update(steps=99999)),
        ("wall budget", "calls.json", lambda j: j["calls"][0].update(core_wall_seconds=61)),
        ("nonfinite score", "calls.json", lambda j: j["calls"][0].update(score=float("nan"))),
        ("forbidden extra content field", "calls.json", lambda j: j["calls"][0].update(plain="fabricated fixture")),
        ("aggregate budget", "summary.json", lambda j: j["counts"].update(nominal_iteration_budget_total=1)),
        ("plus-one rank", "summary.json", lambda j: j["scores"].update(plus_one_p=.02)),
        ("aggregate wall", "summary.json", lambda j: j["runtime"].update(aggregate_core_wall_seconds=1)),
        ("timing compliance", "summary.json", lambda j: j["cadence"].update(cadence_pass=True)),
        ("reading claim", "summary.json", lambda j: j["decision"].update(complete_reading_established=True)),
        ("auditor nested summary candidate injection", "summary.json", lambda j: j["identifiability"].update(candidate_plaintext="fabricated fixture")),
        ("auditor nested score key injection", "summary.json", lambda j: j["scores"].update(substitution_assignments="fabricated fixture")),
        ("auditor nested runtime lease injection", "summary.json", lambda j: j["runtime"].update(lease_digest="fabricated fixture")),
        ("auditor nested source-record injection", "provenance.json", lambda j: j["call_records"][0].update(candidate_plaintext="fabricated fixture")),
        ("auditor extraction-field replacement", "provenance.json", lambda j: j["call_records"][0].update(extracted_fields=["candidate_plaintext"])),
        ("auditor source-record hash unlink", "provenance.json", lambda j: j["call_records"][0].update(sha256="0" * 64)),
        ("auditor missing-span count erased", "summary.json", lambda j: j["identifiability"].update(unknown_sentinel_positions_retained=0)),
        ("auditor model position count falsified", "summary.json", lambda j: j["identifiability"].update(model_positions=1)),
        ("auditor inherited audit status altered", "summary.json", lambda j: j["inherited_independent_math_audit"].update(status="COMPLETE_DECIPHERMENT_PROVED")),
        ("auditor evidence role altered", "summary.json", lambda j: j.update(evidence_role="new historical solver execution")),
        ("auditor limitations claim replaced", "summary.json", lambda j: j.update(limitations=["complete historical reading proved"])),
        ("auditor boolean recorded exit", "calls.json", lambda j: j["calls"][0].update(exit_code=False)),
        ("auditor boolean winner restart", "calls.json", lambda j: j["calls"][0].update(winner_restart=False)),
        ("auditor noninteger shuffle seed", "calls.json", lambda j: j["calls"][1].update(shuffle_seed=2026101501.0)),
        ("auditor boolean zero rank", "summary.json", lambda j: j["scores"].update(null_ge_positive=False)),
        ("auditor nonfinite trial runtime", "summary.json", lambda j: j["runtime"].update(whole_trial_elapsed_seconds=float("inf"))),
        ("auditor boolean score", "calls.json", lambda j: j["calls"][0].update(score=False)),
        ("auditor mutable-schema call injection", ["schema.json", "calls.json"],
         lambda j: (j[0]["call_fields"].append("candidate_plaintext"),
                    j[1]["calls"][0].update(candidate_plaintext="fabricated fixture"))),
        ("auditor authorization pin injection", "provenance.json", lambda j: j["resource_pins"].update(authorization_sha256="0" * 64)),
        ("auditor source case substitution", "provenance.json", lambda j: j.update(source_case_id="hcportal:OTHER_FIXTURE")),
        ("component positive shadow score", "summary.json", lambda j: j["scores"]["positive_components"].update(score=-1.0)),
        ("component baseline shadow score", "summary.json", lambda j: j["scores"]["baseline_components"].update(score=-1.0)),
        ("component positive shadow winner", "summary.json", lambda j: j["scores"]["positive_components"].update(winner_restart=1)),
        ("component positive shadow sentinel windows", "summary.json", lambda j: j["scores"]["positive_components"].update(sentinel_containing_quadgram_windows=0)),
        ("component baseline shadow sentinel windows", "summary.json", lambda j: j["scores"]["baseline_components"].update(sentinel_containing_quadgram_windows=0)),
        ("component positive zero all denominator", "summary.json", lambda j: j["scores"]["positive_components"].update(all_quadgram_windows=0)),
        ("component baseline zero all denominator", "summary.json", lambda j: j["scores"]["baseline_components"].update(all_quadgram_windows=0)),
        ("component positive zero observed denominator", "summary.json", lambda j: j["scores"]["positive_components"].update(fully_observed_quadgram_windows=0)),
        ("component baseline zero observed denominator", "summary.json", lambda j: j["scores"]["baseline_components"].update(fully_observed_quadgram_windows=0)),
        ("arithmetic typed winner score", "calls.json", lambda j: j["calls"][0].update(score=-1.0)),
        ("arithmetic typed restart maximum", "calls.json", lambda j: j["calls"][0]["restart_scores"][0].update(score=1.0)),
        ("arithmetic typed wall budget", "calls.json", lambda j: j["calls"][0].update(core_wall_seconds=61.0)),
        ("arithmetic typed aggregate wall", "summary.json", lambda j: j["runtime"].update(aggregate_core_wall_seconds=1.0)),
    ]
    intended_gates = {
        "component positive shadow score": "positive component linkage: score",
        "component baseline shadow score": "baseline component score linkage",
        "component positive shadow winner": "positive component linkage: winner_restart",
        "component positive shadow sentinel windows": "positive window count consistency",
        "component baseline shadow sentinel windows": "baseline window count consistency",
        "component positive zero all denominator": "positive window denominators",
        "component baseline zero all denominator": "baseline window denominators",
        "component positive zero observed denominator": "positive window denominators",
        "component baseline zero observed denominator": "baseline window denominators",
        "arithmetic typed winner score": "restart maximum",
        "arithmetic typed restart maximum": "restart maximum",
        "arithmetic typed wall budget": "per-call wall budget",
        "arithmetic typed aggregate wall": "aggregate core wall",
    }
    rejected = []
    rejection_receipts = []
    for name, file, mutation in fixtures:
        with tempfile.TemporaryDirectory(prefix="hc1527-numeric-test-") as tmp:
            root = Path(tmp) / "record"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns("__pycache__"))
            files = [file] if type(file) is str else file
            data = json.loads((root / file).read_text()) if type(file) is str else [json.loads((root / f).read_text()) for f in files]
            mutation(data)
            if type(file) is str:
                dump(root / file, data)
            else:
                for filename, value in zip(files, data):
                    dump(root / filename, value)
            # Rehash semantic fixtures: rejection must come from a semantic gate.
            rehash(root)
            try:
                check(root)
            except (InvalidEvidence, ValueError, KeyError, TypeError) as error:
                reason = str(error)
                intended = intended_gates.get(name)
                if intended is not None:
                    if type(error) is not InvalidEvidence or reason != intended:
                        raise AssertionError("wrong rejection gate for " + name + ": " + type(error).__name__ + ": " + reason)
                rejection_receipts.append({"fixture": name, "exception_type": type(error).__name__,
                                           "rejection_reason": reason, "intended_gate": intended,
                                           "intended_gate_matched": None if intended is None else reason == intended})
                rejected.append(name)
            else:
                raise AssertionError("accepted tamper: " + name)
    for name in ["unrehashable byte change", "file inventory change",
                 "auditor nested manifest hidden file", "auditor hidden cache content"]:
        with tempfile.TemporaryDirectory(prefix="hc1527-numeric-test-") as tmp:
            root = Path(tmp) / "record"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns("__pycache__"))
            if name == "unrehashable byte change":
                with (root / "calls.json").open("a") as stream:
                    stream.write("\n")
            elif name == "file inventory change":
                (root / "unexpected.txt").write_text("fabricated fixture\n")
            elif name == "auditor nested manifest hidden file":
                folder = root / "fixture"
                folder.mkdir()
                (folder / "MODULE_SHA256.json").write_text('{"candidate_plaintext":"fabricated fixture"}\n')
                rehash(root)
            else:
                folder = root / "__pycache__"
                folder.mkdir()
                (folder / "candidate_plaintext.txt").write_text("fabricated fixture\n")
                rehash(root)
            try:
                check(root)
            except InvalidEvidence as error:
                rejection_receipts.append({"fixture": name, "exception_type": type(error).__name__,
                                           "rejection_reason": str(error), "intended_gate": None,
                                           "intended_gate_matched": None})
                rejected.append(name)
            else:
                raise AssertionError("accepted tamper: " + name)
    return {"status": "PASS", "baseline_public_checks": baseline["new_public_checks"],
            "semantic_tamper_fixtures_rejected": len(fixtures), "integrity_fixtures_rejected": 4,
            "original_fixtures_preserved": 18, "auditor_rehashed_mutations_rejected": 20,
            "auditor_inventory_mutations_rejected": 2,
            "focused_component_and_arithmetic_fixtures_rejected": len(intended_gates),
            "focused_intended_gate_matches": sum(x["intended_gate_matched"] is True for x in rejection_receipts),
            "total_tamper_fixtures_rejected": len(rejected), "new_solver_calls": 0,
            "rejected_gates": rejected, "rejection_receipts": rejection_receipts}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
