#!/usr/bin/env python3
"""Registered HC852 generic controls, with no source or target inputs.

Replay an unchanged, prior independently implemented matrix codec. Its old
broad self-test is never called here. This is explicit reuse, not a newly
independent implementation or a test of the historical HC852 source key.
"""
from __future__ import annotations

import collections
from datetime import datetime, timezone
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "independent_method_v1"
CORE = ROOT / "scripts" / "independent_grille_v1.py"
CORE_SHA256 = "5c2d8c3bbf1f54ecf8c43583e0f7e8f875a167050ab12d7e4a393f230f095e16"


def write_new(name, value):
    with (REPORT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main():
    started = datetime.now(timezone.utc).isoformat()
    registration = json.loads((REPORT / "REGISTRATION_v1.json").read_text())
    if registration["fresh_seed"] != 8521952:
        raise ValueError("unregistered seed")
    if registration["synthetic_side"] != 8 or registration["distinct_generic_keys"] != 4:
        raise ValueError("unregistered synthetic scope")
    if registration["blocks"] != [1, 2] or registration["planned_synthetic_trials"] != 256:
        raise ValueError("unregistered block scope")
    if hashlib.sha256(CORE.read_bytes()).hexdigest() != CORE_SHA256:
        raise ValueError("copied generic core hash mismatch")
    spec = importlib.util.spec_from_file_location("own_sealed_generic_grille", CORE)
    codec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codec)
    rng = random.Random(registration["fresh_seed"])
    checks = 0
    failures = []

    def check(condition, label):
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(label)
            raise AssertionError(label)

    vector = registration["known_vector"]
    kwargs_names = ("side", "holes", "start_quarters", "direction", "hole_scan", "cipher_serialization")
    vkwargs = {name: vector[name] for name in kwargs_names}
    check(codec.encrypt(vector["payload"], **vkwargs) == vector["ciphertext"], "ACA encrypt")
    check(codec.decrypt(vector["ciphertext"], **vkwargs) == vector["payload"], "ACA decrypt")
    check(codec._oracle_encrypt(vector["payload"], **vkwargs) == vector["ciphertext"], "ACA oracle encrypt")
    check(codec._oracle_decrypt(vector["ciphertext"], **vkwargs) == vector["payload"], "ACA oracle decrypt")

    orbits = codec._generic_orbits(8)
    keys = []
    seen = set()
    for draw in range(registration["key_generation_bound"]):
        key = tuple(sorted(divmod(rng.choice(orbit), 8) for orbit in orbits))
        if key not in seen:
            keys.append(key)
            seen.add(key)
        if len(keys) == registration["distinct_generic_keys"]:
            break
    check(len(keys) == 4, "bounded distinct generic key generation")
    settings = list(itertools.product(registration["start_quarters"], registration["directions"],
                                     registration["hole_scans"], registration["cipher_serializations"]))
    check(len(settings) == 32 and len(set(settings)) == 32, "exact registered convention set")
    fixtures = []
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 \nXé中\x00"
    for key_index, key in enumerate(keys):
        check(codec.validate_key(8, key) == key, f"synthetic key {key_index} legal")
        for blocks in registration["blocks"]:
            payload = "".join(rng.choice(alphabet) for _ in range(64 * blocks))
            for start, direction, scan, serialization in settings:
                kwargs = dict(side=8, holes=key, start_quarters=start, direction=direction,
                              hole_scan=scan, cipher_serialization=serialization)
                ciphertext = codec.encrypt(payload, **kwargs)
                label = f"key{key_index}/blocks{blocks}/{start}/{direction}/{scan}/{serialization}"
                check(ciphertext == codec._oracle_encrypt(payload, **kwargs), label + " oracle forward")
                check(codec.decrypt(ciphertext, **kwargs) == payload, label + " exact inverse")
                check(codec._oracle_decrypt(ciphertext, **kwargs) == payload, label + " oracle inverse")
                route = codec.settings_route(**kwargs)
                oracle_route = codec._oracle_route(8, key, start, direction, scan)
                check(route == tuple(oracle_route), label + " independently looped route")
                check(len(route) == 64 and len(set(route)) == 64, label + " generic complete route")
                check(len(ciphertext) == len(payload), label + " literal length")
                check(collections.Counter(ciphertext) == collections.Counter(payload), label + " literal multiset")
                fixtures.append(dict(key_index=key_index, blocks=blocks, payload=payload,
                                     ciphertext=ciphertext, start_quarters=start, direction=direction,
                                     hole_scan=scan, cipher_serialization=serialization))
    check(len(fixtures) == registration["planned_synthetic_trials"], "exact trial scope")

    # Literal whitespace/non-ASCII/NUL preservation is a fixed control rather
    # than an incidental property of the seeded random payloads.
    literal = ("A X\né中\x00" * 8)
    literal += " " * (64 - len(literal))
    base = dict(side=8, holes=keys[0], start_quarters=0, direction="clockwise",
                hole_scan="row-major", cipher_serialization="row-major")
    encoded = codec.encrypt(literal, **base)
    check(codec.decrypt(encoded, **base) == literal, "fixed literal preservation")
    check(collections.Counter(encoded) == collections.Counter(literal), "fixed literal no filtering")

    # The overlap key uses two distinct cells from one generic four-cell orbit,
    # leaving another orbit empty while preserving the 16-cut count.
    overlap = list(keys[0])
    first_orbit = next(orbit for orbit in orbits if overlap[0][0] * 8 + overlap[0][1] in orbit)
    another_first_orbit = next(divmod(cell, 8) for cell in first_orbit if divmod(cell, 8) != overlap[0])
    overlap[1] = another_first_orbit
    cases = [
        ("odd_side", "A" * 64, {"side": 7}),
        ("side_bool", "A" * 64, {"side": True}),
        ("duplicate_cut", "A" * 64, {"holes": list(keys[0][:-1]) + [keys[0][0]]}),
        ("missing_cut", "A" * 64, {"holes": keys[0][:-1]}),
        ("out_of_bounds_cut", "A" * 64, {"holes": list(keys[0][:-1]) + [(8, 0)]}),
        ("same_orbit_overlap", "A" * 64, {"holes": overlap}),
        ("empty_literal", "", {}),
        ("short_literal", "A" * 63, {}),
        ("nonstring_literal", ["A"] * 64, {}),
        ("bad_start", "A" * 64, {"start_quarters": 4}),
        ("bad_direction", "A" * 64, {"direction": "guess"}),
        ("bad_hole_scan", "A" * 64, {"hole_scan": "guess"}),
        ("bad_cipher_serialization", "A" * 64, {"cipher_serialization": "guess"}),
    ]
    check([case[0] for case in cases] == registration["invalid_controls"], "registered invalid set")
    invalid_results = []
    for label, value, updates in cases:
        kwargs = dict(base, **updates)
        for operation in ("encrypt", "decrypt"):
            try:
                getattr(codec, operation)(value, **kwargs)
            except ValueError as error:
                invalid_results.append(dict(control=label, operation=operation, rejected=True,
                                            exception="ValueError", reason=str(error)))
            else:
                invalid_results.append(dict(control=label, operation=operation, rejected=False))
            check(invalid_results[-1]["rejected"], label + "/" + operation + " rejects")

    write_new("SYNTHETIC_FIXTURES_v1.json", dict(seed=8521952, side=8, keys=keys, fixtures=fixtures,
                                              fixed_literal_control=dict(payload=literal, ciphertext=encoded)))
    write_new("INVALID_CONTROLS_v1.json", dict(results=invalid_results))
    result = dict(status="PASS", started_at_utc=started, completed_at_utc=datetime.now(timezone.utc).isoformat(),
                  core_sha256=CORE_SHA256, fresh_seed=8521952, known_primary_vectors=1,
                  distinct_synthetic_keys=4, settings_per_key=32, blocks=[1, 2], synthetic_trials=len(fixtures),
                  expected_invalid_rejections=len(invalid_results), assertions=checks, failures=failures,
                  target_inputs_read=0, network_requests=0, prior_broad_self_test_called=False,
                  target_historical_claim=False)
    write_new("CONTROL_RESULTS_v1.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
