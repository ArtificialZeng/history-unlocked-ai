# Reusable methods and known-answer controls

## Czech substitution without word spaces

The [portable Czech solver](czech_wordless_masc/README.md) adds independently
audited known-answer controls for clean, accent-folded Czech with word boundaries
removed. Six frozen messages of 200, 400 and 600 letters were recovered exactly:
2,400/2,400 characters and 132/132 observed key entries. Frequency-only ranking
recovered 596/2,400 characters. The independent audit checked 156 assertions,
candidate-key forward reconstruction and one fresh compiled replay.

Code, seeds, frozen evidence and reproduction instructions are included. This
profile does not certify historical handwriting, erasures or a target's cipher
family. Three frequency-preserving shuffled controls do not establish statistical
significance or a calibrated historical success probability.

## Czech substitution with masked symbols and unknown spans

The [masked/gap benchmark](czech_wordless_masked_masc/README.md) extends the
wordless profile to six new 400–600-letter synthetic messages. Fixed masks
replace individual symbols and short unknown spans with explicit gap sentinels.
Recovery is 5/6 exact known-position streams and 2,612/2,613 known characters;
the frequency baseline recovers 575/2,613. All 387 hidden original characters
remain ungraded, and the one-character P05 failure is retained.

A separate AI-assisted audit verified 3,156 assertions, all 162 restart outputs
and the training-only model. This is synthetic software evidence, not an
external expert verdict or a newly deciphered historical message. The module
provides frozen checking, optional fresh compiled replay and a deterministic
rebuild from pinned upstream corpus files. Its UD-derived data are
CC BY-NC-SA 4.0; program code is MIT.

## Indexed cells

The indexed-cell resource is a self-contained, target-independent codec and
verifier. Its 11 frozen files are copied unchanged. It preserves literal tokens,
explicit lengths and source-supported distinctions; it rejects duplicate,
missing, malformed or out-of-range positions rather than silently repairing them.

Run with Node.js 22 or later:

```sh
node scripts/verify_methods.mjs
```

The runner verifies all input/software locks, checks three prewritten known-answer
fixtures and 30 refusal controls, and enumerates 364 token vectors under 12 order
variants (4,368 decode variants). A separate verifier reads the frozen controls
without calling the kernel. No historical source, target, language model, AI or
network is used. A software PASS does not establish applicability to an archive
item or calibrate historical success probability.

[API and frozen scope](indexed_cells/README.md) ·
[Mathematical specification](indexed_cells/MATHEMATICAL_SPEC.md)

Original project code and synthetic controls: copyright Zijian Zeng, 2026,
MIT under the repository licence. This release note sits outside the frozen
directory so the original locks remain valid.
