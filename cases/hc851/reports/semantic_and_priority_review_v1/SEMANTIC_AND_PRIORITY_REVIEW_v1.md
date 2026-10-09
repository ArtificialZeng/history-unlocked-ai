# HC851 bounded semantic and source-priority audit

The preferred registered `(start=0, direction=+1)` literal is retained exactly:

```text
DIESCHWERENANGRIFFERICHTETENSICHGEGENDIELONDONUNDSONSTIGEHAFENANLAGEDERBRITISCHENHAUPTSTADTXFERNERWURDENGASWERKEUNDBAHNHOEFEMITLBOMBENBELEGTSTOP
```

The two audited substrings are `DIELONDONUNDSONSTIGEHAFENANLAGE` (positions 38–68) and `MITLBOMBEN` (125–134), using one-based positions in the 144-letter literal. No letter was repaired. The supplied mechanical output reports all 144 active letters reproduced and all eight registered orientation streams re-encode to the same ciphertext. This semantic audit does not independently rederive grille geometry or certify an earlier cancelled/source layer.

The grille key is a **public historical attachment** ([key image](https://api.hcportal.eu/media/2512/29041685310199.jpg)); the work is known-key-assisted archival reading. A null `cipher_key_id` in catalogue metadata is not evidence that no physical key is available.

## Literal meaning and uncertainty

A spaces-only editorial segmentation is `die London und sonstige Hafenanlage`. Under an ordinary city-name/noun-coordination reading this is grammatically anomalous. The literal retains **LONDON**, and **HAFENANLAGE is singular**. Neither word division nor the intended construction is established by an independent antecedent. Typo, copying or teaching-text error remains a possible hypothesis; no correction is source-verified. This report provides no modern restoration as the literal.

`MITLBOMBEN` admits a spaces-only observation `mit L Bomben`. The **L remains unexpanded**. The three-query search did not establish a primary definition or exact matching text. No bomb type, historical attack date or intended replacement is inferred.

A rough **editorial English gloss**, not a literal repair, is: “Heavy attacks were directed against [the unresolved London/other-harbour-installation phrase] of the British capital; gasworks and railway stations were bombed with ‘L bombs’ (L unresolved).” The bracketed phrase and L are genuine limits of this gloss.

## Bounded source evidence

Exactly three search queries were registered before one batched execution. Their exact strings are in `QUERY_REGISTRATION_v1.json`; no further search query was issued. The tool returned a combined response, so this report does not claim separate exhaustive per-query coverage.

1. Exact HC851/title/cipher-prefix prior-casework search.
2. Unmodified long literal prefix plus London/Hafen, seeking primary historical antecedents.
3. L-Bomben, restricted to named public newspaper/archive/lexicon domains.

No exact prior HC851 reading, exact historical antecedent, or primary L-Bomben definition was established in that finite response. Primary newspaper search results contain broadly related attack-report language ([Hamburg library newspaper scan](https://pdf.sub.uni-hamburg.de/kitodo/PPN1012405958_19410315.pdf), [Warsaw newspaper scan](https://mbc.cyfrowemazowsze.pl/Content/74313/00079985_-_Warschauer-Zeitung-R-4-1942-nr-188-11-VIII-_BUW-05764.pdf)); these are **context-only results**, not a verified source for the exact HC851 literal. Their historical dates are not assigned to the target. Nonprimary mirrors/rehosts returned by the search were not used to restore text or infer a bomb designation.

Access limitations are preserved in captures: DWDS denied robots access; web opening the Hamburg PDF failed due to its 16,553,445-byte size; Warsaw PDF opening returned 502; the API and portal were inaccessible to the web tool. An unauthenticated direct API recheck returned HTTP 466. No credentials were requested, no full external PDF was saved, and no retry/exhaustive-search claim is made.

## Catalogue status and priority scope

The supplied dated primary API snapshot `sources/raw/HC851_detail_2026-10-06.json` records HC851 as **Not solved**, German, Transposition; `cipher_key_id=null`; exact `date=null`, `date_around=1952`; and tags including **Cryptanalysis course**. It identifies the archival folder as box BF388a, 27-19/6-099 in ZSGS at Archiv bezpečnostních složek. The independent HTTP recheck failed, so no later catalogue-state update was verified. The around-1952 label is archival catalogue context and does not date the wartime-sounding message.

The archive's original answer, unpublished/unindexed prior readings and external acceptance were not checked or ruled out. “No exact antecedent found in these three queries” is the complete negative result. **Historical priority is unestablished**; neither worldwide-first nor absent-original-answer claims follow from a portal Not solved field or this finite search.

Only this report directory was written. The exact query registration, raw returned search/open responses, failed API receipt, URL inventory, assessment JSON and hashes are sealed locally. Remote-source hashes mean captured responses only; no hash of an unfetched original PDF is claimed.
