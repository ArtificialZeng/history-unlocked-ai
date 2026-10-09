# Reproduce the historical cipher evidence

Run from the repository root with Python 3.10 or later:

```sh
python3 -B scripts/verify_portfolio.py --replay
```

This command checks the derivative's own SHA-256 manifest, confirms that the
selected scientific payloads remain byte-identical to their original packages,
checks the repository's public-content boundary, and executes eight verification
commands covering seven cases. No accounts, API keys, AI calls, downloads, or
new target searches are needed. Outputs are printed; HC1619's generated receipt
is created in a temporary directory outside the frozen inputs.

| Case | What the replay checks |
|---|---|
| HC615 | 220 glyphs, 32 segments, eight lines; fixed observed substitution; archived control trials |
| HC696 | 180 final-visible letters; PORTAX encrypt/decrypt; source and certificate pins; six negative tests |
| HC849 | Given-grille mechanical projections, source-position certificates and integrity tests |
| HC851 | 144 active letters; two grille implementations; 800 synthetic controls; integrity tests |
| HC852 | Given-grille mechanical projections, held source alternatives and integrity tests |
| HC1615 | Donor-key/mark-carry projection; source certificates; 48 tamper checks |
| HC1619 | Preferred 80/80 and conservative 79/80 transfer packets; ten pinned input files |

HC1760 is an index entry; HC1446 and HC1098 are partial-result notes. These three
entries are not runnable solver releases. The HC1619 comparator in the HC1760
analysis is not counted as another independent solved message.

An exact forward check proves consistency with a frozen transcription and stated
model. It does not independently re-read omitted source images, prove historical
priority, resolve an ambiguous source layer, or provide a new external verdict.
The official HC615 catalogue status is documented separately with a public URL.

The earlier full-package manifests are not the manifest for this derivative.
Historical internal manifests retain their source references and may explicitly
report omitted scans or documents. `CODE_CORE_MANIFEST.json` defines this release;
`docs/CORE_PROVENANCE.json` pins the unchanged scientific subset.
