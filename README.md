# History Unlocked AI

## Hidden messages. Open code. Verifiable results.

**AI reads a Cold War cryptogram — and the evidence is yours to reproduce.**

An expanding collection of AI-assisted historical cipher results led by **Zijian Zeng, UCSI University**. From Czech substitution symbols to PORTAX, turning grilles and conditional key-transfer readings, this project makes the path from historical symbols to checkable text available as code.

[English](README.md) · [中文](README.zh-CN.md) · [Čeština](README.cs.md) · [日本語](README.ja.md)

**HC Portal #615 is officially listed as Solved and credited to Zijian Zeng.** Results for other cipher problems are being verified by other experts; their conclusions will be added as they become available.

[Official HC615 record](https://crypto.hcportal.eu/dashboard/cryptograms/615) · [Public status excerpt](docs/HC615_PUBLIC_CATALOGUE_STATUS.json) · [HC615 reading and method](cases/hc615/docs/SOLUTION.md)

### Reproduce it in one command

```sh
git clone https://github.com/ArtificialZeng/history-unlocked-ai.git
cd history-unlocked-ai
python3 -B scripts/verify_portfolio.py --replay
```

Python 3.10+. Offline verification needs only the standard library. The runner checks scientific input hashes and executes **nine verification commands across eight runnable cases**, including forward reconstruction and applicable negative tests. It makes no AI or network calls. Cloning a private repository requires access; the verification itself needs no account.

### Explore the results

| Case | Method | Current evidence | Code / notes |
|---|---|---|---|
| HC615 | Monoalphabetic substitution | Officially catalogued solved; all 220 observed symbols reproduced | [Replay](cases/hc615/) |
| HC696 | PORTAX | Exact local reading of 180 final-visible letters; old-layer holds retained | [Replay](cases/hc696/) |
| HC849 | Turning grille | Supplied-public-key reproduction of 64 active letters | [Replay](cases/hc849/) |
| HC851 | Turning grille | Supplied-public-key reproduction of 144 active letters | [Replay](cases/hc851/) |
| HC852 | Turning grille | Supplied-public-key reproduction of 64 active letters; alternatives retained | [Replay](cases/hc852/) |
| HC1615 | Donor key / mark-carry | Conditional proposal; fixed rules and source certificates | [Replay](cases/hc1615/) |
| HC1619 | Key transfer | Conditional preferred 80/80; conservative 79/80 with one unknown | [Replay](cases/hc1619/) |
| HC1760 | Comparative card analysis | Conditional proposal; no standalone solver in this release | [Index note](cases/hc1760/) |
| HC1446 | Symbol / ordering analysis | Partial result; four marks remain unassigned | [Partial note](cases/hc1446/) |
| HC1098 | Symbol / ordering analysis | Partial result; 48 source fields remain erasures | [Partial note](cases/hc1098/) |
| HC1679 | Conditional substitution | Independently audited partial reading; 276 selected positions checked, 15 unresolved spans | [Replay](cases/hc1679/) |

The portfolio contains eleven research entries, with explicit differences between confirmed readings, local exact readings, supplied-key replays and partial work. The HC1619 comparator is counted once. [Machine-readable index](data/CASE_INDEX.json).

### Latest update · 13 October 2026

**More evidence, ready to replay:** HC1679 now adds an independently audited partial-reading checker with 2,633 passing checks and no new key search. The unchanged candidate still contains 15 unresolved spans; it is published as a partial result.

The research toolkit also includes a sanitized **2,550-identity no-repeat registry** and frozen indexed-cell code with 3 known-answer controls, 30 refusal controls and 4,368 finite decode variants. These tools help others extend the project without repeating known cases or treating plausible prose as proof.

**Find the next cipher without losing the evidence:** the independently audited catalogue parser preserves exact item links and refuses to confuse incomplete parsing with an empty search. Its portable checks retain 14 regression assertions and six adversarial cases. The latest update adds **29 screening identities**, including Italian and Spanish archive leads, with explicit source and prior-reading holds. Parent aliases are checked alongside child IDs; a server error image has been removed from ciphertext fingerprints. These are research infrastructure results, with no new complete decipherment in this update. [Screening results and remaining barriers](research/SCREENING_UPDATE.json) · [Run the catalogue controls](research/catalogue_metadata/README.md).

[Latest research tools](research/README.md) · [Method controls](methods/README.md) · [Release changes](CHANGELOG.md)

### Why it matters

Historical archives hold messages whose symbols, source layers and encoding procedures still need to be reconstructed. AI can help organise these tasks and write specialised programs. Reproducible evidence lets others check what was read, what assumptions were used and what remains unknown.

HC615 is catalogued as a circa-1952 Czechoslovak cryptanalysis-course item. Its Czech text concerns workers sent to Ostrava for a one-year work brigade. One consistent symbol mapping explains every observed source unit, giving readers a concrete way to check the recovered historical content.

### How the evidence works

- Preserve the exact item ID, public source URLs and transcription provenance.
- Keep uncertain marks, overwritten layers and editorial restorations explicit.
- Freeze the key, model and candidate before certificate replay.
- Re-encrypt the proposed text and compare it with every observed source unit.
- Run controls and tamper checks appropriate to the case.
- Record external verdicts separately from mechanical consistency.

[Reproduction guide](docs/REPRODUCIBILITY.md) · [Unchanged scientific payload hashes](docs/CORE_PROVENANCE.json) · [Release manifest](CODE_CORE_MANIFEST.json)

### Help unlock more history

**Star** to follow new results. **Fork** to run the checkers. Bring an independent source reading, language review or a documented archival answer sheet through an issue or pull request. [Contribution guide](CONTRIBUTING.md).

**Lead researcher:** Zijian Zeng · UCSI University, Kuala Lumpur, Malaysia.

This repository distributes reproducible code, necessary research data, methods and brief project promotion. Case licences and source rights remain separate: [licence scope](LICENSE_SCOPE.md).
