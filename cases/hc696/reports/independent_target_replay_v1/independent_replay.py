"""Independent frozen-Python target replay; never imports the root decoder."""

import csv
import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
import portax_v1 as method


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def check_method_seal():
    checked = []
    for line in (ROOT / "reports/method_primary_work_v1/SHA256SUMS").read_text().splitlines():
        expected, relative = line.split("  ", 1)
        actual = digest(ROOT / relative)
        assert actual == expected, (relative, expected, actual)
        checked.append({"path": relative, "expected_sha256": expected,
                        "actual_sha256": actual, "unchanged": True})
    assert len(checked) == 8
    return checked


def main():
    sealed_before = check_method_seal()
    ledger_path = ROOT / "reports/independent_source_review_v1/source_ledger_v1.json"
    stream_path = ROOT / "reports/independent_source_review_v1/visible_final_stream_v1.txt"
    events_path = ROOT / "reports/independent_source_review_v1/marks_and_layer_events_v1.json"
    candidates_path = ROOT / "experiments/target_first_v1/SEARCH_RESULTS_v1.tsv"
    input_paths = [ledger_path, stream_path, events_path, candidates_path]
    input_hashes_before = {str(p.relative_to(ROOT)): digest(p) for p in input_paths}
    ledger = json.loads(ledger_path.read_text())
    events = json.loads(events_path.read_text())
    observations = ledger["occurrences"]
    assert len(observations) == 180
    assert [o["global_position"] for o in observations] == list(range(1, 181))
    assert len({o["occurrence_id"] for o in observations}) == 180
    ciphertext = "".join(o["visible_final_uppercase"] for o in observations)
    # Only one terminal file newline is a container boundary; source glyphs
    # themselves come from the ledger and are never stripped or changed.
    assert stream_path.read_text() in (ciphertext, ciphertext + "\n")
    assert len(ciphertext) == 180 and all(c in method.ALPHABET for c in ciphertext)
    assert all(o["visible_identity_status"] == "fixed_from_pixels" for o in observations)
    assert all(o["source_supported_alternative_letters"] == [] for o in observations)
    assert digest(ROOT / ledger["source"]) == ledger["source_sha256"]
    candidates = list(csv.DictReader(candidates_path.open(), delimiter="\t"))
    selected = [r for r in candidates if r["effective_key_representative"] == "OAQKEQ"]
    assert len(selected) == 1 and selected[0]["period"] == "6"
    selected = selected[0]
    key = selected["effective_key_representative"]
    slides = method.effective_key(key)
    assert slides == (7, 0, 8, 5, 2, 8)
    plain = method.decrypt(ciphertext, slides)
    assert plain == selected["plaintext"]
    forward = method.encrypt(plain, slides)
    assert forward == ciphertext
    pairs = method.packing_pairs(len(ciphertext), len(slides))
    assert len(pairs) == 90
    assert sorted(i for top, bottom, _ in pairs for i in (top, bottom)) == list(range(180))
    event_lookup = {e["event_id"]: e for e in events["events"]}
    certificate = [None] * len(observations)
    for pair_number, (top, bottom, column) in enumerate(pairs, 1):
        cipher_pair = (ord(ciphertext[top]) - 65, ord(ciphertext[bottom]) - 65)
        decoded = method.transform_pair(*cipher_pair, slides[column])
        assert decoded == (ord(plain[top]) - 65, ord(plain[bottom]) - 65)
        encoded = method.transform_pair(*decoded, slides[column])
        assert encoded == cipher_pair
        for position, role, partner in [(top, "top_A1", bottom), (bottom, "bottom_A2", top)]:
            source = observations[position]
            assert all(eid in event_lookup for eid in source["event_ids"])
            certificate[position] = {
                "source_occurrence": source,
                "cryptographic_replay": {
                    "pair_number": pair_number,
                    "block_number": top // (2 * len(slides)) + 1,
                    "role": role,
                    "key_column_one_based": column + 1,
                    "effective_slide_zero_based": slides[column],
                    "representative_key_letter": key[column],
                    "partner_occurrence_id": observations[partner]["occurrence_id"],
                    "partner_global_position": partner + 1,
                    "partner_line": observations[partner]["line"],
                    "partner_group": observations[partner]["group"],
                    "partner_position_in_group": observations[partner]["position_in_group"],
                    "partner_bbox_original_xyxy": observations[partner]["bbox_original_xyxy"],
                    "top_global_position": top + 1,
                    "bottom_global_position": bottom + 1,
                    "observed_final_letter": ciphertext[position],
                    "plain_letter": plain[position],
                    "forward_letter": forward[position],
                    "exact_forward_match": True,
                    "source_edit": "none",
                    "event_ids_preserved": source["event_ids"]
                }
            }
    assert all(row is not None for row in certificate)
    assert all(all(value is not None for value in row["cryptographic_replay"].values())
               for row in certificate)
    write("occurrence_certificate_v1.json", {
        "schema": "HC696_independent_occurrence_replay_v1",
        "source_layer": "visible_final_only",
        "method": "independently authored pretarget-frozen scripts/portax_v1.py",
        "key_representative": key, "effective_slides": slides,
        "period": 6, "source_edits": [], "occurrences": certificate})
    with (OUT / "occurrence_certificate_v1.tsv").open("w", newline="") as handle:
        fields = ["occurrence_id", "global_position", "line", "group", "position_in_group",
                  "pair_number", "key_column", "slide", "role", "partner", "observed",
                  "plain", "forward", "source_bbox", "event_ids", "typed_underlayer_status"]
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in certificate:
            s, c = row["source_occurrence"], row["cryptographic_replay"]
            writer.writerow(dict(zip(fields, [s["occurrence_id"], s["global_position"], s["line"],
                s["group"], s["position_in_group"], c["pair_number"], c["key_column_one_based"],
                c["effective_slide_zero_based"], c["role"], c["partner_occurrence_id"],
                c["observed_final_letter"], c["plain_letter"], c["forward_letter"],
                json.dumps(s["bbox_original_xyxy"]), ",".join(s["event_ids"]), s["typed_underlayer_status"]])))
    write("source_layout_and_events_preserved_v1.json", {
        "source_metadata_and_groups": {k: v for k, v in ledger.items() if k != "occurrences"},
        "source_events_complete": events})
    cipher_rows, plain_rows = [], []
    for line in range(1, 7):
        groups = [g for g in ledger["groups"] if g["line"] == line]
        assert len(groups) == 6
        assert all(g["site_count"] == 5 for g in groups)
        cipher_groups, plain_groups = [], []
        for group in groups:
            a, b = group["first_position"] - 1, group["last_position"]
            assert ciphertext[a:b] == group["visible_final"]
            assert [o["occurrence_id"] for o in observations[a:b]] == group["occurrence_ids"]
            cipher_groups.append(ciphertext[a:b]); plain_groups.append(plain[a:b])
        cipher_rows.append(" ".join(cipher_groups)); plain_rows.append(" ".join(plain_groups))
    (OUT / "replayed_cipher_at_source_layout.txt").write_text("\n".join(cipher_rows) + "\n")
    (OUT / "plaintext_at_source_layout.txt").write_text("\n".join(plain_rows) + "\n")
    (OUT / "plaintext_stream.txt").write_text(plain + "\n")
    segmented = ("MANY PATROLS HAVE SUCCESSFULLY ACCOMPLISHED THEIR MISSIONS ONLY TO LOSE PERSONNEL "
                 "BY A HASTY NOISY WITHDRAWAL X NIGHT PATROLS GO OUT STEALTHILY TAKING ALL "
                 "PRECAUTIONS BUT FORGET ALL THAT IN GETTING BACK TO SAFETY X")
    assert segmented.replace(" ", "") == plain
    spans, start = [], 1
    for word in segmented.split(" "):
        spans.append({"word": word, "first_position": start, "last_position": start + len(word) - 1})
        start += len(word)
    assert start == 181
    (OUT / "segmented_reading_spaces_only.txt").write_text(segmented + "\n")
    write("word_segmentation_audit_v1.json", {
        "operation": "insert spaces only; no deletions, substitutions, or punctuation",
        "collapse_equals_all_180_decrypted_letters": True,
        "x_positions": [i + 1 for i, c in enumerate(plain) if c == "X"],
        "word_spans": spans,
        "interpretation": {"X95": "sentence separator plausible; conditional",
                           "X180": "terminal padding plausible; conditional"}})
    held = [o for o in observations if o["typed_underlayer_identity"] is None]
    assert [o["global_position"] for o in held] == [23, 66, 80, 132, 172]
    write("typed_underlayer_hold_v1.json", {
        "status": "UNIDENTIFIED; full originally typed stream cannot be replayed",
        "independently_recovered_underlayer_letters": 0,
        "positions": held,
        "reason": "Re-encryption yields the selected visible-final layer. It cannot independently establish occluded earlier ink or correction chronology."})
    keypair_options = [method.ALPHABET[2*s:2*s + 2] for s in slides]
    equivalent = ["".join(chars) for chars in itertools.product(*keypair_options)]
    assert len(equivalent) == len(set(equivalent)) == 64
    assert all(method.effective_key(k) == slides and method.encrypt(plain, k) == ciphertext for k in equivalent)
    (OUT / "equivalent_key_spellings_64.txt").write_text("\n".join(equivalent) + "\n")
    # A roundtrip is universal, not a uniqueness proof. Falsification below
    # conditions on this exact recovered reading, never on score thresholds.
    alternatives = []
    for candidate in candidates:
        alternate_key = candidate["effective_key_representative"]
        alternate_plain = method.decrypt(ciphertext, alternate_key)
        assert alternate_plain == candidate["plaintext"]
        assert method.encrypt(alternate_plain, alternate_key) == ciphertext
        alternatives.append({"period": int(candidate["period"]), "key": alternate_key,
                             "root_plaintext_independently_reproduced": True,
                             "own_roundtrip_matches_source": True,
                             "differs_from_selected_reading": alternate_plain != plain,
                             "plaintext_position_mismatches": sum(a != b for a, b in zip(plain, alternate_plain)),
                             "fixed_reading_forward_mismatches": sum(a != b for a, b in zip(ciphertext, method.encrypt(plain, alternate_key))),
                             "plaintext_sha256": hashlib.sha256(alternate_plain.encode()).hexdigest()})
    assert sum(not r["differs_from_selected_reading"] for r in alternatives) == 1
    mutations = []
    for column in range(6):
        for slide in range(13):
            if slide == slides[column]:
                continue
            key_variant = list(slides); key_variant[column] = slide
            mismatches = [i + 1 for i, (a, b) in enumerate(zip(ciphertext, method.encrypt(plain, key_variant))) if a != b]
            assert mismatches
            mutations.append({"key_column_one_based": column + 1, "replacement_slide": slide,
                              "fixed_reading_forward_mismatch_count": len(mismatches),
                              "mismatching_positions": mismatches})
    assert len(mutations) == 72
    conditional_constraints = []
    for period in range(1, 21):
        options = [set(range(13)) for _ in range(period)]
        for top, bottom, column in method.packing_pairs(180, period):
            input_pair = (ord(plain[top]) - 65, ord(plain[bottom]) - 65)
            target_pair = (ord(ciphertext[top]) - 65, ord(ciphertext[bottom]) - 65)
            options[column] &= {s for s in range(13) if method.transform_pair(*input_pair, s) == target_pair}
        conditional_constraints.append({"period": period, "slide_options_by_column": [sorted(s) for s in options],
                                        "any_key_regenerates_this_fixed_reading": all(options)})
    assert [r["period"] for r in conditional_constraints if r["any_key_regenerates_this_fixed_reading"]] == [6]
    write("alternative_replay_audit_v1.json", {
        "retained_search_candidates_checked": len(alternatives),
        "candidate_replays": alternatives, "single_slide_mutations": mutations,
        "fixed_reading_all_period_1_to_20_constraints": conditional_constraints,
        "scope": "All 175 retained candidates and 72 one-column mutations replayed. Conditional key constraints are exhaustive only for this fixed reading and periods 1-20. Search over possible plaintexts remains nonexhaustive; every alternate decryption has an exact own-key roundtrip."})
    sealed_after = check_method_seal()
    assert sealed_before == sealed_after
    assert input_hashes_before == {str(p.relative_to(ROOT)): digest(p) for p in input_paths}
    write("method_seal_recheck_v1.json", {"before_and_after_unchanged": True, "files": sealed_after})
    write("replay_inputs_v1.json", {
        "files": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)}
                  for p in input_paths],
        "input_hashes_before_and_after_unchanged": True,
        "source_image": {"path": ledger["source"], "sha256_verified": ledger["source_sha256"]},
        "target_access_authorisation": "Parent CP040 task after source freeze and preregistered first attack",
        "decoder_imported": "scripts/portax_v1.py only; no root C++/decoder imported or read"})
    result = {"status": "PASS_VISIBLE_FINAL_EXACT_REPLAY",
              "observed_letters": 180, "accounted_positions": 180, "vertical_pairs": 90,
              "period": 6, "effective_slides": slides, "key_representative": key,
              "exact_forward_position_matches": 180, "source_edits": 0,
              "unassigned_replay_fields": 0, "exceptions_used": 0,
              "primary_method_hashes_unchanged": 8,
              "input_hashes_before_and_after_unchanged": True,
              "equivalent_key_spellings": 64, "occluded_typed_underlayers_unidentified": 5,
              "all_retained_search_candidates_independently_replayed": len(alternatives),
              "single_slide_mutations_rejected_for_fixed_reading": len(mutations),
              "fixed_reading_compatible_periods_1_to_20": [6],
              "x_positions": [95, 180],
              "plaintext_sha256": hashlib.sha256(plain.encode()).hexdigest()}
    write("independent_replay_results_v1.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
