#!/usr/bin/env python3
"""Pure-stdlib, read-only HC852 image-free scientific record checker.

Imports only the observer's byte-pinned generic codec. No audit wrapper, root
implementation, image library, network, data writes or implicit source repair.
Package expectations are a required-record subset, not a release manifest.
"""
import argparse
import collections
import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = "reports/independent_release_checker_v1/CHECKER_EXPECTATIONS_v1.json"
CONFIG_SHA = "68574a7aa0188f7cd2abce9a961f4560d7e6bcb89acbe64f50611ff6399b8d27"
CORE_SHA = "5c2d8c3bbf1f54ecf8c43583e0f7e8f875a167050ab12d7e4a393f230f095e16"
DATA = "data/cold_source_v1/"
AUDIT = "reports/independent_candidate_audit_v1/"
TARGET = "reports/registered_target_v1/"


class VerificationError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise VerificationError(reason)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_pin(relative, row):
    path = ROOT / relative
    require(path.is_file(), "missing required/available frozen file: " + relative)
    require(path.stat().st_size == row["bytes"], "frozen byte-count mismatch: " + relative)
    require(digest(path) == row["sha256"], "frozen SHA mismatch: " + relative)


def adapter(settings, holes):
    return dict(side=8, holes=holes, start_quarters=settings["start"],
                direction="clockwise" if settings["direction"] == 1 else "counterclockwise",
                hole_scan=settings["hole_scan"], cipher_serialization=settings["cipher_order"])


def carrier_turn(board, clockwise):
    result = [[None] * 8 for _ in range(8)]
    for row in range(8):
        for column in range(8):
            if clockwise:
                result[column][7 - row] = board[row][column]
            else:
                result[7 - column][row] = board[row][column]
    return result


def source_certificate(settings, plain, typed, key):
    cut_records = {r["id"]: r for r in key["cells"] if r["cut"]}
    board = [[None] * 8 for _ in range(8)]
    for identifier, record in cut_records.items():
        board[record["row"] - 1][record["column"] - 1] = identifier
    for _ in range(settings["start"]):
        board = carrier_turn(board, True)
    result = []
    for turn in range(4):
        positions = ([(r, c) for r in range(8) for c in range(8)] if settings["hole_scan"] == "row-major"
                     else [(r, c) for c in range(8) for r in range(8)])
        for r, c in positions:
            identifier = board[r][c]
            if identifier is None:
                continue
            source_index = r * 8 + c if settings["cipher_order"] == "row-major" else c * 8 + r
            record = typed["positions"][source_index]
            p_index = len(result)
            require(plain[p_index] == record["current_ascii"], "certificate letter/source mismatch")
            result.append(dict(plaintext_position=p_index + 1, plaintext_letter=plain[p_index],
                source_position=source_index + 1, current_source_letter=record["current_ascii"],
                matrix_row=r + 1, matrix_column=c + 1, turn_index=turn,
                initial_physical_cell_id=identifier, typed_source_record=record,
                physical_cut_record=cut_records[identifier]))
        board = carrier_turn(board, settings["direction"] == 1)
    require(len(result) == 64 and {r["source_position"] for r in result} == set(range(1, 65)), "certificate extent")
    require(collections.Counter(r["initial_physical_cell_id"] for r in result) ==
            collections.Counter({identifier: 4 for identifier in cut_records}), "physical origin census")
    return result


def verify_records(bundle, codec, expected):
    typed = bundle[DATA + "TYPED_CURRENT_v1.json"]
    key = bundle[DATA + "PHYSICAL_KEY_v1.json"]
    require(len(typed["positions"]) == typed["current_count"] == 64 and typed["row_counts"] == [30, 30, 4], "typed census/extent")
    require(len(key["cells"]) == key["coarse_cells"] == 64 and key["coarse_rows"] == key["coarse_columns"] == 8, "physical census")
    for actual, fixed in zip(typed["positions"], expected["typed_census"]):
        require({name: actual[name] for name in fixed} == fixed, "typed native/source census changed: " + fixed["id"])
        require(actual["older_value"] is None and actual["distinct_older_layer_detected"] is False, "invented typed older layer")
    for actual, fixed in zip(key["cells"], expected["physical_census"]):
        require({name: actual[name] for name in fixed} == fixed, "physical native/cut census changed: " + fixed["id"])
    cipher = "".join(r["current_ascii"] for r in typed["positions"])
    require(cipher == typed["current_stream_ascii"] == expected["expected_current_ciphertext"], "current ciphertext changed")
    require({(r["row"], r["column"]) for r in key["cells"]} == set(itertools.product(range(1, 9), repeat=2)), "physical coordinates")
    holes = tuple(sorted((r["row"] - 1, r["column"] - 1) for r in key["cells"] if r["cut"]))
    require(len(holes) == key["cut_cells"] == 16 and key["solid_cells"] == 48, "physical cut census")
    require(codec.validate_key(8, holes) == holes, "invalid four-turn mathematical key")

    originals = {r["path"]: r for r in bundle[DATA + "ORIGINAL_INPUT_IDENTITY_v1.json"]}
    strips = bundle[DATA + "NATIVE_ATLAS_PROVENANCE_v1.json"]["strips"]
    tiles = {}
    for strip in strips:
        for tile in strip["tiles"]:
            require(tile["id"] not in tiles, "duplicate source atlas id")
            tiles[tile["id"]] = (strip["path"], tile)
    array = bundle[DATA + "NOTEBOOK_ARRAY_v1.json"]
    grouped = bundle[DATA + "NOTEBOOK_GROUPED_COPY_v1.json"]
    units = typed["positions"] + key["cells"] + array["positions"] + grouped["current_positions"] + grouped["cancelled_visible_glyphs"]
    require(len(units) == 261 and len(tiles) == 261 and len(strips) == 33, "native provenance census")
    for record in units:
        strip, tile = tiles[record["id"]]
        require(record["parent_sha256"] == originals[record["parent"]]["sha256"], "parent identity")
        require(record["native_xyxy"] == tile["source_native_xyxy"] and record["atlas_native_tile_xyxy"] == tile["atlas_tile_xyxy"], "native/source atlas coordinates")
        require(record["atlas"] == strip and record["native_RGB_pixel_sha256"] == tile["unit_pixel_sha256"], "retained source pixel identity")
        x0, y0, x1, y1 = record["native_xyxy"]
        w, h = originals[record["parent"]]["native_dimensions"]
        require(0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h and [x1-x0, y1-y0] == record["native_dimensions"], "native rectangle extent")
        require(len(record["native_RGB_pixel_sha256"]) == len(record["native_PNG_encoding_sha256"]) == 64, "source hash extent")

    preferred = bundle[TARGET + "PREFERRED_CURRENT_LAYER_LITERAL_v1.json"]
    registration = bundle["config/TARGET_METHOD_REGISTRATION_v1.json"]
    fixed = preferred["plaintext_literal"]
    require(fixed == expected["expected_preferred_plaintext"] and len(fixed) == 64, "preferred literal changed")
    require(preferred["settings"] == registration["preferred"], "preferred convention registration")
    gloss = bundle[AUDIT + "LITERAL_SPACES_ONLY_GLOSS_AND_SEMANTIC_HOLDS_v1.json"]
    require(gloss["literal"] == fixed and gloss["strict_spaces_only_gloss"] == expected["expected_strict_spaces_only_gloss"], "literal/gloss changed")
    require(gloss["strict_spaces_only_gloss"].replace(" ", "") == fixed, "spaces-only gloss inserts letters")
    require("KOMUNISTISCHE" in fixed and "IMWESTDEUTSCHLAND" in fixed and "IMLETZTEMZEIT" in fixed, "literal anomalies repaired")
    mappings = []
    for name in [TARGET + "ALL_32_REGISTERED_PROJECTIONS_v1.json", AUDIT + "OWN_ALL_32_PROJECTIONS_v1.json",
                 TARGET + "ALL_32_SOURCE_POSITION_CERTIFICATES_v1.json", AUDIT + "OWN_2048_SOURCE_POSITION_CERTIFICATES_v1.json"]:
        rows = bundle[name]
        mapping = {r["id"]: r for r in rows}
        require(len(rows) == len(mapping) == 32, "32 unique settings required")
        mappings.append(mapping)
    root_rows, own_rows, root_certs, own_certs = mappings
    preferred_count = 0
    for start, direction, scan, order in itertools.product(range(4), (-1, 1), ("row-major", "column-major"), ("row-major", "column-major")):
        settings = dict(start=start, direction=direction, hole_scan=scan, cipher_order=order)
        identifier = f"a{start}_d{direction}_h{scan}_c{order}"
        plain = codec.decrypt(cipher, **adapter(settings, holes))
        forward = codec.encrypt(plain, **adapter(settings, holes))
        require(forward == cipher, "full64 forward mismatch")
        record = dict(id=identifier, settings=settings, plaintext_literal=plain, reencrypted_literal=forward,
                      exact_source_positions=64, is_registered_preferred=settings == registration["preferred"])
        require(record == root_rows[identifier] == own_rows[identifier], "own/root literal projection mismatch")
        certificate = source_certificate(settings, plain, typed, key)
        for mapping in (root_certs, own_certs):
            require(mapping[identifier]["settings"] == settings and mapping[identifier]["certificate"] == certificate,
                    "own/root native source certificate mismatch")
        if record["is_registered_preferred"]:
            preferred_count += 1
            require(record == preferred, "preferred reading mismatch")
    require(preferred_count == 1, "one registered preferred setting required")

    controls = bundle[AUDIT + "ALL_79_FIXED_LITERAL_FINITE_CONTROLS_v1.json"]
    rows = controls["controls"]
    require(len(rows) == 79 and len({r["id"] for r in rows}) == 79, "79 finite controls")
    remaining_settings = {identifier for identifier, row in own_rows.items() if not row["is_registered_preferred"]}
    neighbors = set()
    outputs = collections.defaultdict(list)
    for row in rows:
        selected = tuple(tuple(pair) for pair in row["holes"])
        require(codec.validate_key(8, selected) == selected, "finite control legal key")
        require(row["fixed_plaintext_literal"] == fixed, "finite control preferred literal changed")
        generated = codec.encrypt(fixed, **adapter(row["settings"], selected))
        require(codec.decrypt(generated, **adapter(row["settings"], selected)) == fixed, "finite control roundtrip")
        matches = [i+1 for i, (a, b) in enumerate(zip(generated, cipher)) if a == b]
        require(row["generated_ciphertext"] == generated and row["matching_positions"] == matches and row["mismatch_count"] == 64-len(matches), "finite outcome mismatch")
        require(row["exact_source_match"] is (generated == cipher) and row["exact_own_roundtrip"] is True, "finite outcome flags")
        require(generated != cipher, "finite competitor unexpectedly exact")
        if row["kind"] == "other_registered_convention":
            identifier = row["id"].removeprefix("convention/")
            require(identifier in remaining_settings and selected == holes and row["settings"] == own_rows[identifier]["settings"], "other-convention control domain")
            remaining_settings.remove(identifier)
        else:
            require(row["kind"] == "single_orbit_valid_key_neighbor" and row["settings"] == registration["preferred"], "neighbor convention")
            removed, added = set(holes)-set(selected), set(selected)-set(holes)
            require(len(removed) == len(added) == 1, "neighbor not single-cut change")
            require(list(removed)[0] == tuple(row["removed_cut_zero_based"]) and list(added)[0] == tuple(row["added_cut_zero_based"]), "neighbor cut provenance")
            neighbors.add(selected)
        outputs[generated].append(row["id"])
    require(not remaining_settings and len(neighbors) == 48, "finite convention/neighbor extent")
    mathematical_neighbors = set()
    for orbit in codec._generic_orbits(8):
        selected = next(h for h in holes if h[0]*8+h[1] in orbit)
        for label in orbit:
            alternate = divmod(label, 8)
            if alternate != selected:
                mathematical_neighbors.add(tuple(sorted(set(holes)-{selected}|{alternate})))
    require(neighbors == mathematical_neighbors, "all16orbits×3alternatives required")
    duplicates = [dict(generated_ciphertext=value, control_ids=ids) for value, ids in outputs.items() if len(ids)>1]
    require(duplicates == controls["duplicate_groups"] == [] and controls["global_keyspace_uniqueness_claim"] is False, "finite duplicate/global scope")

    a41 = next(r for r in array["positions"] if r["id"] == "A41")
    require(a41["preferred_ascii_base"] == "W" and a41["alternatives"] == ["W", "U"] and typed["positions"][3]["current_ascii"] == "U", "A41 source disagreement repaired")
    c11 = next(r for r in grouped["current_positions"] if r["id"] == "C11")
    require(c11["preferred_current_ascii"] == "A" and "detached dot; explicit ASCII case base I" in c11["modifiers"], "C11 held description changed")
    c31 = next(r for r in grouped["current_positions"] if r["id"] == "C31")
    require(c31["unknown_wholly_hidden_earlier_value"] is True and c31["earlier_whole_value"] is None, "C31 earlier layer invented")
    require(len(grouped["cancelled_visible_glyphs"]) == 5 and grouped["raw_visible_alphabetic_glyph_count"] == 69, "cancelled source extent")
    require("".join(r["preferred_current_ascii"] for r in grouped["current_positions"]) == cipher, "grouped current comparison")
    secondary = bundle[AUDIT + "POST_FREEZE_SECONDARY_COMPARISON_AND_HOLDS_v1.json"]
    require(secondary["grouped_current64_matches_typed"] is True and secondary["C11_modifier_description_issue_held"] is True,
            "secondary holds not retained")
    require(len(bundle[DATA + "SOURCE_MARKS_AND_EXTENT_v1.json"]["marks"]) == 29, "source nonbody mark extent")
    native = bundle[AUDIT + "INDEPENDENT_NATIVE_PIXEL_AND_VISUAL_AUDIT_v1.json"]
    require(native["native_unit_pixel_checks"] == 261 and native["actual_images_seen"] == 42 and native["manual_all128_primary_cells_agree_with_freeze"] is True, "retained native audit scope")

    fixtures = bundle["reports/root_method_v1/FOCUSED_SYNTHETIC_FIXTURES_v1.json"]
    require(len(fixtures) == 320, "root generic fixture extent")
    fixture_settings = collections.defaultdict(set)
    for fixture in fixtures:
        settings = {name: fixture[name] for name in ("start", "direction", "hole_scan", "cipher_order")}
        generic_holes = tuple(tuple(p) for p in fixture["holes"])
        require(len(fixture["plaintext"]) == len(fixture["ciphertext"]) == 64*fixture["blocks"], "generic multiple-block extent")
        require(codec.encrypt(fixture["plaintext"], **adapter(settings, generic_holes)) == fixture["ciphertext"], "root generic forward disagreement")
        require(codec.decrypt(fixture["ciphertext"], **adapter(settings, generic_holes)) == fixture["plaintext"], "root generic inverse disagreement")
        fixture_settings[fixture["generic_key_index"]].add((fixture["blocks"], *settings.values()))
    require(len(fixture_settings) == 5 and all(len(v) == 64 for v in fixture_settings.values()), "generic5keys×32settings×2blocks")
    vector = bundle["reports/independent_method_v1/REGISTRATION_v1.json"]["known_vector"]
    params = {name: vector[name] for name in ("side", "holes", "start_quarters", "direction", "hole_scan", "cipher_serialization")}
    require(vector["payload"] == "THETURNINGGRILLE" and vector["ciphertext"] == "TILUNRGHGELTENIR", "primary ACA fixture changed")
    require(codec.encrypt(vector["payload"], **params) == vector["ciphertext"] and codec.decrypt(vector["ciphertext"], **params) == vector["payload"], "primary ACA replay")
    return dict(current_letters=64, physical_cells=64, native_provenance_records=261,
                own_root_projections=32, exact64forwards=32, certificate_records=4096,
                finite_controls=79, root_generic_fixtures=320, primary_ACA_vectors=1,
                historical_order_or_global_uniqueness_proved=False)


def historical_subsets(bundle, expected):
    outcomes = []
    manifests = [("source_payload", bundle["reports/cold_source_v1/MANIFEST_v1.json"]["payload_files"]),
                 ("source_reference", bundle["reports/cold_source_v1/MANIFEST_v1.json"]["input_references"]),
                 ("own_method_artifact", bundle["reports/independent_method_v1/SEAL_MANIFEST_v1.json"]["artifacts"]),
                 ("own_audit_artifact", bundle[AUDIT + "SEAL_MANIFEST_v1.json"]["artifacts"])]
    remaps = {r["frozen_path"]: r["actual_path"] for r in (expected["historical_state_remap"], expected["historical_README_remap"])}
    require(len(manifests[0][1]) == 67 and len(manifests[1][1]) == 10, "historical source manifest extent")
    for kind, entries in manifests:
        for row in entries:
            selected = remaps.get(row["path"], row["path"])
            if (ROOT / selected).is_file():
                file_pin(selected, row)
                status = "present_hash_match"
            else:
                status = "intentionally_omitted_historical_reference"
            outcomes.append(dict(kind=kind, frozen_path=row["path"], actual_path=selected, status=status))
    seal = bundle["reports/cold_source_v1/SEAL_v1.json"]
    require(digest(ROOT / seal["manifest_path"]) == seal["manifest_sha256"], "source manifest seal")
    target_seal = bundle[TARGET + "TARGET_RESULT_SEAL_v1.json"]
    require(digest(ROOT / "config/TARGET_METHOD_REGISTRATION_v1.json") == target_seal["registration_sha256"], "target registration seal")
    for row in target_seal["artifacts"]:
        file_pin(row["path"], row)
    return outcomes


def integrity_tests(bundle, codec, expected):
    tests = []
    for name in ("changed_P", "changed_C", "changed_native_coordinate", "valid_orbit_cut_change", "invented_older_layer"):
        changed = copy.deepcopy(bundle)
        if name == "changed_P":
            record = changed[TARGET + "PREFERRED_CURRENT_LAYER_LITERAL_v1.json"]
            record["plaintext_literal"] = "X" + record["plaintext_literal"][1:]
        elif name == "changed_C":
            record = changed[DATA + "TYPED_CURRENT_v1.json"]
            record["positions"][0].update(current_ascii="X", raw_current_glyph="X", current_alternatives=["X"])
            record["current_stream_ascii"] = "X" + record["current_stream_ascii"][1:]
        elif name == "changed_native_coordinate":
            record = changed[DATA + "TYPED_CURRENT_v1.json"]["positions"][0]
            record["native_xyxy"][0] += 1
            record["native_xyxy"][2] += 1
        elif name == "valid_orbit_cut_change":
            cells = changed[DATA + "PHYSICAL_KEY_v1.json"]["cells"]
            holes = {(r["row"]-1, r["column"]-1) for r in cells if r["cut"]}
            orbit = codec._generic_orbits(8)[0]
            removed = next(h for h in holes if h[0]*8+h[1] in orbit)
            added = next(divmod(i,8) for i in orbit if divmod(i,8) != removed)
            for cell in cells:
                if (cell["row"]-1, cell["column"]-1) == removed:
                    cell.update(cut=False, physical_material="solid stencil paper")
                if (cell["row"]-1, cell["column"]-1) == added:
                    cell.update(cut=True, physical_material="absent stencil/background")
            new_holes = tuple(sorted(holes-{removed}|{added}))
            require(codec.validate_key(8,new_holes) == new_holes, "tamper control must remain a mathematically legal key")
        else:
            changed[DATA + "TYPED_CURRENT_v1.json"]["positions"][0].update(older_value="A", distinct_older_layer_detected=True)
        try:
            verify_records(changed, codec, expected)
        except VerificationError as error:
            tests.append(dict(test=name, rejected=True, reason=str(error), deep_copy_only=True))
        else:
            raise VerificationError("counterfactual accepted: " + name)
    return tests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integrity-tests", action="store_true")
    args = parser.parse_args()
    require(digest(ROOT / CONFIG_PATH) == CONFIG_SHA, "checker expectations hash changed")
    expected = json.loads((ROOT / CONFIG_PATH).read_text())
    for row in expected["required_files"]:
        file_pin(row["path"], row)
    module_path = ROOT / "scripts" / "independent_grille_v1.py"
    require(digest(module_path) == CORE_SHA, "own presealed generic codec changed")
    spec = importlib.util.spec_from_file_location("own_presealed_generic_codec", module_path)
    codec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codec)
    bundle = {row["path"]: json.loads((ROOT/row["path"]).read_text())
              for row in expected["required_files"] if row["path"].endswith(".json")}
    outcomes = historical_subsets(bundle, expected)
    checks = verify_records(bundle, codec, expected)
    tests = integrity_tests(bundle, codec, expected) if args.integrity_tests else []
    omitted = [r for r in outcomes if r["status"] == "intentionally_omitted_historical_reference"]
    print(json.dumps(dict(status="PASS_READONLY_RECORD_CHECK", required_pinned_records=len(expected["required_files"]),
        checks=checks, integrity_tests=tests, historical_subset_present=len(outcomes)-len(omitted),
        intentionally_omitted_historical_references=omitted, historical_context_remapped_to_CP000=True,
        archival_images_required=False, source_pixels_rechecked_this_run=False,
        retained_native_observer_audit_is_referenced=True, read_only=True, network_requests=0,
        root_implementation_imported=False, writing_audit_wrapper_imported=False,
        release_manifest_claim=False, source_holds=expected["holds"]), indent=2))


if __name__ == "__main__":
    try:
        main()
    except (VerificationError, KeyError, TypeError, IndexError) as error:
        print(json.dumps(dict(status="FAIL", reason=str(error))), file=sys.stderr)
        raise SystemExit(1)
