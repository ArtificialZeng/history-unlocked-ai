# HC Portal #1615: Fixed donor-key / mark-carry projection

Conditional proposed reading.

77 source units; literal spellings and explicit rule assumptions retained.

[Original catalogue](https://crypto.hcportal.eu/dashboard/cryptograms/1615) · [Public API](https://api.hcportal.eu/api/cryptograms/1615)

## Reproduce

Python 3.10+; offline checks use the Python standard library. From this case directory:

```sh
python3 -B verify.py --root . --donor-key data/key/DONOR_FIXED_OBSERVED_KEY_v2.json --tamper
```

The verifier replays frozen transcription, keys and certificates. An exact forward check establishes consistency with those source records; it does not repeat visual transcription, establish worldwide priority, or establish the correctness of all historical interpretations.

## Review status

Results for other cipher problems are undergoing verification by other experts; verdicts will be recorded when available. This statement does not turn conditional proposals or supplied-key replays into expert-confirmed solutions.

## Package scope and licensing

This is a code/data/methods derivative of the original case package. Scientific payload files are retained byte for byte and listed in [core provenance](../../docs/CORE_PROVENANCE.json). Existing case licences remain authoritative. Original scans, PDFs, manuscript bundles and media submissions are not distributed here. Historical evidence manifests may reference omitted items; they do not certify this derivative as the old full release.
