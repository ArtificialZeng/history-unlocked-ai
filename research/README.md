# Portable no-repeat research registry

This sanitized snapshot retains known case IDs, exact identity aliases, public source locators and image hashes. It excludes runtime leases, free-text case histories and private correspondence. All registered items block a **new** attack; a source-page/hash collision requests identity review rather than silently equating separate messages. A clear result is not proof of worldwide novelty or permission to solve.

```sh
python3 scripts/case_registry.py --state-dir /tmp/history-unlocked-state init --seed research/NO_REPEAT_REGISTRY.json
python3 scripts/case_registry.py --state-dir /tmp/history-unlocked-state check --case-id hcportal:615
```

The second command deliberately returns `REJECT` (exit2), because the known confirmed case must not be attacked again. Use a working state directory outside this repository. Re-running `init` merges without erasing exclusions.

Fresh primary status, exact-item prior review, source qualification, matched method controls and transparent feasibility strictly above 80/100 precede any historical solver assignment. Scores are judgments, not calibrated probabilities. Root coordinates; isolated workers solve only admitted cases. The local registry lock coordinates a single current directory, not disconnected machines.

Snapshot display date: 14 October 2026. The snapshot contains **2,579 registered
identities**, preserving all previous exclusions and refreshing observed source
locators and image fingerprints. No new identity was added in code-core-v10;
58 were added since code-core-v3. These are administrative
identities, not solved or attempted cipher counts. [PROGRESS.json](PROGRESS.json)
tracks the 11-entry portfolio separately. Frozen attempts remain frozen.

[Screening notes](SCREENING_NOTES.md), [current evidence](SCREENING_UPDATE.json)
and the [dated HC inventory](CATALOGUE_REFRESH.json) record published-reading
exclusions and incomplete source/method qualification. The
[update provenance](UPDATE_PROVENANCE.json) pins the full local registry and its
different sanitized public derivative; it does not transfer runtime ownership.

Exact parent aliases must be checked as well as child IDs. The portable helper
returns `REVIEW` for a shared non-HC alias, which blocks a new attack pending
identity review; it does not silently merge messages. An inherited hash of the
server's `forbidden.png` response has been removed from ciphertext fingerprints.
The affected case's no-repeat exclusion and all earlier flags remain.

## Catalogue selection without false empty results

The [portable catalogue parser](catalogue_metadata/README.md) preserves exact
item IDs and query-bearing links. It reports unknown when rows cannot be
accounted for, instead of declaring that no open items exist. Run its 14
regression checks and six adversarial tests offline; no source images, plaintext,
keys or authentication are needed.

## Static loader tracing without page execution

Run the four synthetic checks offline with Node.js 22 or later:

```sh
node research/catalogue_metadata/static_loader/check_controls.mjs
```

The [tool guide](catalogue_metadata/static_loader/README.md) explains AST node
identity, supported syntax and unresolved dynamic expressions. Acorn 8.19.0 is
vendored with its MIT notice. This is a selection utility, not a cipher solver.

## Verified catalogue fields, with unresolved item identity

The [dated metadata check](CATALOGUE_MAPPING.json) establishes 846 catalogue
articles/objects and ten interface-to-field bindings. The UI groups native
`open`, `part` and `key` together: its 266-object open group is not an independently
qualified unsolved-message count. Initial parent/mixed-system prospects were
withdrawn. No original response bodies, source scans or answer-bearing queries
are distributed. Individual open/prior/source/method qualification remains required.

## Latest exact status and access checks

[SOURCE_CHECKS.json](SOURCE_CHECKS.json) records the bounded official search, two
official Decrypted exclusions and held 1646 source prospects. Catalogue status,
public original access, exact prior clearance and decipherment remain distinct.
No target trial was run in those source-check scopes. The subsequent HC1527
trial is documented separately below.

## Wordless Czech method qualification

The [new solver module](../methods/czech_wordless_masc/README.md) includes six
known-answer controls without word boundaries and an independently reviewed
6/6 exact result. This qualifies only its documented clean modern-Czech
synthetic profile; it does not admit a historical target or clear its source
ambiguities.

The [masked/gap wordless module](../methods/czech_wordless_masked_masc/README.md)
adds six new known-answer controls, with 5/6 exact known-position streams and
2,612/2,613 known characters. Its independent 3,156-check audit preserves one
wrong known character and excludes 387 masked original characters from recovery
claims. Code-core-v10 adds two observed image fingerprints to the registry
without removing any previous exclusion or admitting a historical target.

## Completed masked-body trial: HC1527

The [retained numerical record](trials/hc1527_fixed_model_v1/README.md) includes
one fixed real-input call, 99 matched shuffles and all 1,800 restart scores.
Its conditional order signal exceeded the controls, but blinded AI-assisted
whole-content review did not establish a complete Czech message. The model
stopped at continuation feasibility 79/100; the earlier admission was 83/100.
These judgments are not probabilities. The numerical checker does not replay
target decipherment, re-read the source or substitute for expert review.

This update also adds two native HC1550 image fingerprints and retains the
source hold. All 2,579 registered identities and their prior exclusions remain.
