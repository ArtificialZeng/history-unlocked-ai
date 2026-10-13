# Finding the next genuinely open cipher

Snapshot: 13 October 2026, code-core-v5. The public portfolio contains eleven
research entries, including HC615's official confirmation and HC1679's audited
conditional partial reading. This update improves source and prior-reading
qualification; it adds no complete decipherment or external verdict.

| Lead | Completed observation | Current decision / remaining requirement |
|---|---|---|
| BnF / DECRYPT R4274 | A public catalogue describes a Tournon letter of 27 February 1556 with cipher and decipherment. | Exclude from new-target admission; exact source-region correspondence remains unverified. |
| BnF / DECRYPT R4279 | A modern Guiche study claims key recovery and substantial partial reading for a letter of 22 November 1551. | Exclude from new-target admission; folio references remain unresolved and are not silently merged. |
| Brussels / R992, R996, R997, R998 | A public Balbases study references these exact record IDs as letters without an original decipherment. | HOLD: historical absence of an answer does not establish absence of modern work. |
| Two Belgian inventory routes | Requests produced a redirect or HTML rather than a PDF. | Access HOLD; no inventory contents, credential requirement or new cipher identity certified. |
| Zurich-labelled postcard / Baden-CH-tex | First native inspection: 1601 × 1009 image, clipped writing; Zurich and year suffix 07 visible. | Frozen source HOLD. Complete card, exact identity, absolute date, current prior clearance and matched method are unqualified. |
| First/2010 postcard on the same blog page | A cached comment cites a previously published solution; recipient metadata supports its attribution to the first card. | Prior-claim HOLD / no new attack; exact image correspondence remains unverified. |

Six cached claim blocks were reviewed without new network or target access.
A sentence about **another** solved card and a guess about Zurich shorthand are
different claims. Neither adjacency nor an old “unsolved” headline settles the
status of a particular image. Public-study claims are attributed evidence, not
independent verification of those studies' decryptions.

The no-repeat snapshot contains **2,554 identities**: all 2,550 earlier exclusions
plus four new records. Access routes and source candidates count as identities,
not additional solved or attempted cryptograms. The controller's 47 main rows
and 1,466 screening rows are likewise administrative totals.

The source and prior scopes add no full transcription ledger, historical key
search or target trial. Recorded deadline exceptions do not become timing PASS
or proof that a cipher is unsolvable. The original sealed records are retained
locally; only a compact public metadata derivative is distributed here.

[Structured observations, public references and limits](SCREENING_UPDATE.json) ·
[Snapshot provenance](UPDATE_PROVENANCE.json) · [Progress counts](PROGRESS.json)

To reproduce the portable tools offline:

```sh
python3 -B -m unittest discover -s tests
python3 -B research/catalogue_metadata/check_parser_controls.py
```

These commands verify registry and parser behaviour, including exact-identity
checks and incomplete-page refusal. They do not independently re-read omitted
source images or certify worldwide novelty. Every new target still requires
fresh primary status, exact prior review, source and matched-method qualification,
feasibility strictly above 80/100, and a central reservation before solving.
