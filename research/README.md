# Portable no-repeat research registry

This sanitized snapshot retains known case IDs, exact identity aliases, public source locators and image hashes. It excludes runtime leases, free-text case histories and private correspondence. All registered items block a **new** attack; a source-page/hash collision requests identity review rather than silently equating separate messages. A clear result is not proof of worldwide novelty or permission to solve.

```sh
python3 scripts/case_registry.py --state-dir /tmp/history-unlocked-state init --seed research/NO_REPEAT_REGISTRY.json
python3 scripts/case_registry.py --state-dir /tmp/history-unlocked-state check --case-id hcportal:615
```

The second command deliberately returns `REJECT` (exit2), because the known confirmed case must not be attacked again. Use a working state directory outside this repository. Re-running `init` merges without erasing exclusions.

Fresh primary status, exact-item prior review, source qualification, matched method controls and transparent feasibility strictly above80/100 precede any historical solver assignment. Scores are judgments, not calibrated probabilities. Root coordinates; isolated workers solve only admitted cases. The local registry lock coordinates a single current directory, not disconnected machines.

Snapshot date:13October2026. Case count is in `PROGRESS.json`. Existing frozen attempts remain frozen; this file does not authorize their restart.
