# HC Portal #1619: Fixed key transfer

Conditional preferred reading / conservative partial.

Preferred 80/80; conservative 79/80 keeps O0080 unknown.

[Original catalogue](https://crypto.hcportal.eu/dashboard/cryptograms/1619) · [Public API](https://api.hcportal.eu/api/cryptograms/1619)

## Reproduce

Python 3.10+; offline checks use the Python standard library. From this case directory:

```sh
python3 -B checker.py --output-dir /tmp/hc1619_fresh_replay
```

The verifier replays frozen transcription, keys and certificates. An exact forward check establishes consistency with those source records; it does not repeat visual transcription, establish worldwide priority, or establish the correctness of all historical interpretations.

## Review status

Results for other cipher problems are undergoing verification by other experts; verdicts will be recorded when available. This statement does not turn conditional proposals or supplied-key replays into expert-confirmed solutions.

## Package scope and licensing

This is a code/data/methods derivative of the original case package. Scientific payload files are retained byte for byte and listed in [core provenance](../../docs/CORE_PROVENANCE.json). Existing case licences remain authoritative. Original scans, PDFs, manuscript bundles and media submissions are not distributed here. Historical evidence manifests may reference omitted items; they do not certify this derivative as the old full release.
