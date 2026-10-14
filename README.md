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

### Latest update · 14 October 2026

**Unlock history — and make every claim checkable.** The 11-entry portfolio includes HC615's official confirmation and HC1679's independently audited partial reading: 276 selected positions, 2,633 checks and 15 explicitly unresolved spans. Every runnable case retains its reproduction command and scientific hashes.

**New: recover readable text even when symbols are missing.** In a separate wordless Czech benchmark, 6 synthetic messages of 400–600 letters included masked single symbols and collapsed unknown spans. The solver recovered **5/6 known-position streams exactly and 2,612/2,613 known characters (99.96%)**, compared with 575/2,613 for frequency-only ranking. A separate AI-assisted workflow independently verified **3,156 checks**. The one-character failure is retained, and 387 hidden original characters are not claimed as recovered. Source code, fixed masks and seeds, all 162 restart outputs, an offline checker and fresh replay commands are included. This is a synthetic method result; the historical portfolio remains at 11 entries. [Reproduce the masked-symbol benchmark](methods/czech_wordless_masked_masc/README.md).

**New: recovering Czech text without word spaces.** The portable substitution solver recovered all six synthetic messages at lengths of 200, 400 and 600 letters: **2,400/2,400 characters**, versus 596/2,400 for a frequency-only baseline. A separate AI-assisted audit passed 156 checks and confirmed exact forward reconstruction; a freshly compiled replay also matched the frozen output. The module includes source code, fixed seeds, controls and verification commands. These are clean modern-Czech tests; historical handwriting, missing symbols and other cipher families still require separate qualification. [Explore the reproducible solver](methods/czech_wordless_masc/README.md).

**New portable code:** a static JavaScript loader tracer now accompanies the catalogue parser. Four synthetic controls check nested calls that share the same start offset, lexical wrappers, in-page containers and a false-resource negative. It parses source without executing page JavaScript or fetching data. Dynamic or unsupported expressions stay unresolved. [Run the four controls](research/catalogue_metadata/static_loader/README.md).

**Find new mysteries without solving the same one twice.** The portable registry retains **2,579 identities** and every previous exclusion. This update adds two source-image fingerprints; the preceding releases added six fingerprints and 11 screening identities. Official checks excluded DECRYPT #1185 and #2284 because both are already listed as Decrypted. Two 1646 British Library records remain source/prior/method holds; one observed image-gallery route requires authentication. [Current source checks](research/SOURCE_CHECKS.json).

**Reusable discovery tools:** the 846-object catalogue index has ten verified interface-field bindings. Its 266-object “open” group also includes partial readings and key records. Each candidate still needs exact-item source and prior checks. [Catalogue evidence](research/CATALOGUE_MAPPING.json) · [HC Portal inventory](research/CATALOGUE_REFRESH.json).

**Published readings come before new attacks.** Exact prior claims for Brussels R982 and R984 now exclude them from the new-target queue. New British Library and SP53/16 leads remain held for source, identity, language or method evidence. The latest work advances reproducibility and selection, with no additional complete decipherment in this release. [Screening notes](research/SCREENING_NOTES.md) · [Evidence and remaining barriers](research/SCREENING_UPDATE.json).

[Research tools](research/README.md) · [Method controls](methods/README.md) · [Release changes](CHANGELOG.md)

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
