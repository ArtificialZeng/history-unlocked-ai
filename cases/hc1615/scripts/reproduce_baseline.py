#!/usr/bin/env python3
"""One declared fixed-table application to an explicitly sealed source ledger."""
import argparse
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--authorization", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--donor-key", type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve()
    auth = read(args.authorization)
    assert auth["independent_cold_source_audit_complete"] is True
    pins = auth["source_pins"]
    assert len(pins) >= 4
    for rel, expected in pins.items():
        assert sha(root / rel) == expected, rel
    donor = args.donor_key.resolve()
    assert sha(donor) == auth["donor_key_sha256"]
    values = read(donor)["unit_values"]
    assert len(values) == 22 and len(set(values.values())) == 22
    inverse = {v: k for k, v in values.items()}
    source = read(root / "data/source_v1/SOURCE_UNITS_v1.json")
    groups = read(root / "data/source_v1/SOURCE_GROUPS_v1.json")["groups"]
    rows = read(root / "data/source_v1/SOURCE_ROWS_v1.json")["rows"]
    events = read(root / "data/source_v1/SOURCE_EVENTS_v1.json")["events"]
    units = source["units"]
    assert units and len(units) == source["preferred_unit_count"]
    decoded = []
    for u in units:
        label = u["preferred_raw_unit_label"]
        val = values.get(label)
        if val is not None:
            assert inverse[val] == label
        decoded.append({"unit_id": u["unit_id"], "raw_unit_label": label,
                        "mark_attributes": u["mark_attributes"],
                        "plaintext_value": val})
    by_id = {u["unit_id"]: u for u in decoded}
    assert len(by_id) == len(decoded)
    grouped = []
    for g in groups:
        vals = [by_id[i]["plaintext_value"] for i in g["unit_ids"]]
        grouped.append({"group_id": g["group_id"], "unit_ids": g["unit_ids"],
                        "literal_base": "".join(v if v is not None else "[UNKNOWN]" for v in vals),
                        "all_units_covered": None not in vals})
    plain_rows = []
    for r in rows:
        gs = [g for g, original in zip(grouped, groups)
              if original["physical_row"] == r["physical_row"]]
        base = " ".join(g["literal_base"] for g in gs)
        with_punctuation = []
        allowed_roles = auth["punctuation_emission_roles"]
        for g in gs:
            original_group = next(x for x in groups if x["group_id"] == g["group_id"])
            pieces = []
            for ordinal, uid in enumerate(original_group["unit_ids"], 1):
                val = by_id[uid]["plaintext_value"]
                pieces.append(val if val is not None else "[UNKNOWN]")
                here = [e for e in events if e["group_id"] == g["group_id"] and
                        e["preferred_role"] in allowed_roles and
                        e["after_local_unit_ordinal"] == ordinal]
                assert len(here) <= 1
                pieces.extend(e["raw_shape"] for e in here)
            with_punctuation.append("".join(pieces))
        plain_rows.append({"row_id": r["row_id"], "unit_ids": r["unit_ids"],
                           "literal_base": base,
                           "literal_with_preferred_terminal_event": " ".join(with_punctuation)})
    cert = {"schema": "HC1615_FIXED_UNIT_CERTIFICATE_v1", "mode": auth["mode"],
            "source_pins": pins, "donor_key_sha256": auth["donor_key_sha256"],
            "key_values": values, "units": decoded, "groups": grouped,
            "rows": plain_rows, "events": events,
            "counts": {"preferred_units": len(decoded),
                       "covered_units": sum(u["plaintext_value"] is not None for u in decoded),
                       "groups": len(groups), "rows": len(rows), "events": len(events)},
            "scope": "Literal lookup under frozen preferred glyph-unit grammar; coverage is not historical confirmation."}
    args.output.mkdir(parents=True, exist_ok=True)
    out = args.output / "CONDITIONAL_CANDIDATE_v1.json"
    assert not out.exists(), "Immutable output already exists"
    out.write_text(json.dumps(cert, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output / "LITERAL_ROWS_v1.txt").write_text("\n".join(
        r["literal_with_preferred_terminal_event"] for r in plain_rows) + "\n", encoding="utf-8")
    print(json.dumps(cert["counts"]))
    print((args.output / "LITERAL_ROWS_v1.txt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
