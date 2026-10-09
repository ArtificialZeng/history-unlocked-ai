# PORTAX primary-method freeze v1

Status: PASS for the primary construction and controls, 5 October 2026.
Scope: isolated method work. No target image, ledger, transcription, letters,
candidate, or answer-bearing project document was opened. Root handles the
checkpoint, project state, research log, and Git.

## Primary-source calibration

The [ACA PORTAX one-page PDF](https://www.cryptogram.org/downloads/aca.info/ciphers/Portax.pdf)
was downloaded, retained, hashed, rendered, and visually inspected in full.
The two diagrams establish the relative position of the fixed row and slides.
The printed examples establish both rectangle and same-column substitutions.
The six-row example establishes horizontal output after vertical pairing; the
final example establishes equally short final rows.

Actual run: key `EASY` has slides `(2, 0, 9, 12)`.
Input `THEEARLYBIRDGETSTHEWORM` with explicitly requested `X` padding produced
`NIJAMPBGQCWKHQJEUIKYMPAT`, exactly the printed ciphertext. Decryption returned
`THEEARLYBIRDGETSTHEWORMX`. The printed U/V pairs `IN -> JL`, `NO -> UA`,
`NA -> DB`, and E/F pairs `TA -> NM`, `BG -> QH` all passed.

The period-seven partial layout is `SHALLBE / UPLIFTE / DNEVE / RMORE`:
two full rows and two five-letter rows. The final ten letters pair at offsets
`14+i` and `19+i`, using key column `i` for `i=0..4`.

## Authored rule and API

`scripts/portax_v1.py` is authored from the diagrams rather than obtained from
an external implementation. For integer letters `a,b` in `0..25` and slide
`s` in `0..12`, use coordinates:

```text
top_column = a                         if a < 13
             (a - 13 - s) mod 13       otherwise
bottom_column = (floor(b/2) - s) mod 13
bottom_row = b mod 2
```

If the columns differ, output the unused rectangle corners in the same A1/A2
roles and rows. If the columns coincide, change A1 row and A2 row, retaining
the column. This direct geometric rule is its own inverse. The code preserves
all letters and rejects unsupported characters and odd ciphertext lengths.

Exports:

- `transform_pair(top: int, bottom: int, slide: int) -> tuple[int, int]`
- `pair_letters(top: str, bottom: str, key_letter: str) -> tuple[str, str]`
- `effective_key(key) -> tuple[int, ...]`
- `packing_pairs(length: int, period: int) -> tuple[(top_index, bottom_index, key_index), ...]`
- `transform_block(text: str, key) -> str`: one even block, at most `2*period`.
- `transform(text: str, key) -> str`: any even length.
- `encrypt(text, key, *, pad_odd=False, pad_char='X') -> str`
- `decrypt(text, key) -> str`: retains any padding.
- `transform_values(values, key) -> tuple[int, ...]`
- `PAIR_TABLE[slide][top][bottom] -> (new_top, new_bottom)`

Text inputs are exact uppercase ASCII A-Z. Keys may be exact uppercase letter
strings or integer-slide sequences. Adjacent key letters `AB/CD/EF/GH/IJ/KL/MN/OP/QR/ST/UV/WX/YZ`
are equivalent. Thus a solution can establish effective slides without uniquely
establishing original key spelling. Thirteen complete pair maps are distinct.

## Reproducible controls

Run from the project directory:

```sh
python3 reports/method_primary_work_v1/test_portax_v1.py
```

This writes `verification_results.json`. Actual results:

- 8,788 pair cases: exhaustive `26 x 26 x 13` self-reciprocity, mutual inverse,
  no fixed pair, and 676 distinct outputs per slide.
- 8,788 adjacent-keypair equivalence cases; exactly 13 distinct slide maps.
- 676 same-column cases included in the exhaustive test.
- 920 deterministic varied-length roundtrips across periods 1-20, including
  816 incomplete final blocks and explicit odd-length padding.
- All input positions appear in exactly one vertical pair. Individual-block
  transformation agrees with the full-text transformation.
- 20 known-plaintext synthetic effective-key recoveries by finite enumeration,
  exposing all letter pairs at each column. These are nonlinguistic controls
  and do not test target-language search or scoring.
- Nine invalid-input cases reject unsupported symbols, lowercase/whitespace,
  unannounced padding, invalid slides/letters, empty keys, and oversized blocks.

All passed under system Python 3.9.6. The initial import used a Python 3.10
type-alias expression; its compatibility failure and correction are retained
in `verification_failures.json`. No cipher rule was revised.

The preserved primary source, authored code, test harness, actual results, and
receipt are covered by `SHA256SUMS`. These controls validate the published
method only and make no target decipherment claim.
