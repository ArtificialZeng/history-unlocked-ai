#!/usr/bin/env python3
"""Literal even-square turning grille; independent generic method only.

All public indices are zero based. Starting angles are clockwise quarter turns
from the supplied mask. Direction applies after that initial angle. Hole scan
and whole-cipher serialization are independently explicit. A string is a stream
of Unicode codepoints; this codec never cleans, pads, normalizes or filters it.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import random
from datetime import datetime, timezone


ORDERS = ("row-major", "column-major")
DIRECTIONS = ("clockwise", "counterclockwise")


def _integer(value, name):
    if type(value) is not int:
        raise ValueError(f"{name} must be an integer, excluding bool")
    return value


def _rotate(matrix, clockwise=True):
    # Production transform uses transpose and reversal, never coordinate maps.
    if clockwise:
        return [list(row) for row in zip(*matrix[::-1])]
    return [list(row) for row in zip(*matrix)][::-1]


def _scan(side, order):
    if order == "row-major":
        return [(r, c) for r in range(side) for c in range(side)]
    return [(r, c) for c in range(side) for r in range(side)]


def validate_key(side, holes):
    """Return an immutable key after exact even-square coverage validation."""
    _integer(side, "side")
    if side < 2 or side % 2:
        raise ValueError("side must be even and at least two")
    try:
        supplied = tuple(holes)
    except TypeError as exc:
        raise ValueError("holes must be an iterable of coordinate pairs") from exc
    clean = []
    for pair in supplied:
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError("each hole must be a coordinate pair")
        r, c = pair
        _integer(r, "hole row")
        _integer(c, "hole column")
        if not 0 <= r < side or not 0 <= c < side:
            raise ValueError("hole outside square")
        clean.append((r, c))
    if len(set(clean)) != len(clean):
        raise ValueError("duplicate hole")
    if len(clean) != side * side // 4:
        raise ValueError("hole count must be exactly one quarter of cells")
    mask = [[False] * side for _ in range(side)]
    for r, c in clean:
        mask[r][c] = True
    coverage = [[0] * side for _ in range(side)]
    for _ in range(4):
        for r, c in _scan(side, "row-major"):
            coverage[r][c] += int(mask[r][c])
        mask = _rotate(mask)
    if any(value != 1 for row in coverage for value in row):
        raise ValueError("four rotations must cover every cell exactly once")
    return tuple(sorted(clean))


def _settings(start_quarters, direction, hole_scan, cipher_serialization):
    _integer(start_quarters, "start_quarters")
    if not 0 <= start_quarters <= 3:
        raise ValueError("start_quarters must be 0, 1, 2 or 3")
    if direction not in DIRECTIONS:
        raise ValueError("unknown rotation direction")
    if hole_scan not in ORDERS or cipher_serialization not in ORDERS:
        raise ValueError("scan and serialization must be explicit supported orders")


def settings_route(*, side, holes, start_quarters=0, direction="clockwise",
                   hole_scan="row-major", cipher_serialization="row-major"):
    """Return the payload-visit coordinates, after validated matrix rotations."""
    key = validate_key(side, holes)
    _settings(start_quarters, direction, hole_scan, cipher_serialization)
    mask = [[False] * side for _ in range(side)]
    for r, c in key:
        mask[r][c] = True
    for _ in range(start_quarters):
        mask = _rotate(mask)
    route = []
    for _ in range(4):
        route.extend((r, c) for r, c in _scan(side, hole_scan) if mask[r][c])
        mask = _rotate(mask, clockwise=direction == "clockwise")
    return tuple(route)


def _literal_extent(value, side):
    if not isinstance(value, str):
        raise ValueError("literal input must be a string")
    if not value or len(value) % (side * side):
        raise ValueError("input must contain a positive exact number of full blocks")


def encrypt(payload, *, side, holes, start_quarters=0, direction="clockwise",
            hole_scan="row-major", cipher_serialization="row-major"):
    """Encrypt literal complete blocks; return all serialized cells unchanged."""
    route = settings_route(side=side, holes=holes, start_quarters=start_quarters,
                           direction=direction, hole_scan=hole_scan,
                           cipher_serialization=cipher_serialization)
    _literal_extent(payload, side)
    extent = side * side
    output = []
    for offset in range(0, len(payload), extent):
        grid = [[None] * side for _ in range(side)]
        for value, (r, c) in zip(payload[offset:offset + extent], route):
            if grid[r][c] is not None:
                raise AssertionError("validated route revisited a cell")
            grid[r][c] = value
        if any(value is None for row in grid for value in row):
            raise AssertionError("validated route left an unassigned cell")
        output.extend(grid[r][c] for r, c in _scan(side, cipher_serialization))
    return "".join(output)


def decrypt(ciphertext, *, side, holes, start_quarters=0, direction="clockwise",
            hole_scan="row-major", cipher_serialization="row-major"):
    """Invert complete literal blocks without filtering or implicit padding."""
    route = settings_route(side=side, holes=holes, start_quarters=start_quarters,
                           direction=direction, hole_scan=hole_scan,
                           cipher_serialization=cipher_serialization)
    _literal_extent(ciphertext, side)
    extent = side * side
    output = []
    for offset in range(0, len(ciphertext), extent):
        grid = [[None] * side for _ in range(side)]
        for value, (r, c) in zip(ciphertext[offset:offset + extent],
                                 _scan(side, cipher_serialization)):
            grid[r][c] = value
        output.extend(grid[r][c] for r, c in route)
    return "".join(output)


# The controls' oracle intentionally does not call production rotation, scan,
# route, encrypt or decrypt. It constructs matrices with explicit nested loops.
def _oracle_turn(old, clockwise):
    n = len(old)
    result = []
    for new_row in range(n):
        line = []
        for new_col in range(n):
            if clockwise:
                line.append(old[n - 1 - new_col][new_row])
            else:
                line.append(old[new_col][n - 1 - new_row])
        result.append(line)
    return result


def _oracle_cells(n, column_order):
    result = []
    for outer in range(n):
        for inner in range(n):
            result.append((inner, outer) if column_order else (outer, inner))
    return result


def _oracle_route(side, holes, start_quarters, direction, hole_scan):
    board = []
    hole_set = {tuple(pair) for pair in holes}
    for r in range(side):
        board.append([(r, c) in hole_set for c in range(side)])
    for _ in range(start_quarters):
        board = _oracle_turn(board, True)
    path = []
    for _ in range(4):
        for r, c in _oracle_cells(side, hole_scan == "column-major"):
            if board[r][c]:
                path.append((r, c))
        board = _oracle_turn(board, direction == "clockwise")
    return path


def _oracle_encrypt(payload, *, side, holes, start_quarters, direction,
                    hole_scan, cipher_serialization):
    path = _oracle_route(side, holes, start_quarters, direction, hole_scan)
    extent = side * side
    encoded = ""
    for start in range(0, len(payload), extent):
        square = [[None for _ in range(side)] for _ in range(side)]
        for i in range(extent):
            r, c = path[i]
            square[r][c] = payload[start + i]
        for r, c in _oracle_cells(side, cipher_serialization == "column-major"):
            encoded += square[r][c]
    return encoded


def _oracle_decrypt(ciphertext, *, side, holes, start_quarters, direction,
                    hole_scan, cipher_serialization):
    path = _oracle_route(side, holes, start_quarters, direction, hole_scan)
    cells = _oracle_cells(side, cipher_serialization == "column-major")
    extent = side * side
    payload = ""
    for start in range(0, len(ciphertext), extent):
        square = [[None for _ in range(side)] for _ in range(side)]
        for i in range(extent):
            r, c = cells[i]
            square[r][c] = ciphertext[start + i]
        for r, c in path:
            payload += square[r][c]
    return payload


def _generic_orbits(side):
    # Labelled-matrix construction, independent from target coordinates.
    matrix = [[r * side + c for c in range(side)] for r in range(side)]
    turns = [matrix]
    for _ in range(3):
        turns.append(_oracle_turn(turns[-1], True))
    seen = set()
    for r in range(side):
        for c in range(side):
            orbit = tuple(sorted(turn[r][c] for turn in turns))
            if len(set(orbit)) != 4:
                raise AssertionError("even square must have four-cell orbits")
            seen.add(orbit)
    return tuple(sorted(seen))


def _digest_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_json_exclusive(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def self_test(report_dir):
    started = datetime.now(timezone.utc).isoformat()
    registration_path = report_dir / "REGISTRATION_v1.json"
    vectors_path = report_dir / "KNOWN_VECTORS_v1.json"
    registration = json.loads(registration_path.read_text())
    vectors = json.loads(vectors_path.read_text())["vectors"]
    seed = registration["seed"]
    quotas = {int(n): count for n, count in registration["key_quotas"].items()}
    assert seed == 8491952
    assert quotas == {2: 4, 4: 24, 6: 24, 8: 24, 10: 24}
    assert registration["blocks"] == [1, 2, 3]
    checks = 0
    failures = []

    def check(condition, label):
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(label)
            raise AssertionError(label)

    for fixture in vectors:
        kwargs = {k: fixture[k] for k in ("side", "holes", "start_quarters",
                  "direction", "hole_scan", "cipher_serialization")}
        check(encrypt(fixture["payload"], **kwargs) == fixture["ciphertext"],
              fixture["name"] + " encode")
        check(decrypt(fixture["ciphertext"], **kwargs) == fixture["payload"],
              fixture["name"] + " decode")
        check(_oracle_encrypt(fixture["payload"], **kwargs) == fixture["ciphertext"],
              fixture["name"] + " oracle")

    key_rng = random.Random(seed)
    payload_rng = random.Random(seed + 1)
    generic_keys = []
    for side, quota in sorted(quotas.items()):
        orbits = _generic_orbits(side)
        check(len(orbits) == side * side // 4, f"orbit count side {side}")
        check(len(set(itertools.chain.from_iterable(orbits))) == side * side,
              f"orbit coverage side {side}")
        finite_space = 4 ** len(orbits)
        check(quota <= finite_space, f"finite key quota side {side}")
        keys = set()
        if side == 2:
            keys = {tuple([divmod(label, side)]) for label in orbits[0]}
        else:
            for _ in range(10000):
                labels = [key_rng.choice(orbit) for orbit in orbits]
                keys.add(tuple(sorted(divmod(label, side) for label in labels)))
                if len(keys) == quota:
                    break
        check(len(keys) == quota, f"distinct key quota side {side}")
        for key in sorted(keys):
            validate_key(side, key)
            generic_keys.append({"key_index": len(generic_keys), "side": side,
                                 "holes": key, "orbit_count": len(orbits)})
    check(len(generic_keys) == 100, "100 distinct side-key combinations")

    settings = list(itertools.product(range(4), DIRECTIONS, ORDERS, ORDERS))
    literal_pool = " ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789\t\n!?:éΩ中🧩"
    prefix = " \t\néΩ中🧩!?012AB"
    receipts = []
    representative = []
    representative_sides = set()
    for key_record in generic_keys:
        side = key_record["side"]
        holes = key_record["holes"]
        representative_key = side not in representative_sides
        representative_sides.add(side)
        for start, direction, scan, serialization in settings:
            kwargs = dict(side=side, holes=holes, start_quarters=start,
                          direction=direction, hole_scan=scan,
                          cipher_serialization=serialization)
            route = settings_route(**kwargs)
            oracle_route = _oracle_route(side, holes, start, direction, scan)
            check(route == tuple(oracle_route), "production/oracle route equality")
            check(len(route) == side * side and len(set(route)) == side * side,
                  "all cells visited once")
            for blocks in (1, 2, 3):
                extent = side * side * blocks
                payload = (prefix + "".join(payload_rng.choice(literal_pool)
                           for _ in range(extent)))[:extent]
                cipher = encrypt(payload, **kwargs)
                oracle_cipher = _oracle_encrypt(payload, **kwargs)
                check(cipher == oracle_cipher, "oracle forward equality")
                check(decrypt(cipher, **kwargs) == payload, "literal roundtrip")
                check(_oracle_decrypt(cipher, **kwargs) == payload, "oracle inverse")
                check(encrypt(decrypt(oracle_cipher, **kwargs), **kwargs) == cipher,
                      "forward replay of oracle ciphertext")
                check(len(cipher) == extent, "exact extent preserved")
                receipts.append({"trial": len(receipts), "key_index": key_record["key_index"],
                                 "side": side, "blocks": blocks, "start_quarters": start,
                                 "direction": direction, "hole_scan": scan,
                                 "cipher_serialization": serialization,
                                 "codepoint_count": extent,
                                 "payload_sha256_utf8": _digest_text(payload),
                                 "ciphertext_sha256_utf8": _digest_text(cipher)})
                if representative_key and blocks == 1:
                    representative.append({**kwargs, "payload": payload, "ciphertext": cipher})
    check(len(receipts) == 9600, "9600 synthetic trials")
    check(len(representative) == 160, "160 literal representative vectors")

    valid = dict(side=4, holes=[(0, 0), (1, 3), (2, 1), (2, 3)])
    rejected = []

    def reject(label, value="A" * 16, **changes):
        kwargs = {**valid, **changes}
        outcomes = []
        for fn in (encrypt, decrypt):
            try:
                fn(value, **kwargs)
            except ValueError as exc:
                outcomes.append({"api": fn.__name__, "error": str(exc)})
            else:
                check(False, label + " incorrectly accepted by " + fn.__name__)
        check(len(outcomes) == 2, label + " both APIs reject")
        rejected.append({"label": label, "outcomes": outcomes})

    for value in (-2, 0, 1, 3, 5, True, 4.0, "4", None):
        reject("bad side " + repr(value), side=value)
    for label, holes in [
        ("holes none", None), ("holes scalar", 7), ("pair scalar", [1]),
        ("short pair", [(0,)]), ("long pair", [(0, 0, 0)]),
        ("float coordinate", [(0.0, 0), (1, 3), (2, 1), (2, 3)]),
        ("bool coordinate", [(False, 0), (1, 3), (2, 1), (2, 3)]),
        ("negative coordinate", [(-1, 0), (1, 3), (2, 1), (2, 3)]),
        ("out of bounds", [(4, 0), (1, 3), (2, 1), (2, 3)]),
        ("duplicate", [(0, 0), (0, 0), (2, 1), (2, 3)]),
        ("too few", [(0, 0)]),
        ("too many", [(0, 0), (1, 3), (2, 1), (2, 3), (1, 1)]),
        ("overlap and missing orbit", [(0, 0), (0, 3), (2, 1), (2, 3)]),
    ]:
        reject(label, holes=holes)
    for value in (-1, 4, True, 0.5, "0", None):
        reject("bad start " + repr(value), start_quarters=value)
    for value in ("CW", "", None, True):
        reject("bad direction " + repr(value), direction=value)
    for field in ("hole_scan", "cipher_serialization"):
        for value in ("row", "", None, True):
            reject("bad " + field + " " + repr(value), **{field: value})
    for value in (None, [], b"A" * 16, "", "A", "A" * 15, "A" * 17, "A" * 31):
        reject("bad literal type/extent " + repr(value), value=value)

    whitespace_payload = " \t\nAéΩ中🧩!?01234 "
    check(len(whitespace_payload) == 16, "whitespace fixture extent")
    whitespace_cipher = encrypt(whitespace_payload, **valid)
    check(decrypt(whitespace_cipher, **valid) == whitespace_payload,
          "leading/trailing whitespace and Unicode literal preservation")
    pristine = encrypt("THETURNINGGRILLE", **valid)
    changed_cipher = "~" + pristine[1:]
    changed_payload = decrypt(changed_cipher, **valid)
    check(changed_payload != "THETURNINGGRILLE", "same-length content tamper changes decoded input")
    check(encrypt(changed_payload, **valid) == changed_cipher,
          "no authentication falsely claimed")

    finished = datetime.now(timezone.utc).isoformat()
    artifacts = {
        "SYNTHETIC_KEYS_v1.json": {"seed": seed, "quotas": quotas, "keys": generic_keys},
        "SYNTHETIC_REPRESENTATIVE_VECTORS_v1.json": {"payload_seed": seed + 1, "vectors": representative},
        "SYNTHETIC_TRIAL_RECEIPTS_v1.json": {"trials": receipts},
        "REJECTION_CONTROLS_v1.json": {"cases": rejected, "content_tamper_negative_control": {
            "mechanical_permutation_detects_content_tamper": False,
            "same_length_change_forward_replays": True}},
        "CONTROL_RESULTS_v1.json": {
            "started_utc": started, "finished_utc": finished, "status": "PASS",
            "seed": seed, "payload_seed": seed + 1, "checks": checks,
            "distinct_keys": len(generic_keys), "settings_per_key": len(settings),
            "block_counts": [1, 2, 3], "synthetic_trials": len(receipts),
            "known_vectors": len(vectors), "representative_literal_vectors": len(representative),
            "malformed_cases": len(rejected), "malformed_api_rejections": len(rejected) * 2,
            "failures": failures,
            "code_sha256_at_execution": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "registration_sha256": hashlib.sha256(registration_path.read_bytes()).hexdigest(),
            "known_vectors_sha256": hashlib.sha256(vectors_path.read_bytes()).hexdigest(),
            "target_exposure": "none; no target path opened by controls",
            "limits": registration["limits"],
        },
    }
    for name, value in artifacts.items():
        _write_json_exclusive(report_dir / name, value)
    return artifacts["CONTROL_RESULTS_v1.json"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(self_test(args.report_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
