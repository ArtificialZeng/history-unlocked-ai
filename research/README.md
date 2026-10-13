# Portable no-repeat research registry

This sanitized snapshot retains known case IDs, exact identity aliases, public source locators and image hashes. It excludes runtime leases, free-text case histories and private correspondence. All registered items block a **new** attack; a source-page/hash collision requests identity review rather than silently equating separate messages. A clear result is not proof of worldwide novelty or permission to solve.

```sh
python3 scripts/case_registry.py --state-dir /tmp/history-unlocked-state init --seed research/NO_REPEAT_REGISTRY.json
python3 scripts/case_registry.py --state-dir /tmp/history-unlocked-state check --case-id hcportal:615
```

The second command deliberately returns `REJECT` (exit2), because the known confirmed case must not be attacked again. Use a working state directory outside this repository. Re-running `init` merges without erasing exclusions.

Fresh primary status, exact-item prior review, source qualification, matched method controls and transparent feasibility strictly above80/100 precede any historical solver assignment. Scores are judgments, not calibrated probabilities. Root coordinates; isolated workers solve only admitted cases. The local registry lock coordinates a single current directory, not disconnected machines.

Snapshot date:13October2026. The snapshot contains **2,550 registered identities**,
including 29 additional screening records since code-core-v3.
These are administrative exclusions, not counts of cryptanalytic attempts or
solved ciphers. Case counts are in [PROGRESS.json](PROGRESS.json). Existing frozen
attempts remain frozen; this file does not authorize their restart.

The [latest screening report](SCREENING_UPDATE.json) records the source and
identity holds alongside the new Italian and Spanish catalogue leads. None was
admitted to historical key search. The [update provenance](UPDATE_PROVENANCE.json)
pins the full local registry and its different sanitized public derivative.

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
