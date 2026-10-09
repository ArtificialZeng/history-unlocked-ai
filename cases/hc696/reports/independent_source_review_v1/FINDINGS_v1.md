# HC696 independent original-pixel source review v1

The complete visible final uppercase layer is readable and fixed at **180 letter sites**. This is an independent pixel transcription, not a successful decipherment or a claim about the intended original typed text. The violet typewritten underlayer remains **unidentified at five sites** covered by thick dark letters: C023=P, C066=N, C080=B, C132=H, and C172=W. The image does not establish whether each overlay corrects a different letter or reinforces the same one. No alternative underlying alphabetic identity is asserted.

## Observed count and layout

The original is a 3024 × 4032 JPEG. I inspected the whole original, then native crops of all six cipher rows and the heading. Counting visible sites directly gives six rows, six spatial groups in each row, and five uppercase letter sites in every group: 36 groups and 180 sites. This independently checks the provisional 6 × 6 × 5 lead. Some internal gaps in rows 2 and 3 are larger than the usual pitch; their coordinates remain in the ledger. Dark overwrites occupy existing letter sites and do not add sites. Geometry does not recover occluded typed identities.

The final visible reading, with observed group and line divisions, is:

```text
CIUSW INBAX ERHPB WPXOQ YKPVA GUSRB
KWXKJ UKILR WBCJW MTYLZ WUSUF CBKDA
UGTKS NKJFS JLZGM MWZWB EKKMN LNAJT
SQMZL JCIMS WIFNE NEQPN SWQRC CPNLM
MQNSD MLWMK ZHKHL ENXJI VKPMW ASSHI
NKDJR ZCWJT BFPNG BQZGP HWZYO EKNCL
```

## Layer and mark policy

The five dark letters have directly legible final P/N/B/H/W shapes in the native image and nearest-neighbor enlargements. Their heavy irregular strokes differ from the violet typewriter impressions. The source ledger calls their dominant visible layer `thick_dark_overlay`; it does not call them five decipherment-driven repairs. Violet residues are insufficient to name their earlier typewritten forms. `typed_underlayer_held_v1.txt` has exactly five `?` markers and preserves all 175 directly readable typed sites.

The W at C077 remains visibly W despite an irregular darker crossing/top mark. This is recorded as an ambiguous crossing or print irregularity, not a replacement. C150 is visibly I with extra violet ink below/beside its lower serif. The apparent extension is not an additional letter.

Four dark underlines touch/spatially connect C005–C006, C011–C012, C101–C102, and C107–C108. The first runs across an intergroup blank. They are marks, not cipher glyphs. All retain occurrence references and original-coordinate event boxes. E11 is adjacent to the first cipher site; E12 is below the column of C153. These spatial references imply no semantic connection.

The noncipher typewritten heading is tentatively transcribed `Anglický text čís. 7`; mixed-case bases and the numeral are legible, while diacritic spellings are explicitly tentative. A violet dashed rule, a rising red heading stroke, a large handwritten magenta 4, a dark check/V-like shape, a left red margin stroke, and a narrow blue stroke below the cipher are separately inventoried. Header words and catalogue language/method labels were not used as cribs. Paper fibers, creases, and incidental stains are not exhaustively treated as deliberate handwriting.

## Provenance and review limits

`source_ledger_v1.json` is the authoritative per-site ledger. It records global position, line, group, position within group, final visible value, typewritten status, event IDs, original image hash, and original-pixel bbox for every occurrence. Boxes are manually centered occurrence windows spanning each native row height; they are reproducible provenance windows, not tight ink segmentation or claims that every edge belongs to one letter. `letter_position_ledger_v1.tsv` is an export of the same observations. `marks_and_layer_events_v1.json` and `noncipher_ledger_v1.json` link every inventory event to cipher or noncipher occurrences.

All crops are derived only by native `PIL.Image.crop`. Event views add exactly 3× nearest-neighbor duplication, without rotation, contrast changes, filtering, interpolation, sharpening, OCR, or synthetic strokes. `crop_manifest_v1.json` gives every crop's transform, source bbox, dimensions, and SHA-256. The display tool resized the whole original from 3024 × 4032 to 2752 × 3669 for display; that did not alter the retained original or native crop pixels.

The source's JPEG SHA-256 is `2dc894dd0aaa745eb5c7ba6155b653038cc6625817ef66ec0502125dd93f0ae4`, matching the adoption receipt. The sealed manifest hashes all report artifacts and the explicitly permitted source inputs. `verify_source_freeze.py` is read-only: it checks manifest hashes, count/layout, grouped/stream exports, held positions, source/event links, bbox bounds, and crop transform/hash metadata. It neither invokes nor reads a cipher method.

This cold observer did not read root README/state/protocol/config, methods, experiments, candidate answers, plaintext, keys, or other puzzle images, and made no network calls or Git/root-state changes. Actual exposure is documented in `EXPOSURE_v1.json`. Any later inference about the five hidden identities must remain distinct from this sealed source-only record.
