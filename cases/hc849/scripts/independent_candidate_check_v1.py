#!/usr/bin/env python3
"""HC849 finite current-body audit using only the observer's sealed codec.

No source correction, language scoring, or key search beyond registered fixed-
literal single-orbit controls. Root result JSON is comparison evidence only;
root implementation code is never read or imported.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/independent_candidate_audit_v1"
EXPECTED_CODEC_HASH = "5c2d8c3bbf1f54ecf8c43583e0f7e8f875a167050ab12d7e4a393f230f095e16"


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads((ROOT / path).read_text())


def write(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def provenance(record):
    keys = ("crop", "crop_sha256", "native_xyxy", "parent", "parent_sha256",
            "rotation_degrees", "resampling", "role")
    return {key: record[key] for key in keys}


def kwargs(setting, side, holes):
    return dict(side=side, holes=holes, start_quarters=setting["start"],
                direction="clockwise" if setting["direction"] == 1 else "counterclockwise",
                hole_scan=setting["hole_scan"],
                cipher_serialization=setting["cipher_order"])


def identifier(setting):
    return (f"a{setting['start']}_d{setting['direction']}_"
            f"h{setting['hole_scan']}_c{setting['cipher_order']}")


def differences(actual, expected):
    assert len(actual) == len(expected)
    return [{"source_position": i + 1, "actual": a, "expected": b}
            for i, (a, b) in enumerate(zip(actual, expected)) if a != b]


def duplicate_groups(records, field):
    grouped = {}
    for record in records:
        grouped.setdefault(record[field], []).append(record["id"])
    return [{"literal": literal, "ids": ids} for literal, ids in grouped.items()
            if len(ids) > 1]


def main():
    started = utc()
    scope = load("reports/independent_candidate_audit_v1/AUDIT_SCOPE_REGISTRATION_v1.json")
    codec_path = ROOT / "scripts/independent_grille_v1.py"
    assert sha(codec_path) == EXPECTED_CODEC_HASH == scope["codec_sha256"]
    spec = importlib.util.spec_from_file_location("observer_presealed_grille", codec_path)
    codec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codec)
    typed = load("data/cold_source_v1/typed_current_v1.json")
    physical = load("data/cold_source_v1/physical_key_v1.json")
    registration = load("config/TARGET_METHOD_REGISTRATION_v1.json")
    native = load("reports/independent_candidate_audit_v1/NATIVE_SOURCE_AUDIT_v1.json")
    assert native["typed_current_match_frozen"] and native["physical_membership_match_frozen"]
    assert native["current_body_count"] == 64
    side = physical["coarse_rows"]
    assert side == physical["coarse_columns"] == 8
    source = typed["stream_ascii"]
    assert len(source) == typed["current_count"] == 64
    assert source == "".join(record["current"] for record in typed["positions"])
    assert source == "".join(native["typed_observed_rows"])
    cells = {(o["row"] - 1, o["column"] - 1): o for o in physical["cells"]}
    holes = tuple(sorted(cell for cell, record in cells.items() if record["cut"]))
    assert len(holes) == physical["cut_cell_count"] == 16
    codec.validate_key(side, holes)
    preferred = registration["preferred_before_outputs"]
    fixed_literal = scope["pre_audit_target_exposure"]["literal_preferred_P64"]
    assert len(fixed_literal) == 64
    assert len(registration["settings"]) == 32
    assert len({identifier(x) for x in registration["settings"]}) == 32

    first_projection_utc = utc()
    projections = []
    certificates = []
    for setting in registration["settings"]:
        cfg = kwargs(setting, side, holes)
        literal = codec.decrypt(source, **cfg)
        forward = codec.encrypt(literal, **cfg)
        assert forward == source
        route = codec.settings_route(**cfg)
        assert len(route) == len(set(route)) == 64
        # Labelled matrices derive physical-cut provenance separately from the
        # production Boolean route. Rotation helper is the presealed own oracle.
        labels = [[cells[(r, c)]["cell_id"] if (r, c) in holes else None
                   for c in range(side)] for r in range(side)]
        for _ in range(setting["start"]):
            labels = codec._oracle_turn(labels, True)
        cut_origin = {}
        stages = {}
        for stage in range(4):
            for r in range(side):
                for c in range(side):
                    if labels[r][c] is not None:
                        assert (r, c) not in cut_origin
                        cut_origin[(r, c)] = labels[r][c]
                        stages[(r, c)] = stage
            labels = codec._oracle_turn(labels, setting["direction"] == 1)
        assert len(cut_origin) == 64
        pid = identifier(setting)
        projections.append({"id": pid, "settings": setting,
                            "own_codec_settings": cfg,
                            "plaintext_literal": literal,
                            "reencrypted_literal": forward,
                            "exact_source_positions": 64,
                            "is_registered_preferred": setting == preferred,
                            "source_changes": 0})
        for payload_index, (r, c) in enumerate(route):
            source_index = r * side + c if setting["cipher_order"] == "row-major" else c * side + r
            observed = typed["positions"][source_index]
            key_id = cut_origin[(r, c)]
            key_record = next(o for o in physical["cells"] if o["cell_id"] == key_id)
            assert key_record["cut"]
            assert literal[payload_index] == source[source_index] == observed["current"]
            assert forward[source_index] == observed["current"]
            certificates.append({
                "projection_id": pid, "settings": setting,
                "payload_position": payload_index + 1,
                "payload_literal": literal[payload_index],
                "projected_cell_one_based": [r + 1, c + 1],
                "rotation_stage": stages[(r, c)],
                "absolute_clockwise_quarters": (setting["start"] + setting["direction"] * stages[(r, c)]) % 4,
                "typed_source_position": source_index + 1,
                "typed_source_row": observed["row"],
                "typed_source_group": observed["group"],
                "typed_position_in_group": observed["position_in_group"],
                "source_current_letter": observed["current"],
                "forward_letter": forward[source_index],
                "exact_current_match": True,
                "current_alternatives": observed["current_alternatives"],
                "unknown_prior_layer": observed["unknown_underlayer"],
                "underlayer_value": observed["underlayer_value"],
                "underlayer_policy": observed["underlayer_policy"],
                "typed_native_provenance": provenance(observed),
                "physical_original_cut_cell": key_id,
                "physical_cut_row_column_one_based": [key_record["row"], key_record["column"]],
                "physical_form": key_record["physical_form"],
                "physical_membership_observation": key_record["membership_certainty"],
                "physical_boundary_uncertainty_px": key_record["boundary_uncertainty_px"],
                "physical_cut_native_provenance": provenance(key_record),
                "certificate_scope": "Current typed letter and photographed cut; no unknown old layer or historical-order claim.",
            })
    assert len(certificates) == 2048
    chosen = next(x for x in projections if x["is_registered_preferred"])
    assert chosen["plaintext_literal"] == fixed_literal
    own_completed = utc()
    write("OWN_ALL_32_LITERAL_PROJECTIONS_v1.json", {
        "started_utc": first_projection_utc, "completed_utc": own_completed,
        "codec_sha256": EXPECTED_CODEC_HASH, "records": projections,
        "all_32_full_64_forward_exact": True,
        "no_root_code_or_adapter_imported": True,
        "candidate_preference": "Frozen root source-registration preference; parent supplied literal known before this observer audit.",
    })
    write("OWN_2048_SOURCE_POSITION_CERTIFICATES_v1.json", {
        "derived_utc": own_completed, "record_count": len(certificates),
        "derivation": "Own presealed Boolean-mask route, independent own presealed labelled-matrix physical-cut trace, explicit row/column source serialization.",
        "records": certificates,
    })

    comparison_read_utc = utc()
    root_result = load("reports/registered_target_v1/ALL_32_REGISTERED_PROJECTIONS_v1.json")
    root_by_id = {x["id"]: x for x in root_result["records"]}
    comparisons = []
    assert set(root_by_id) == {x["id"] for x in projections}
    for own in projections:
        other = root_by_id[own["id"]]
        matches = own["plaintext_literal"] == other["plaintext_literal"]
        forwards = own["reencrypted_literal"] == other["reencrypted_literal"] == source
        assert matches and forwards
        comparisons.append({"id": own["id"], "literal_match": matches,
                            "full_64_forward_match": forwards,
                            "exact_source_positions": 64})
    write("ROOT_LITERAL_COMPARISON_v1.json", {
        "comparison_file_read_utc": comparison_read_utc,
        "own_projections_file_written_before_this_comparison_load": True,
        "prior_root_metadata_or_parent_literal_exposure": "Root result schema/timestamps and preferred literal had already been inspected, explicitly no blind candidate-audit claim.",
        "root_first_target_tool_timestamp": root_result["started_utc"],
        "root_registration_utc": registration["registered_utc"],
        "root_registered_config_sha256": root_result["registered_config_sha256"],
        "all_32_literals_match": True, "comparisons": comparisons,
        "root_code_access": False,
    })

    controls_started = utc()
    convention_controls = []
    for setting in registration["settings"]:
        if setting == preferred:
            continue
        output = codec.encrypt(fixed_literal, **kwargs(setting, side, holes))
        convention_controls.append({"id": identifier(setting), "settings": setting,
                                    "fixed_literal": fixed_literal,
                                    "reencrypted_literal": output,
                                    "matches_observed_current_body": output == source,
                                    "mismatches": differences(output, source)})
    assert len(convention_controls) == 31
    orbits = codec._generic_orbits(side)
    assert len(orbits) == 16
    key_controls = []
    for orbit_index, orbit in enumerate(orbits):
        coordinates = tuple(divmod(label, side) for label in orbit)
        occupied = [cell for cell in coordinates if cell in holes]
        assert len(occupied) == 1
        old = occupied[0]
        for replacement in coordinates:
            if replacement == old:
                continue
            modified = tuple(sorted((set(holes) - {old}) | {replacement}))
            codec.validate_key(side, modified)
            output = codec.encrypt(fixed_literal, **kwargs(preferred, side, modified))
            key_controls.append({"id": f"orbit{orbit_index:02d}_{replacement[0]+1}_{replacement[1]+1}",
                "orbit_index": orbit_index, "orbit_one_based": [[r+1,c+1] for r,c in coordinates],
                "removed_observed_cut": cells[old]["cell_id"],
                "removed_observed_cut_native_provenance": provenance(cells[old]),
                "hypothetical_added_cut": cells[replacement]["cell_id"],
                "added_cell_observed_cut": cells[replacement]["cut"],
                "added_cell_native_provenance": provenance(cells[replacement]),
                "hypothetical_holes_zero_based": modified, "valid_four_turn_coverage": True,
                "fixed_literal": fixed_literal, "settings": preferred,
                "reencrypted_literal": output,
                "matches_observed_current_body": output == source,
                "mismatches": differences(output, source),
                "source_change": "None. This is a hypothetical registered control, not a source/key revision.",
            })
    assert len(key_controls) == 48
    combined = [{"id": "convention:" + o["id"], "reencrypted_literal": o["reencrypted_literal"]}
                for o in convention_controls] + [
                {"id": "key:" + o["id"], "reencrypted_literal": o["reencrypted_literal"]}
                for o in key_controls]
    controls = {
        "started_utc": controls_started, "completed_utc": utc(),
        "fixed_literal": fixed_literal, "preferred_settings": preferred,
        "alternative_conventions": convention_controls,
        "single_orbit_key_neighbors": key_controls,
        "convention_exact_matches": sum(x["matches_observed_current_body"] for x in convention_controls),
        "key_neighbor_exact_matches": sum(x["matches_observed_current_body"] for x in key_controls),
        "convention_duplicate_outputs": duplicate_groups(convention_controls, "reencrypted_literal"),
        "key_neighbor_duplicate_outputs": duplicate_groups(key_controls, "reencrypted_literal"),
        "combined_duplicate_outputs": duplicate_groups(combined, "reencrypted_literal"),
        "scope_limit": "Fixed literal only; 31 other conventions and 48 valid one-orbit key neighbors. No global 4^16 uniqueness or historic-order proof.",
    }
    write("FIXED_LITERAL_FINITE_CONTROLS_v1.json", controls)
    glossary = "FRANCOUZSKA VLADA SE ROZHODLA ODESLAT DO KORE JEDEN INTERVENCNI PRAPOR XXX"
    assert glossary.replace(" ", "") == fixed_literal
    write("LITERAL_SPACES_ONLY_GLOSS_v1.json", {
        "literal": fixed_literal, "spaces_only": glossary,
        "exact_space_removal_matches_literal": True,
        "accent_or_punctuation_restoration": "None in the literal/gloss; any grammatical rendering is editorial.",
        "rough_semantic_reading": "The French government decided to send one intervention battalion to KORE [literal destination form held] XXX.",
        "KORE_hold": "Literal DO KORE is retained. Reading this as a reference to Korea is editorial and morphologically incomplete/uncertain; KOREJE would insert JE and is forbidden as a literal gloss.",
        "terminal_X_hold": "All three Xs retained literally; padding/filler/terminator role unassigned.",
        "scope": "Present-day rough gloss of current-body mechanical literal only, no historical war-dispatch authorship or recovered original plaintext claim.",
    })
    finished = utc()
    result = {
        "audit_started_utc": started, "first_own_target_projection_utc": first_projection_utc,
        "audit_finished_utc": finished, "status": "PASS SCOPED CURRENT-BODY MECHANICAL CERTIFICATE",
        "codec_sha256": EXPECTED_CODEC_HASH, "wrapper_sha256_at_execution": sha(Path(__file__)),
        "source_refs_hash_verified": load("reports/independent_candidate_audit_v1/SOURCE_FREEZE_REPLAY_v1.json")["references_verified"],
        "native_primary_crops_pixel_verified": len(load("reports/independent_candidate_audit_v1/NATIVE_PRIMARY_PIXEL_REPLAY_v1.json")["checks"]),
        "native_images_actually_viewed": native["total_viewed_images"],
        "current_body_count": 64, "physical_cell_count": 64, "physical_cut_count": 16,
        "own_projection_count": 32, "all_full_forward_exact": True,
        "source_position_certificates": len(certificates), "root_literals_all_match": True,
        "preferred_literal": fixed_literal,
        "alternative_convention_matches": controls["convention_exact_matches"],
        "single_orbit_key_neighbor_matches": controls["key_neighbor_exact_matches"],
        "combined_duplicate_output_groups": len(controls["combined_duplicate_outputs"]),
        "all_source_and_method_freezes_preserved": True,
        "source_or_method_revision": False,
        "chronology_limit": "Own codec/control seal predated this observer target exposure. Parent preferred literal exposed before own audit registration; root schema metadata before own projections. No fully blind/pre-output candidate audit claim.",
        "claim": "Given publicly supplied photographed stencil and explicitly registered conventions, the 64 current typed source positions have complete literal forward certificates.",
        "holds": scope["limits"],
    }
    write("AUDIT_RESULTS_v1.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
