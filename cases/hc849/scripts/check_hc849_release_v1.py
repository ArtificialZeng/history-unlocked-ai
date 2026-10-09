#!/usr/bin/env python3
"""Read-only portable HC849 current-body certificate checker (pure stdlib).

Default operation never writes files, runs writing wrappers or fetches sources.
Archival photographs/crops are optional and are never necessary for PASS. An
image hash, coordinate or historical receipt is not a new pixel inspection.
Only the observer's SHA-checked presealed codec is imported as cipher logic.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import argparse
import copy
import hashlib
import importlib.util
import itertools
import json
import sys

sys.dont_write_bytecode = True
CONFIG = "reports/independent_release_checker_v1/CHECKER_EXPECTATIONS_v1.json"
CONFIG_SHA = "a9cc65a3a12067c80d6b9c5dc4e2acab6583c9373c4612714948614efdd52039"
CODEC = "scripts/independent_grille_v1.py"
CODEC_SHA = "5c2d8c3bbf1f54ecf8c43583e0f7e8f875a167050ab12d7e4a393f230f095e16"


class VerificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def confined(root, path):
    parts = PurePosixPath(path).parts
    require(parts and not PurePosixPath(path).is_absolute() and ".." not in parts,
            "unsafe retained relative path: " + path)
    candidate = root.joinpath(*parts)
    require(candidate.resolve().is_relative_to(root.resolve()), "path leaves chosen package")
    return candidate


def ident(setting):
    return (f"a{setting['start']}_d{setting['direction']}_"
            f"h{setting['hole_scan']}_c{setting['cipher_order']}")


def config_args(setting, side, holes):
    require(setting["direction"] in (-1, 1), "invalid registered direction")
    return dict(side=side, holes=holes, start_quarters=setting["start"],
                direction="clockwise" if setting["direction"] == 1 else "counterclockwise",
                hole_scan=setting["hole_scan"], cipher_serialization=setting["cipher_order"])


def prov(record):
    return {k: record[k] for k in ("crop", "crop_sha256", "native_xyxy", "parent",
            "parent_sha256", "rotation_degrees", "resampling", "role")}


def native_box(record, dimensions):
    box = record["native_xyxy"]
    require(len(box) == 4 and all(type(x) is int for x in box), "native coordinate types")
    width, height = dimensions[record["parent"]]
    require(0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height,
            "native coordinates outside retained parent dimensions")
    require(record["rotation_degrees"] == 0 and record["resampling"] == "none",
            "unexpected primary crop transformation")


def diff(actual, expected):
    return [{"source_position": i + 1, "actual": a, "expected": b}
            for i, (a, b) in enumerate(zip(actual, expected)) if a != b]


def validate(bundle, expectations, codec, generic_fixtures=True):
    typed = bundle["data/cold_source_v1/typed_current_v1.json"]
    key = bundle["data/cold_source_v1/physical_key_v1.json"]
    reg = bundle["config/TARGET_METHOD_REGISTRATION_v1.json"]
    preferred = bundle["reports/registered_target_v1/PREFERRED_CURRENT_LAYER_LITERAL_v1.json"]
    own = bundle["reports/independent_candidate_audit_v1/OWN_ALL_32_LITERAL_PROJECTIONS_v1.json"]["records"]
    root = bundle["reports/registered_target_v1/ALL_32_REGISTERED_PROJECTIONS_v1.json"]["records"]
    own_certs = bundle["reports/independent_candidate_audit_v1/OWN_2048_SOURCE_POSITION_CERTIFICATES_v1.json"]["records"]
    root_certs = bundle["reports/registered_target_v1/ALL_32_SOURCE_POSITION_CERTIFICATES_v1.json"]
    C = typed["stream_ascii"]
    P = preferred["plaintext_literal"]
    require(len(C) == typed["current_count"] == 64, "current cipher extent must remain 64")
    require(len(P) == 64, "current preferred literal extent must remain 64")
    require(typed["row_counts"] == [30, 30, 4], "current source row census")
    require(len(typed["positions"]) == 64, "typed position ledger count")
    require([o["position"] for o in typed["positions"]] == list(range(1, 65)), "typed position identity")
    require(C == "".join(o["current"] for o in typed["positions"]), "current cipher/ledger disagreement")
    for o in typed["positions"]:
        require(o["underlayer_value"] is None, "invented previous source layer at position " + str(o["position"]))
        require(o["unknown_underlayer"] == (o["position"] in (30, 60)), "unknown correction-layer census")
        require(o["current_alternatives"] == [o["current"]], "primary current singleton source reading")
        native_box(o, expectations["source_native_dimensions"])
    require(key["coarse_rows"] == key["coarse_columns"] == 8 and len(key["cells"]) == 64,
            "full physical 8 by 8 census")
    cells = {(o["row"] - 1, o["column"] - 1): o for o in key["cells"]}
    require(set(cells) == set(itertools.product(range(8), repeat=2)), "physical row/column identities")
    for (r, c), o in cells.items():
        require(o["cell_id"] == f"K{r+1}{c+1}" and type(o["cut"]) is bool, "physical cell identity/cut type")
        native_box(o, expectations["source_native_dimensions"])
    holes = tuple(sorted(cell for cell, o in cells.items() if o["cut"]))
    require(len(holes) == key["cut_cell_count"] == 16, "observed 16-cut census")
    require(sum(not o["cut"] for o in cells.values()) == key["solid_cell_count"] == 48, "observed 48-solid census")
    codec.validate_key(8, holes)
    preferred_settings = reg["preferred_before_outputs"]
    require(preferred["settings"] == preferred_settings, "preferred convention changed")
    require(codec.decrypt(C, **config_args(preferred_settings, 8, holes)) == P,
            "changed preferred P or key: preferred literal no longer matches current source")
    require(codec.encrypt(P, **config_args(preferred_settings, 8, holes)) == C,
            "changed current C or key: fixed preferred forward differs")
    expected_settings = {(a, d, h, s) for a in range(4) for d in (-1, 1)
                         for h in codec.ORDERS for s in codec.ORDERS}
    settings = reg["settings"]
    require(len(settings) == 32 and {(x["start"], x["direction"], x["hole_scan"], x["cipher_order"])
            for x in settings} == expected_settings, "complete registered 32-convention set")
    own_by = {o["id"]: o for o in own}
    root_by = {o["id"]: o for o in root}
    root_cert_by = {o["id"]: o for o in root_certs}
    expected_ids = {ident(s) for s in settings}
    require(len(own) == len(root) == len(root_certs) == 32 and
            set(own_by) == set(root_by) == set(root_cert_by) == expected_ids, "projection IDs/count")
    require(len(own_certs) == 2048, "own source-certificate extent")
    own_cert_by = {(o["projection_id"], o["payload_position"]): o for o in own_certs}
    require(len(own_cert_by) == 2048, "duplicate own certificate identity")
    for setting in settings:
        pid = ident(setting)
        args = config_args(setting, 8, holes)
        literal = codec.decrypt(C, **args)
        require(codec.encrypt(literal, **args) == C, "full current forward failed")
        for records in (own_by, root_by):
            o = records[pid]
            require(o["settings"] == setting and o["plaintext_literal"] == literal and
                    o["reencrypted_literal"] == C and o["exact_source_positions"] == 64,
                    "retained literal/full forward differs: " + pid)
        route = codec.settings_route(**args)
        require(len(set(route)) == 64, "route missing or repeated physical cells")
        labels = [[cells[(r, c)]["cell_id"] if (r, c) in holes else None
                   for c in range(8)] for r in range(8)]
        for _ in range(setting["start"]):
            labels = codec._oracle_turn(labels, True)
        origins, stages = {}, {}
        for turn in range(4):
            for r in range(8):
                for c in range(8):
                    if labels[r][c] is not None:
                        require((r, c) not in origins, "duplicate rotated physical-cut witness")
                        origins[r, c], stages[r, c] = labels[r][c], turn
            labels = codec._oracle_turn(labels, setting["direction"] == 1)
        root_records = root_cert_by[pid]["certificate"]
        require(len(root_records) == 64, "root certificate extent")
        root_records_by = {o["plaintext_position"]: o for o in root_records}
        require(len(root_records_by) == 64, "duplicate root source-certificate identity")
        for i, (r, c) in enumerate(route):
            j = r * 8 + c if setting["cipher_order"] == "row-major" else c * 8 + r
            t = typed["positions"][j]
            k = next(o for o in key["cells"] if o["cell_id"] == origins[r, c])
            a = own_cert_by[pid, i + 1]
            b = root_records_by[i + 1]
            require(a["settings"] == setting and a["payload_literal"] == literal[i] == C[j] and
                    a["typed_source_position"] == j + 1 and a["projected_cell_one_based"] == [r+1,c+1] and
                    a["rotation_stage"] == stages[r,c] and a["absolute_clockwise_quarters"] ==
                    (setting["start"] + setting["direction"] * stages[r,c]) % 4,
                    "own source routing certificate differs")
            require(a["source_current_letter"] == a["forward_letter"] == t["current"] and
                    a["exact_current_match"] is True and a["typed_native_provenance"] == prov(t) and
                    a["physical_original_cut_cell"] == k["cell_id"] and
                    a["physical_cut_native_provenance"] == prov(k) and k["cut"] is True,
                    "own native current-coordinate or physical-cut provenance differs")
            require(a["unknown_prior_layer"] == t["unknown_underlayer"] and
                    a["underlayer_value"] is None and a["underlayer_policy"] == t["underlayer_policy"],
                    "own certificate invented previous source layer")
            require(b["plaintext_letter"] == literal[i] and b["source_position"] == j + 1 and
                    b["current_source_letter"] == t["current"] and b["matrix_row"] == r+1 and
                    b["matrix_column"] == c+1 and b["turn_index"] == stages[r,c] and
                    b["initial_physical_cell_id"] == k["cell_id"] and b["typed_source_record"] == t and
                    b["physical_cut_record"] == k, "root source-position/native-record certificate differs")
    array = bundle["data/cold_source_v1/notebook_array_v1.json"]
    rows = array["preferred_rows_ascii"]
    require(len(rows) == 8 and all(len(r) == 8 for r in rows), "secondary array extent")
    require("".join(rows[r][c] for c in range(8) for r in range(8)) == C, "preferred secondary column witness differs")
    grouped = bundle["data/cold_source_v1/notebook_grouped_copy_v1.json"]
    require("".join(o["current"] for o in grouped["positions"]) == C, "grouped source witness differs")
    require(all(o["earlier_value"] is None for o in grouped["positions"]), "invented grouped previous layer")
    gloss = bundle["reports/independent_candidate_audit_v1/LITERAL_SPACES_ONLY_GLOSS_v1.json"]
    require(gloss["literal"] == P and gloss["spaces_only"].replace(" ", "") == P,
            "spaces-only gloss changes letters")
    require(" DO KORE JEDEN " in gloss["spaces_only"] and P.endswith("XXX"), "literal KORE/XXX holds lost")
    controls = bundle["reports/independent_candidate_audit_v1/FIXED_LITERAL_FINITE_CONTROLS_v1.json"]
    require(controls["fixed_literal"] == P and controls["preferred_settings"] == preferred_settings,
            "finite controls changed fixed literal/preference")
    conventions = controls["alternative_conventions"]
    neighbors = controls["single_orbit_key_neighbors"]
    require(len(conventions) == 31 and len(neighbors) == 48, "finite control scope")
    require({o["id"] for o in conventions} == expected_ids - {ident(preferred_settings)}, "alternative convention IDs")
    outputs = []
    for o in conventions:
        actual = codec.encrypt(P, **config_args(o["settings"], 8, holes))
        require(o["fixed_literal"] == P and actual == o["reencrypted_literal"] and
                o["mismatches"] == diff(actual, C) and o["matches_observed_current_body"] == (actual == C),
                "retained alternative-convention outcome differs")
        outputs.append(actual)
    orbits = codec._generic_orbits(8)
    expected_neighbors = set()
    for orbit_index, orbit in enumerate(orbits):
        coordinates = [divmod(label, 8) for label in orbit]
        old = [cell for cell in coordinates if cell in holes]
        require(len(old) == 1, "physical hole-per-orbit census")
        for replacement in coordinates:
            if replacement != old[0]:
                expected_neighbors.add((orbit_index, tuple(sorted((set(holes)-{old[0]})|{replacement}))))
    observed_neighbors = set()
    for o in neighbors:
        modified = tuple(tuple(cell) for cell in o["hypothetical_holes_zero_based"])
        codec.validate_key(8, modified)
        observed_neighbors.add((o["orbit_index"], modified))
        actual = codec.encrypt(P, **config_args(preferred_settings, 8, modified))
        require(o["fixed_literal"] == P and o["settings"] == preferred_settings and
                actual == o["reencrypted_literal"] and o["mismatches"] == diff(actual, C) and
                o["matches_observed_current_body"] == (actual == C), "retained one-orbit-key outcome differs")
        outputs.append(actual)
    require(observed_neighbors == expected_neighbors, "48-neighbor scope incomplete/changed")
    require(all(o != C for o in outputs) and len(set(outputs)) == 79,
            "fixed-literal failures/duplicate claims differ")
    require(controls["convention_exact_matches"] == controls["key_neighbor_exact_matches"] == 0 and
            controls["combined_duplicate_outputs"] == [], "finite control summary differs")
    fixtures_count = 0
    fixture_block_counts = set()
    fixture_keys = set()
    if generic_fixtures:
        fixtures = bundle["reports/root_method_v1/SYNTHETIC_FIXTURES_v1.json"]
        require(len(fixtures) == 3200, "root generic fixture extent")
        for o in fixtures:
            cfg = o["config"]
            args = config_args(cfg, cfg["side"], cfg["holes"])
            require(codec.encrypt(o["plaintext"], **args) == o["ciphertext"] and
                    codec.decrypt(o["ciphertext"], **args) == o["plaintext"], "root synthetic fixture replay differs")
            fixture_keys.add((cfg["side"], tuple(tuple(x) for x in cfg["holes"])))
            fixture_block_counts.add(len(o["plaintext"]) // (cfg["side"] ** 2))
            fixtures_count += 1
        require(len(fixture_keys) == 100, "generic fixture distinct-key count")
        for o in bundle["reports/independent_method_v1/KNOWN_VECTORS_v1.json"]["vectors"]:
            args = {k:o[k] for k in ("side","holes","start_quarters","direction","hole_scan","cipher_serialization")}
            require(codec.encrypt(o["payload"], **args) == o["ciphertext"] and
                    codec.decrypt(o["ciphertext"], **args) == o["payload"], "known generic fixture replay differs")
    return {"current_letters":64,"physical_cells":64,"physical_cuts":16,"conventions":32,
            "own_source_certificates":2048,"root_source_certificates":2048,
            "bounded_fixed_literal_controls":79,"root_synthetic_fixtures":fixtures_count,
            "root_fixture_distinct_keys":len(fixture_keys),"root_fixture_block_counts":sorted(fixture_block_counts)}


def integrity_tests(bundle, expectations, codec):
    outcomes = []
    mutations = ("changed preferred P", "changed current C", "changed native current coordinate",
                 "changed physical cut with valid orbit coverage", "invented previous source layer")
    for label in mutations:
        candidate = copy.deepcopy(bundle)
        if label == mutations[0]:
            o = candidate["reports/registered_target_v1/PREFERRED_CURRENT_LAYER_LITERAL_v1.json"]
            o["plaintext_literal"] = "X" + o["plaintext_literal"][1:]
        elif label == mutations[1]:
            o = candidate["data/cold_source_v1/typed_current_v1.json"]
            o["stream_ascii"] = "X" + o["stream_ascii"][1:]
            o["positions"][0]["current"] = "X"
            o["positions"][0]["current_alternatives"] = ["X"]
        elif label == mutations[2]:
            o = candidate["data/cold_source_v1/typed_current_v1.json"]["positions"][0]
            o["native_xyxy"][0] += 1
            o["native_xyxy"][2] += 1
        elif label == mutations[3]:
            key = candidate["data/cold_source_v1/physical_key_v1.json"]
            cells = {(o["row"]-1,o["column"]-1):o for o in key["cells"]}
            holes = {cell for cell,o in cells.items() if o["cut"]}
            orbit = [divmod(x,8) for x in codec._generic_orbits(8)[0]]
            old = next(x for x in orbit if x in holes)
            new = next(x for x in orbit if x not in holes)
            cells[old]["cut"], cells[new]["cut"] = False, True
            codec.validate_key(8, (holes-{old})|{new})
        else:
            candidate["data/cold_source_v1/typed_current_v1.json"]["positions"][29]["underlayer_value"] = "A"
        try:
            validate(candidate, expectations, codec, generic_fixtures=False)
        except (VerificationError, ValueError) as exc:
            outcomes.append({"counterfactual":label,"status":"REJECTED","reason":str(exc),
                             "mutation_scope":"deep-copied in-memory objects only"})
        else:
            raise VerificationError("integrity counterfactual incorrectly accepted: " + label)
    require(len(outcomes) == 5, "five integrity controls required")
    return outcomes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="Read-only package root; default script parent project")
    parser.add_argument("--integrity-tests", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    expected_raw = confined(root, CONFIG).read_bytes()
    require(digest(expected_raw) == CONFIG_SHA, "checker expectation snapshot hash differs")
    expectations = json.loads(expected_raw)
    bundle, baselines = {}, {}
    for record in expectations["required_artifacts"]:
        raw = confined(root, record["path"]).read_bytes()
        require(len(raw) == record["bytes"] and digest(raw) == record["sha256"],
                "required frozen artifact differs: " + record["path"])
        baselines[record["path"]] = digest(raw)
        if record["path"].endswith(".json"):
            bundle[record["path"]] = json.loads(raw)
    codec_path = confined(root, CODEC)
    require(digest(codec_path.read_bytes()) == CODEC_SHA, "own presealed codec hash differs")
    spec = importlib.util.spec_from_file_location("hc849_own_sealed_codec", codec_path)
    codec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codec)
    counts = validate(bundle, expectations, codec)
    omissions, checked = [], []
    for manifest_path in expectations["historical_manifest_paths"]:
        manifest = bundle[manifest_path]
        entries = manifest.get("files", []) + manifest.get("external_source_inputs", [])
        entries += manifest.get("artifacts", []) + manifest.get("artifact_hashes", [])
        for record in entries:
            path = record.get("path", record.get("relative_path"))
            p = confined(root, path)
            # Only own sealed cipher logic may be inspected/imported. Other
            # historic Python references remain outside this portable scope.
            if path.endswith(".py") and path != CODEC:
                omissions.append({"manifest":manifest_path,"path":path,"reason":"historical code reference outside checker scope; no code read/import"})
            elif not p.is_file():
                omissions.append({"manifest":manifest_path,"path":path,"reason":"not present in chosen package; retained hash/reference does not replace file or pixels"})
            else:
                raw = p.read_bytes()
                require(digest(raw) == record["sha256"] and len(raw) == record["bytes"],
                        "present historical artifact differs: " + path)
                checked.append({"manifest":manifest_path,"path":path,"sha256":digest(raw)})
    tests = integrity_tests(bundle, expectations, codec) if args.integrity_tests else []
    for path, before in baselines.items():
        require(digest(confined(root,path).read_bytes()) == before, "checker changed frozen file")
    require(digest(confined(root,CONFIG).read_bytes()) == CONFIG_SHA, "checker changed expectations")
    image_missing = sorted({o["path"] for o in omissions if o["path"].lower().endswith((".jpg",".png"))})
    originals = [o for o in bundle["sources/NETWORK_RECEIPTS_v1.json"] if o["kind"].startswith("original")]
    require(len(originals) == 3, "three public original source receipts required")
    output = {"status":"PASS SCOPED CURRENT-BODY READ-ONLY CHECK","checked_utc":datetime.now(timezone.utc).isoformat(),
              "required_frozen_artifacts_verified":len(baselines),"counts":counts,
              "integrity_tests":tests,"read_only_frozen_hashes_unchanged":True,
              "historical_present_reference_checks":len(checked),"historical_omissions":omissions,
              "omitted_archival_image_count":len(image_missing),
              "pixels_required_for_portable_pass":False,"new_pixel_inspection":False,
              "original_source_references":[{k:o[k] for k in ("kind","url","sha256","bytes")} for o in originals],
              "limits":["Stored native coordinates/URL/SHA do not substitute for omitted original pixels; independent native audit receipts remain historical evidence.",
                        "Current 64-body given-public-grille mechanical scope only; older layers30/60 and all secondary/nonbody/source-order holds persist.",
                        "DO KORE and terminal XXX remain literal and unassigned where noted; no JE insertion.",
                        "79 finite fixed-literal controls do not prove global4^16 uniqueness or historical operation.",
                        "No current catalogue/world solvedness, priority, unknown-key recovery or original war-dispatch claim.",
                        "This expectation snapshot is not an actual RELEASE_MANIFEST or a PDF/publication audit."],
              "network_requests":0,"files_written":0,"root_implementation_imported_or_read":False}
    print(json.dumps(output,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    try:
        main()
    except (VerificationError, ValueError, KeyError, OSError) as exc:
        print(json.dumps({"status":"FAIL","error":str(exc),"files_written":0},ensure_ascii=False),file=sys.stderr)
        raise SystemExit(1)
