# HC696 independent own-code replay v1

5 October 2026. Status: PASS for the frozen visible-final layer. The originally
typed underlayer remains incomplete. This report makes a scoped local result,
not a claim about an official answer, historical priority, original key spelling,
or outside expert confirmation.

## Exact result

The independently authored `scripts/portax_v1.py` was frozen and calibrated on
the primary ACA examples before target access. Its eight seal hashes were
unchanged before and after this replay. This agent independently parsed the
source ledger and final stream, then used that Python implementation alone.
No root C++ search or decoder code was read, imported, or executed here.

Key representative `OAQKEQ`, period six, selects slides `(7, 0, 8, 5, 2, 8)`.
Decryption returns exactly:

```text
MANYPATROLSHAVESUCCESSFULLYACCOMPLISHEDTHEIRMISSIONSONLYTOLOSEPERSONNELBYAHASTYNOISYWITHDRAWALXNIGHTPATROLSGOOUTSTEALTHILYTAKINGALLPRECAUTIONSBUTFORGETALLTHATINGETTINGBACKTOSAFETYX
```

Forward encryption matches 180 of 180 observed final letters. The source's
180 sites are covered exactly once by 90 vertical pairs in 15 complete
two-row mathematical blocks. There are no inserted/deleted source letters,
substitution patches, unassigned replay fields, exceptional cipher rules,
or candidate-dependent source choices. Ledger-supported alternatives are empty.
The original image bytes agree with the source SHA-256 recorded in the ledger.
All four parsed inputs retained their hashes throughout the replay.

`occurrence_certificate_v1.json` preserves each complete source occurrence
and attaches the paired occurrence's position, line, group and pixel window,
key column, slide, A1/A2 role, decoded letter, and forward letter. The TSV
provides a compact view. `source_layout_and_events_preserved_v1.json` retains
all 36 source groups and all 18 event records, including noncipher annotations.
Text views retain the six source lines and five-letter grouping as layout;
they are not used as cryptographic row boundaries or word boundaries.

## Whole-reading audit

Only spaces are inserted in the following presentation:

```text
MANY PATROLS HAVE SUCCESSFULLY ACCOMPLISHED THEIR MISSIONS ONLY TO LOSE PERSONNEL BY A HASTY NOISY WITHDRAWAL X NIGHT PATROLS GO OUT STEALTHILY TAKING ALL PRECAUTIONS BUT FORGET ALL THAT IN GETTING BACK TO SAFETY X
```

Collapsing those spaces recovers all 180 letters. The audit records 35 token
spans, including both X tokens. The first clause describes loss after a
successful patrol mission; the second describes care during departure and its
loss during return. Subject, verbs, objects and the contrast between departure
and return continue across the entire message. No language repair is required.
This is a linguistic interpretation, supported separately by the pretarget
method calibration, compact fixed cipher parameters, and exact source replay;
LLM fluency is not treated as sufficient evidence of decipherment.

X is preserved at positions 95 and 180. X95 plausibly separates the two
sentences. If X95 is a separator, the preceding 179 letters are odd in number,
making a terminal X padding interpretation consistent with the published
paired construction. Neither interpretation is directly established by the
pixels or cipher transformation. Both X characters remain in the certificate
and authoritative decrypted stream, and both could be literal delimiters.

## Underlayer remains held

| Site | Final visible letter | Decoded letter | Earlier typed identity |
| --- | --- | --- | --- |
| C023 | P | F | unidentified |
| C066 | N | S | unidentified |
| C080 | B | N | unidentified |
| C132 | H | P | unidentified |
| C172 | W | T | unidentified |

The five ledger nulls remain null. The independently replayed visible letters
are the final dark overlay outlines, not recovered earlier violet characters.
Forward encryption of a selected plaintext predicts its ciphertext under that
key; it cannot independently identify occluded earlier ink or determine whether
an overlay corrected or reinforced it. A complete originally typed-layer
forward claim is therefore held. `typed_underlayer_hold_v1.json` retains the
original records and their uncertainty.

## Alternative falsification and scope

All 175 retained first-attack candidates were independently decrypted. Every
stored candidate plaintext agrees with the frozen Python construction. All
175 have exact own-key roundtrips: invertibility alone cannot distinguish a
meaningful reading from another candidate. The 174 alternatives differ from
the selected reading and fail to regenerate that fixed reading's observed
ciphertext at at least 158 positions.

Each of the 72 one-column slide mutations of the selected key was tried.
It changes 12-20 forward positions for this fixed reading. An independent
finite intersection of all 13 possible slides at every column for each period
1-20 admits this fixed reading only at period six, with precisely the six
selected slides. These constraints exhaust keys conditional on this reading
and those periods. They do not exhaust all possible plaintexts, cipher families,
periods outside the registered range, or arbitrary source reinterpretations.
The first attack remains a nonexhaustive optimisation search. The separate
matched negative controls are root's work and are not independently claimed here.

At each selected key position, either adjacent letter selects the same slide:
`OP / AB / QR / KL / EF / QR`. All 64 strings in the Cartesian product were
tested and yield the same ciphertext. `OAQKEQ` is therefore an effective-key
representative; the original six-letter spelling is not uniquely established.

## Historical-source check

Nine bounded search queries did not yield a verified exact official-manual
match for both decrypted sentences. A search-index hit suggested a related
passage in a mirrored *Battle Experiences* compilation, but the snippet's
mission number and second-sentence wording differ from the decrypted text.
That snippet is a lead, not a verified quotation or a historical citation.
The full PDF fetch was stopped after a very slow partial download; its listed
source mirror timed out after 30 seconds. No relevant printed page was
independently inspected. `source_search_negative_v1.json` retains the queries,
URLs, retrieval failures, and limited status. No date, page number, exact
quotation, or document-to-puzzle historical relationship is asserted.

## Reproduce

```sh
PYTHONDONTWRITEBYTECODE=1 python3 reports/independent_target_replay_v1/independent_replay.py
shasum -a 256 -c reports/independent_target_replay_v1/SHA256SUMS
```

`independent_replay_results_v1.json` contains the actual counts and scope.
`SHA256SUMS` covers this authored replay, certificates, retained failures,
reading audits and report. Root alone handles state, checkpoints and Git.
