# Reproduce the historical cipher evidence

Run from the repository root with Python 3.10 or later:

```sh
python3 -B scripts/verify_portfolio.py --replay
```

This command checks the derivative's own SHA-256 manifest, confirms that the
selected scientific payloads remain byte-identical to their original packages,
checks the repository's public-content boundary, and executes nine verification
commands covering eight cases. No accounts, API keys, AI calls, downloads, or
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
| HC1679 | Conditional partial reading; 276 selected positions; all 15 unresolved spans and 114 saved trials preserved; 2,633 derivative checks |

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

## Target-independent research tools

With Node.js 22 or later, run `node scripts/verify_methods.mjs` for the frozen
indexed-cell software and independent synthetic-only audit. Its controls are
not historical-target trials. See [method scope](../methods/README.md).

The [portable registry guide](../research/README.md) explains how to initialize
a separate working state from the sanitized identity snapshot. A known ID is
rejected; a shared page/image hash requests review. A clear registry result
does not replace fresh primary status, prior-art, source and method qualification.

The static-loader utility has four synthetic controls that run with the vendored
MIT Acorn parser, without an npm installation or page execution:

```sh
node research/catalogue_metadata/static_loader/check_controls.mjs
```

See its [supported syntax and limits](../research/catalogue_metadata/static_loader/README.md).
Passing these controls is software validation, not a historical cipher result.

## Czech substitution controls without word spaces

The [Czech solver module](../methods/czech_wordless_masc/README.md) provides
portable source code and frozen known-answer evidence for six messages of
200, 400 and 600 letters. Its artifact checker and optional freshly compiled
replay are separate from the nine historical-case verification commands above.
Consult the module guide for exact commands, corpus attribution and profile
limits. Synthetic recovery does not add a solved historical case to the portfolio.

## Czech controls with masks and unknown spans

The [masked wordless module](../methods/czech_wordless_masked_masc/README.md)
contains six new synthetic messages, fixed source-position masks and three
histogram/gap-preserving shuffled controls. From the repository root:

```sh
python3 -B methods/czech_wordless_masked_masc/verify_frozen.py
```

This offline artifact check is separate from historical-case replay. Reported
recovery concerns known positions only: 2,612/2,613 characters and 5/6 exact
known-position streams. The 387 masked original characters are not reconstructed
or graded. Returned-key/output forward consistency is 2,613/2,613; agreement
with the known original is 2,612/2,613. Consult the module guide for fresh compiled
replay, input rebuilding, the retained failure and profile/licence limits.
## Fixed-budget masked runtime

The [bounded runtime](../methods/czech_masked_bounded_runtime/README.md) exposes
an explicitly registered numeric-only interface with fixed code/model/input
pins, retained restarts, unknown-gap preservation and process limits. Run its
target-free checks without a compiler or network:

```sh
python3 -B methods/czech_masked_bounded_runtime/verify_runtime.py
```

With an existing C++17 compiler on a little-endian system, replay the public
synthetic P05 case into a new directory outside the repository:

```sh
python3 -B methods/czech_masked_bounded_runtime/replay_p05.py --output ../history-unlocked-bounded-p05
```

The P05 replay is a regression check and retains the original one-character
failure. It is not another complete benchmark or a historical decipherment.
The implemented 99-shuffle plan remains prospective; no historical comparison
result is claimed. A caller-supplied authorization digest is a local contract
assertion, not a credential or an independent admission decision.
