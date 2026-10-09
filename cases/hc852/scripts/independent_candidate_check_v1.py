#!/usr/bin/env python3
"""HC852 bounded audit using only the observer's unchanged sealed codec.

The preferred literal was exposed before this audit. No root implementation is
read or imported. Certificates carry source cut identities through independently
constructed labelled matrices; finite controls are not global uniqueness proof.
"""
from datetime import datetime, timezone
import collections
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "independent_candidate_audit_v1"
CORE_HASH = "5c2d8c3bbf1f54ecf8c43583e0f7e8f875a167050ab12d7e4a393f230f095e16"


def read(relative):
    return json.loads((ROOT / relative).read_text())


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def turn_labels(board, clockwise):
    # Explicit loop transform used for source provenance, separate from the
    # reused production transpose/reverse rotation and its route API.
    n = len(board)
    transformed = [[None for _ in range(n)] for _ in range(n)]
    for old_row in range(n):
        for old_column in range(n):
            if clockwise:
                transformed[old_column][n - old_row - 1] = board[old_row][old_column]
            else:
                transformed[n - old_column - 1][old_row] = board[old_row][old_column]
    return transformed


def certify(settings, plain, typed, key):
    cuts = {cell["id"]: cell for cell in key["cells"] if cell["cut"]}
    board = [[None for _ in range(8)] for _ in range(8)]
    for identifier, cell in cuts.items():
        board[cell["row"] - 1][cell["column"] - 1] = identifier
    for _ in range(settings["start"]):
        board = turn_labels(board, True)
    certificate = []
    for turn in range(4):
        coordinates = ([(r, c) for r in range(8) for c in range(8)]
                       if settings["hole_scan"] == "row-major"
                       else [(r, c) for c in range(8) for r in range(8)])
        for r, c in coordinates:
            identifier = board[r][c]
            if identifier is None:
                continue
            source_index = r * 8 + c if settings["cipher_order"] == "row-major" else c * 8 + r
            source_record = typed["positions"][source_index]
            p_index = len(certificate)
            assert plain[p_index] == source_record["current_ascii"]
            certificate.append(dict(plaintext_position=p_index + 1, plaintext_letter=plain[p_index],
                source_position=source_index + 1, current_source_letter=source_record["current_ascii"],
                matrix_row=r + 1, matrix_column=c + 1, turn_index=turn,
                initial_physical_cell_id=identifier, typed_source_record=source_record,
                physical_cut_record=cuts[identifier]))
        board = turn_labels(board, settings["direction"] == 1)
    assert len(certificate) == 64
    assert {r["source_position"] for r in certificate} == set(range(1, 65))
    assert collections.Counter(r["initial_physical_cell_id"] for r in certificate) == collections.Counter({identifier: 4 for identifier in cuts})
    return certificate


def kwargs(settings, holes):
    return dict(side=8, holes=holes, start_quarters=settings["start"],
                direction="clockwise" if settings["direction"] == 1 else "counterclockwise",
                hole_scan=settings["hole_scan"], cipher_serialization=settings["cipher_order"])


def main():
    started = datetime.now(timezone.utc).isoformat()
    scope = read("reports/independent_candidate_audit_v1/AUDIT_SCOPE_AND_EXPOSURE_REGISTRATION_v1.json")
    module_path = ROOT / "scripts" / "independent_grille_v1.py"
    assert hashlib.sha256(module_path.read_bytes()).hexdigest() == CORE_HASH
    spec = importlib.util.spec_from_file_location("own_presealed_codec", module_path)
    codec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codec)
    typed = read("data/cold_source_v1/TYPED_CURRENT_v1.json")
    key = read("data/cold_source_v1/PHYSICAL_KEY_v1.json")
    registration = read("config/TARGET_METHOD_REGISTRATION_v1.json")
    root_rows = read("reports/registered_target_v1/ALL_32_REGISTERED_PROJECTIONS_v1.json")
    root_certificates = read("reports/registered_target_v1/ALL_32_SOURCE_POSITION_CERTIFICATES_v1.json")
    preferred = read("reports/registered_target_v1/PREFERRED_CURRENT_LAYER_LITERAL_v1.json")
    assert len(typed["positions"]) == typed["current_count"] == 64
    assert [r["position"] for r in typed["positions"]] == list(range(1, 65))
    assert typed["row_counts"] == [30, 30, 4]
    cipher = "".join(r["current_ascii"] for r in typed["positions"])
    assert cipher == typed["current_stream_ascii"] and len(cipher) == 64
    assert all(r["current_alternatives"] == [r["current_ascii"]] and r["older_value"] is None
               and r["distinct_older_layer_detected"] is False for r in typed["positions"])
    assert len(key["cells"]) == 64
    assert {(r["row"], r["column"]) for r in key["cells"]} == set(itertools.product(range(1, 9), repeat=2))
    holes = tuple(sorted((r["row"] - 1, r["column"] - 1) for r in key["cells"] if r["cut"]))
    assert len(holes) == key["cut_cells"] == 16 and key["solid_cells"] == 48
    assert codec.validate_key(8, holes) == holes
    assert preferred["plaintext_literal"] == scope["parent_supplied_preferred_literal"]
    assert preferred["settings"] == registration["preferred"]
    assert len(preferred["plaintext_literal"]) == 64
    root_by_id = {r["id"]: r for r in root_rows}
    root_cert_by_id = {r["id"]: r for r in root_certificates}
    assert len(root_by_id) == len(root_cert_by_id) == 32
    own_rows = []
    certificates = []
    for start, direction, scan, order in itertools.product(range(4), (-1, 1), ("row-major", "column-major"), ("row-major", "column-major")):
        settings = dict(start=start, direction=direction, hole_scan=scan, cipher_order=order)
        identifier = f"a{start}_d{direction}_h{scan}_c{order}"
        params = kwargs(settings, holes)
        plain = codec.decrypt(cipher, **params)
        forward = codec.encrypt(plain, **params)
        assert forward == cipher
        own = dict(id=identifier, settings=settings, plaintext_literal=plain,
                   reencrypted_literal=forward, exact_source_positions=64,
                   is_registered_preferred=settings == registration["preferred"])
        assert own == root_by_id[identifier]
        cert = certify(settings, plain, typed, key)
        assert cert == root_cert_by_id[identifier]["certificate"]
        assert settings == root_cert_by_id[identifier]["settings"]
        own_rows.append(own)
        certificates.append(dict(id=identifier, settings=settings, certificate=cert))
    assert len(own_rows) == 32 and sum(len(r["certificate"]) for r in certificates) == 2048
    assert next(r for r in own_rows if r["is_registered_preferred"]) == preferred

    fixed = preferred["plaintext_literal"]
    controls = []

    def control(identifier, settings, selected_holes, details):
        generated = codec.encrypt(fixed, **kwargs(settings, selected_holes))
        recovered = codec.decrypt(generated, **kwargs(settings, selected_holes))
        assert recovered == fixed
        matches = [i + 1 for i, (actual, expected) in enumerate(zip(generated, cipher)) if actual == expected]
        controls.append(dict(id=identifier, settings=settings, holes=selected_holes,
                             fixed_plaintext_literal=fixed, generated_ciphertext=generated,
                             exact_source_match=generated == cipher, matching_positions=matches,
                             mismatch_count=64 - len(matches), exact_own_roundtrip=True, **details))

    for row in own_rows:
        if not row["is_registered_preferred"]:
            control("convention/" + row["id"], row["settings"], holes, dict(kind="other_registered_convention"))
    orbits = codec._generic_orbits(8)
    assert len(orbits) == 16
    for orbit_index, orbit in enumerate(orbits):
        selected = [hole for hole in holes if hole[0] * 8 + hole[1] in orbit]
        assert len(selected) == 1
        original = selected[0]
        for cell in orbit:
            alternate = divmod(cell, 8)
            if alternate == original:
                continue
            neighbor = tuple(sorted(set(holes) - {original} | {alternate}))
            assert codec.validate_key(8, neighbor) == neighbor
            control(f"neighbor/orbit{orbit_index + 1}/cell{cell + 1}", registration["preferred"], neighbor,
                    dict(kind="single_orbit_valid_key_neighbor", orbit_index=orbit_index + 1,
                         removed_cut_zero_based=original, added_cut_zero_based=alternate))
    assert len(controls) == 79
    duplicate_groups = collections.defaultdict(list)
    for row in controls:
        duplicate_groups[row["generated_ciphertext"]].append(row["id"])
    duplicates = [dict(generated_ciphertext=value, control_ids=ids) for value, ids in duplicate_groups.items() if len(ids) > 1]
    save("OWN_ALL_32_PROJECTIONS_v1.json", own_rows)
    save("OWN_2048_SOURCE_POSITION_CERTIFICATES_v1.json", certificates)
    save("ALL_79_FIXED_LITERAL_FINITE_CONTROLS_v1.json", dict(controls=controls, duplicate_groups=duplicates,
         all_outcomes_retained=True, global_keyspace_uniqueness_claim=False))

    array = read("data/cold_source_v1/NOTEBOOK_ARRAY_v1.json")
    grouped = read("data/cold_source_v1/NOTEBOOK_GROUPED_COPY_v1.json")
    a_by_coord = {(r["row"], r["column"]): r for r in array["positions"]}
    column_records = [a_by_coord[(r, c)] for c in range(1, 9) for r in range(1, 9)]
    array_differences = [dict(source_position=i + 1, typed_current=expected,
         notebook_array_id=record["id"], array_preferred=record["preferred_ascii_base"],
         array_alternatives=record["alternatives"], unchanged_source_note=record["note"])
         for i, (record, expected) in enumerate(zip(column_records, cipher)) if record["preferred_ascii_base"] != expected]
    grouped_stream = "".join(r["preferred_current_ascii"] for r in grouped["current_positions"])
    save("POST_FREEZE_SECONDARY_COMPARISON_AND_HOLDS_v1.json", dict(comparison_after_both_source_freezes=True,
         grouped_current64_matches_typed=grouped_stream == cipher,
         array_preferred_column_serialization_differences=array_differences,
         variants_preserved=True, secondary_sources_not_used_to_repair_primary=True,
         cancelled_source_locations=len(grouped["cancelled_visible_glyphs"]),
         wholly_hidden_earlier_values=[r["id"] for r in grouped["current_positions"] if r["unknown_wholly_hidden_earlier_value"]],
         C11_modifier_description_issue_held=True))
    result = dict(status="PASS_CURRENT_PRIMARY_COMPONENT_WITH_SOURCE_HOLDS", started_at_utc=started,
         completed_at_utc=datetime.now(timezone.utc).isoformat(), current_source_letters=64,
         physical_cells=64, public_physical_cuts=16, own_projection_count=32, exact_full64_forwards=32,
         own_and_root_literal_agreements=32, independent_source_certificate_records=2048,
         exact_root_certificate_agreements=2048, other_convention_controls=31, single_orbit_key_neighbors=48,
         finite_exact_source_matches=[r["id"] for r in controls if r["exact_source_match"]],
         finite_duplicate_output_groups=duplicates, global_uniqueness_claim=False,
         root_implementation_read_or_imported=False, candidate_preexposed=True,
         source_or_method_seal_edits=0, unchanged_codec_sha256=CORE_HASH,
         independent_wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    save("AUDIT_RESULTS_v1.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
