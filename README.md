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

Python 3.10+. Offline verification needs only the standard library. The runner checks scientific input hashes and executes **eight verification commands across seven runnable cases**, including forward reconstruction and applicable negative tests. It makes no AI or network calls. Cloning a private repository requires access; the verification itself needs no account.

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

The portfolio contains ten research entries, with explicit differences between confirmed readings, local exact readings, supplied-key replays and partial work. The HC1619 comparator is counted once. [Machine-readable index](data/CASE_INDEX.json).

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
