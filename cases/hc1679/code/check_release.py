#!/usr/bin/env python3
"""Read-only, standard-library verification of the frozen HC1679 partial artifact.

No solver/model is imported or run. No network or absolute evidence path is used.
Copyright Zijian Zeng, 2026; CC BY 4.0 (third-party data retain their terms).
"""
import collections
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import string
import sys
import unicodedata

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
checks = []


def check(ok, label):
    checks.append({"check": label, "pass": bool(ok)})


def path(name):
    p = (ROOT / name).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError("Path escaped the portable package")
    return p


def read(name):
    return path(name).read_bytes()


def load(name):
    return json.loads(read(name))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def main():
    manifest = load("MANIFEST.json")
    listed = set()
    for item in manifest["files"]:
        p = item["path"]
        listed.add(p)
        b = read(p)
        check(len(b) == item["bytes"] and digest(b) == item["sha256"],
              "manifest_whole_file:" + p)
    actual = {str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file()
              and p.name != "MANIFEST.json" and "__pycache__" not in p.parts}
    check(actual == listed, "manifest_has_no_missing_or_unlisted_payload")

    candidate = load("data/selected/candidate.json")
    cert = load("data/selected/forward_certificate.json")
    packet = load("data/selected/source_packet.json")
    side = load("data/selected/sidecar.json")
    profile = packet["conditional_compact_profile"]
    projection = packet["original_projection"]
    ledger = projection["source_evidence_packet"]
    dictionary = load("data/source/author_choice_dictionary.json")
    check(packet == side["complete_frozen_source_packet"], "sidecar_complete_packet")
    check(ledger == load("data/source/author_ledger.json"), "whole_original_ledger")
    check(projection["source_packet_canonical_sha256"] == digest(canonical(ledger)),
          "canonical_source_ledger_binding")
    check(projection["dictionary_canonical_sha256"] == digest(canonical(dictionary)),
          "canonical_source_choice_dictionary_binding")
    options = {x["dimension_id"]: {v["option_id"] for v in x["options"]}
               for x in dictionary["dimensions"]}
    choice = projection["choice_vector"]
    check(set(choice) == set(options) and all(v in options[k] for k, v in choice.items()),
          "selected_choices_are_preexisting_frozen_options")

    contours = [x for x in projection["stream"] if x["type"] == "graphic_contour"]
    emitted = [x for x in contours if x["role"] in
               ("body_contour", "body_contour_with_optional_component")]
    objects = [{"origin_atom_ids": x["occurrence_ids"],
                "source_class_id": x["class_id"],
                "source_form_id": x["selected_graphic_form"],
                "component_mark_ids": x["component_mark_ids"], "role": x["role"]}
               for x in emitted]
    excluded = [i for x in contours if x["role"] == "separator_mark"
                for i in x["occurrence_ids"]]
    check(objects == profile["emitted_source_objects"], "all_emitted_source_objects_in_order")
    check(excluded == profile["excluded_separator_occurrence_ids"], "all_separator_exclusions")
    original_ids = {x["occurrence_id"] for x in ledger["occurrences"]}
    emitted_ids = [i for x in objects for i in x["origin_atom_ids"]]
    check(len(original_ids) == 289 and len(emitted_ids) == len(set(emitted_ids)) == 276
          and len(excluded) == len(set(excluded)) == 13
          and not set(emitted_ids) & set(excluded)
          and set(emitted_ids) | set(excluded) == original_ids,
          "exact_full_source_partition_289_equals_276_plus_13")
    check(len(ledger["detached_marks"]) == 2 and
          profile["detached_roles_preserved"] == projection["detached_mark_roles"],
          "both_detached_roles_retained")
    check(len(ledger["uncertainties"]) == 5 and len(ledger["incidental_context"]) == 15
          and len(ledger["visible_gap_boundaries"]) == 46,
          "all_frozen_uncertainty_context_and_gap_records")
    check(not profile["unassigned_visible_run_packets"] and
          not profile["unassigned_bounded_body_clusters"], "selected_unassigned_packets_zero")

    classes = [x["source_class_id"] for x in objects]
    mapping = {}
    for c in classes:
        if c not in mapping:
            mapping[c] = chr(97 + len(mapping))
    carrier = "".join(mapping[c] for c in classes)
    wire = carrier.upper()
    reverse = {v: k for k, v in mapping.items()}
    check(len(objects) == 276 and len(mapping) == 22, "276_positions_22_observed_classes")
    check(side["source_class_to_carrier"] == mapping and
          side["carrier_to_source_class"] == reverse, "ordinal_adapter_bijection")
    check(read("data/selected/carrier.txt") == carrier.encode() + b"\n" and
          read("data/selected/wire.txt") == wire.encode() + b"\n", "entire_carrier_and_wire")
    key = candidate["decoder_key"]
    plain = candidate["literal_compact_folded_output"]
    check(len(key) == 26 and set(key) == set(string.ascii_lowercase), "one_global_bijective_key")
    inverse = {v: chr(65 + i) for i, v in enumerate(key)}
    decoded = "".join(key[ord(w) - 65] for w in wire)
    reciphered = "".join(inverse[c] for c in plain)
    check(decoded == plain and reciphered == wire, "global_decode_and_recipher_all_276")
    check([reverse[w.lower()] for w in reciphered] == classes, "all_276_source_class_inverse")
    check(read("data/selected/literal_unchanged.txt") == plain.encode() + b"\n", "literal_preserved_exactly")
    check(cert["decoder_key"] == key and cert["candidate_sha256"] ==
          digest(read("data/selected/candidate.json")), "candidate_certificate_binding")
    check(len(cert["occurrences"]) == 276, "occurrence_certificate_denominator")
    for i, (obj, row) in enumerate(zip(objects, cert["occurrences"])):
        check(row["index_zero_based"] == i and row["frozen_source_object"] == obj
              and row["carrier_symbol"] == carrier[i]
              and row["solver_wire_symbol"] == wire[i]
              and row["literal_proposed_folded_letter"] == plain[i],
              "selected_occurrence_identity:" + str(i + 1))
    absent = [i for i in range(26) if chr(65 + i) not in wire]
    check(len(absent) == 4 and math.factorial(len(absent)) == 24,
          "four_unidentifiable_assignments_24_equivalent_permutations")
    spans = load("data/selected/unresolved_spans.json")
    check(len(spans) == 15, "all_15_unresolved_or_nonstandard_spans")
    for i, s in enumerate(spans):
        lo, hi = s["span_1based_inclusive"]
        check(plain[lo - 1:hi] == s["literal"] and not s["repair_performed"],
              "unchanged_content_issue_span:" + str(i + 1))
    editorial = read("data/selected/editorial_accents_spacing_only.txt").decode().strip()
    folded = "".join(c for c in unicodedata.normalize("NFD", editorial.lower())
                     if unicodedata.category(c) != "Mn" and c.isalpha())
    check(folded == plain, "editorial_is_reversible_without_letter_repairs")

    conf = load("data/search/portable_config.json")
    bank = load("data/source_bank/index_original.json")
    bank_ids = {x["branch_id"] for x in bank["branches"]}
    check(len(bank_ids) == 36 and len(conf["branch_ids"]) == 19 and
          len(conf["excluded_branch_ids"]) == 17 and
          set(conf["branch_ids"]) | set(conf["excluded_branch_ids"]) == bank_ids,
          "all_36_branches_retained_19_tested_17_not_falsified")
    for b in bank_ids:
        check(load("data/source_bank/" + b + ".json")["branch_id"] == b,
              "source_branch_retained:" + b)
    receipts = load("data/search/portable_receipts.json")
    plan = [(b, r, s) for b in conf["branch_ids"] for r in ("positive", "shuffled")
            for s in conf["seeds"]]
    check(len(receipts) == len(plan) == 114 and
          [(r["branch_id"], r["role"], r["seed"]) for r in receipts] == plan,
          "exact_registered_19_by_2_by_3_run_plan")
    check(len({r["call_id"] for r in receipts}) == 114, "no_missing_or_duplicate_runs")
    returned = 0
    for r in receipts:
        wb = read(r["input_path"])
        w = wb[:-1].decode("ascii")
        check(wb.endswith(b"\n") and wb.count(b"\n") == 1
              and all("A" <= c <= "Z" for c in w), "run_wire_API:" + r["call_id"])
        check(digest(wb) == r["input_sha256"] and
              digest(read(r["stdout_path"])) == r["stdout_sha256"],
              "run_input_output_bindings:" + r["call_id"])
        check(r["returncode"] == 0 and not r["timed_out"] and not r["interrupted"]
              and r["validation_pass"], "recorded_run_success:" + r["call_id"])
        obj = load(r["stdout_path"])
        streams = [(obj["baseline_key"], obj["baseline_plaintext"]),
                   (obj["best_key"], obj["best_plaintext"])] + [
                       (x["key"], x["plaintext"]) for x in obj["restarts"]]
        check(len(obj["restarts"]) == 12 and obj["sa_proposals"] == 240000,
              "recorded_run_budget:" + r["call_id"])
        for k, t in streams:
            valid = len(k) == 26 and set(k) == set(string.ascii_lowercase)
            valid = valid and len(t) == len(w) and all(c in string.ascii_lowercase for c in t)
            if valid:
                inv = {v: chr(65 + i) for i, v in enumerate(k)}
                valid = "".join(k[ord(c) - 65] for c in w) == t and "".join(inv[c] for c in t) == w
            returned += 1
            check(valid, "retained_returned_global_identity:" + str(returned))
    check(returned == 1596, "all_1596_returned_streams_verified_without_search")
    for b in conf["branch_ids"]:
        p = load("data/source_bank/" + b + ".json")
        m = {}
        for obj in p["conditional_compact_profile"]["emitted_source_objects"]:
            c = obj["source_class_id"]
            if c not in m:
                m[c] = chr(97 + len(m))
        chars = [m[x["source_class_id"]] for x in p["conditional_compact_profile"]["emitted_source_objects"]]
        positive = "".join(chars).upper()
        random.Random(1679000 + int(b.rsplit("A", 1)[1])).shuffle(chars)
        negative = "".join(chars).upper()
        check(read("data/search/inputs/" + b + "_positive.txt") == positive.encode() + b"\n"
              and read("data/search/inputs/" + b + "_shuffled.txt") == negative.encode() + b"\n"
              and collections.Counter(positive) == collections.Counter(negative),
              "one_registered_histogram_shuffle_no_redraw:" + b)

    failures = [x["check"] for x in checks if not x["pass"]]
    result = {"root_safe": True, "case_id": "hcportal:1679",
              "status": "PASS_CONDITIONAL_REPRODUCTION_ONLY" if not failures else "FAIL",
              "checks": len(checks), "failures": failures, "positions": 276,
              "full_source_occurrences": 289, "excluded_separator_objects": 13,
              "observed_classes": 22, "unobserved_assignments": 4,
              "equivalent_unobserved_permutations": 24, "retained_source_branches": 36,
              "registered_runs": 114, "returned_streams_verified": returned,
              "unresolved_content_spans": 15, "whole_content_coherent": False,
              "new_solver_calls": 0, "new_score_calls": 0, "repairs": 0,
              "historical_solution_or_probability_claim": False}
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(json.dumps({"root_safe": True, "status": "FAIL",
                          "error_type": type(exc).__name__, "error": str(exc),
                          "new_solver_calls": 0}, indent=2))
        sys.exit(1)
