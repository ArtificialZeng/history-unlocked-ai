"""No-target method controls. Writes reproducible results when run directly."""

import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import portax_v1 as portax


def run() -> dict:
    # Public facts, not target material. Whitespace/case conversion is explicit.
    published_plaintext = "THEEARLYBIRDGETSTHEWORM"
    published_ciphertext = "NIJAMPBGQCWKHQJEUIKYMPAT"
    published_key = "EASY"
    actual_ciphertext = portax.encrypt(published_plaintext, published_key, pad_odd=True)
    actual_plaintext = portax.decrypt(published_ciphertext, published_key)
    assert actual_ciphertext == published_ciphertext
    assert actual_plaintext == published_plaintext + "X"
    pair_examples = [("I", "N", "U", "JL"), ("N", "O", "U", "UA"),
                     ("N", "A", "U", "DB"), ("T", "A", "E", "NM"),
                     ("B", "G", "E", "QH")]
    pair_results = []
    for top, bottom, key, expected in pair_examples:
        actual = "".join(portax.pair_letters(top, bottom, key))
        assert actual == expected
        assert "".join(portax.pair_letters(top, bottom, chr(ord(key) + 1))) == expected
        pair_results.append({"input": top + bottom, "key_pair": key + chr(ord(key) + 1),
                             "expected": expected, "actual": actual})

    inverse_cases = 0
    same_column_cases = 0
    for slide in range(13):
        outputs = set()
        for top in range(26):
            for bottom in range(26):
                output = portax.transform_pair(top, bottom, slide)
                assert portax.transform_pair(*output, slide) == (top, bottom)
                assert output != (top, bottom)
                assert portax.PAIR_TABLE[slide][top][bottom] == output
                outputs.add(output)
                inverse_cases += 1
                top_column = top if top < 13 else (top - 13 - slide) % 13
                same_column_cases += top_column == (bottom // 2 - slide) % 13
        assert len(outputs) == 26 * 26
    keypair_cases = 0
    slide_maps = []
    for slide in range(13):
        left, right = portax.ALPHABET[2 * slide:2 * slide + 2]
        assert portax.effective_key(left) == portax.effective_key(right) == (slide,)
        slide_maps.append(tuple(portax.transform_pair(a, b, slide) for a in range(26) for b in range(26)))
        for top in range(26):
            for bottom in range(26):
                a, b = portax.ALPHABET[top], portax.ALPHABET[bottom]
                assert portax.pair_letters(a, b, left) == portax.pair_letters(a, b, right)
                keypair_cases += 1
    assert len(set(slide_maps)) == 13

    # The final published period-7 group has row lengths 7, 7, 5, 5.
    partial_text = "SHALLBEUPLIFTEDNEVERMORE"
    # The PDF contains 24 letters; its final two shorter rows contain 5 each.
    assert len(partial_text) == 24
    expected_packing = tuple([(i, i + 7, i) for i in range(7)] +
                             [(14 + i, 19 + i, i) for i in range(5)])
    assert portax.packing_pairs(24, 7) == expected_packing
    rows = [partial_text[a:b] for a, b in [(0, 7), (7, 14), (14, 19), (19, 24)]]
    assert rows == ["SHALLBE", "UPLIFTE", "DNEVE", "RMORE"]

    rng = random.Random(20261005)
    roundtrip_cases = 0
    partial_cases = 0
    synthetic_recovery_cases = 0
    for period in range(1, 21):
        for length in range(0, 4 * period + 4):
            key = tuple(rng.randrange(13) for _ in range(period))
            plain = "".join(rng.choice(portax.ALPHABET) for _ in range(length))
            cipher = portax.encrypt(plain, key, pad_odd=True)
            expected_plain = plain + ("X" if length % 2 else "")
            assert portax.decrypt(cipher, key) == expected_plain
            assert portax.encrypt(portax.decrypt(cipher, key), key) == cipher
            assert len(cipher) == length + length % 2
            pairs = portax.packing_pairs(len(cipher), period)
            assert sorted(index for a, b, _ in pairs for index in (a, b)) == list(range(len(cipher)))
            for start in range(0, len(expected_plain), 2 * period):
                block = expected_plain[start:start + 2 * period]
                assert portax.transform_block(block, key) == cipher[start:start + 2 * period]
            roundtrip_cases += 1
            partial_cases += bool(len(cipher) % (2 * period))

        # Enumerate all slides against deliberately nonlinguistic known data.
        # Every pair of letters is exposed at every key position. This proves
        # recovery of the effective slides, not a scoring or language method.
        key = tuple((3 * i + period) % 13 for i in range(period))
        known_parts = []
        for a in range(26):
            for b in range(26):
                known_parts.append(portax.ALPHABET[a] * period + portax.ALPHABET[b] * period)
        plain = "".join(known_parts)
        cipher = portax.encrypt(plain, key)
        possible = [set(range(13)) for _ in key]
        for a, b, column in portax.packing_pairs(len(plain), period):
            top, bottom = ord(plain[a]) - 65, ord(plain[b]) - 65
            cipher_pair = (ord(cipher[a]) - 65, ord(cipher[b]) - 65)
            possible[column] &= {slide for slide in range(13)
                                 if portax.transform_pair(top, bottom, slide) == cipher_pair}
        assert possible == [{slide} for slide in key]
        synthetic_recovery_cases += 1

    rejected = []
    for name, call in [
        ("unknown_input", lambda: portax.decrypt("A?", "AB")),
        ("lowercase_input", lambda: portax.decrypt("ab", "AB")),
        ("whitespace_input", lambda: portax.decrypt("A B", "AB")),
        ("odd_ciphertext", lambda: portax.decrypt("ABC", "AB")),
        ("undeclared_plaintext_padding", lambda: portax.encrypt("ABC", "AB")),
        ("empty_key", lambda: portax.encrypt("AB", "")),
        ("invalid_slide", lambda: portax.transform_pair(0, 0, 13)),
        ("invalid_letter", lambda: portax.transform_pair(26, 0, 0)),
        ("oversize_block", lambda: portax.transform_block("ABCD", "A")),
    ]:
        try:
            call()
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError(f"did not reject {name}")

    return {
        "status": "PASS",
        "scope": "Primary method and synthetic controls only; no target files read",
        "source": "https://www.cryptogram.org/downloads/aca.info/ciphers/Portax.pdf",
        "published_vector": {"plaintext": published_plaintext, "explicit_pad": "X",
                             "key": published_key, "effective_key": list(portax.effective_key(published_key)),
                             "expected_ciphertext": published_ciphertext, "actual_ciphertext": actual_ciphertext,
                             "actual_decryption": actual_plaintext, "pass": True},
        "published_pairs": pair_results,
        "exhaustive_pair_inverse_cases": inverse_cases,
        "same_column_pair_cases": same_column_cases,
        "pair_permutation_sizes": [676] * 13,
        "adjacent_keypair_equivalence_cases": keypair_cases,
        "distinct_effective_slide_maps": len(set(slide_maps)),
        "published_partial_layout": {"period": 7, "length": 24, "rows": rows,
                                     "packing": [list(pair) for pair in expected_packing]},
        "varied_periods": [1, 20], "seed": 20261005,
        "varied_length_roundtrip_cases": roundtrip_cases,
        "incomplete_block_roundtrip_cases": partial_cases,
        "known_plaintext_synthetic_effective_key_recovery_cases": synthetic_recovery_cases,
        "rejected_invalid_inputs": rejected,
        "method_sha256": hashlib.sha256((ROOT / "scripts/portax_v1.py").read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    results = run()
    destination = Path(__file__).with_name("verification_results.json")
    destination.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in results.items()
                      if key in ("status", "exhaustive_pair_inverse_cases",
                                 "adjacent_keypair_equivalence_cases", "varied_length_roundtrip_cases",
                                 "incomplete_block_roundtrip_cases", "known_plaintext_synthetic_effective_key_recovery_cases")}, indent=2))
