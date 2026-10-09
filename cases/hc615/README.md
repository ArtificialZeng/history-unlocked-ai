# HC Portal #615: Monoalphabetic substitution

Complete observed-message reading; officially catalogued as solved.

220 observed symbols, 32 source segments, 8 lines; fixed 22-symbol observed mapping.

[Original catalogue](https://crypto.hcportal.eu/dashboard/cryptograms/615) · [Public API](https://api.hcportal.eu/api/cryptograms/615)

## Reproduce

Python 3.10+; offline checks use the Python standard library. From this case directory:

```sh
python3 -B scripts/verify_solution.py
```

The verifier replays frozen transcription, keys and certificates. An exact forward check establishes consistency with those source records; it does not repeat visual transcription, establish worldwide priority, or establish the correctness of all historical interpretations.

## Public confirmation

The public HC Portal record labels the item **Solved** and credits **Zijian Zeng**. See the [public catalogue excerpt](../../docs/HC615_PUBLIC_CATALOGUE_STATUS.json). No private email is part of this repository.

## Package scope and licensing

This is a code/data/methods derivative of the original case package. Scientific payload files are retained byte for byte and listed in [core provenance](../../docs/CORE_PROVENANCE.json). Existing case licences remain authoritative. Original scans, PDFs, manuscript bundles and media submissions are not distributed here. Historical evidence manifests may reference omitted items; they do not certify this derivative as the old full release.
