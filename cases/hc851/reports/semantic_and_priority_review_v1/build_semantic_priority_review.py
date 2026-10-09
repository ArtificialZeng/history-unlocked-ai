from pathlib import Path
import json,datetime,hashlib,re
R=Path(__file__).resolve().parents[2];P=R/'reports/semantic_and_priority_review_v1';cap=P/'captures'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
input_decode=R/'reports/target_decode_v1/ALL_EIGHT_REGISTERED_DECODES_v1.json';input_meta=R/'sources/raw/HC851_detail_2026-10-06.json';dec=json.load(open(input_decode));meta=json.load(open(input_meta));m=meta['data'];chosen=next(x for x in dec['results'] if x['start']==0 and x['direction']==1);literal=chosen['plaintext_literal']
phrases=[]
for x in ['DIELONDONUNDSONSTIGEHAFENANLAGE','MITLBOMBEN']:
 i=literal.index(x);phrases.append({'literal':x,'offset_zero_based':i,'positions_one_based_inclusive':[i+1,i+len(x)],'length':len(x),'unchanged':True})
assert len(literal)==144 and phrases[0]['positions_one_based_inclusive']==[38,68] and phrases[1]['positions_one_based_inclusive']==[125,134]
search=json.load(open(cap/'REGISTERED_SEARCH_RESPONSE_v1.json'))['result'];opens=json.load(open(cap/'DIRECT_OPEN_RESPONSE_v1.json'))['result'];urls=sorted(set(re.findall(r'https://[^\s)\]]+',search)))
allcapture=[{'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(cap.iterdir()) if p.is_file()]
api_receipt=json.load(open(cap/'PUBLIC_API_RECHECK_RECEIPT_v1.json'))
urlrecords=[]
primary_context=['https://pdf.sub.uni-hamburg.de/kitodo/PPN1012405958_19410315.pdf','https://mbc.cyfrowemazowsze.pl/Content/74313/00079985_-_Warschauer-Zeitung-R-4-1942-nr-188-11-VIII-_BUW-05764.pdf','https://sbc.org.pl/Content/651289/PDF/iv4424-1941-229-0001.pdf','https://opendata2.uni-halle.de/retrieve/a7d0a549-2739-41e6-af6c-400ebf13123c/166752470419411119.pdf','https://opendata2.uni-halle.de/retrieve/e5f6a53e-1a14-485a-ad42-47a79fd6c3ce/16818797781940070801.pdf']
for u in urls:
 urlrecords.append({'url':u,'access_registration_utc':json.load(open(P/'QUERY_REGISTRATION_v1.json'))['registered_utc'],'capture':str((cap/'REGISTERED_SEARCH_RESPONSE_v1.json').relative_to(R)),'source_status':'primary newspaper digital facsimile result; context only, no exact antecedent established' if u in primary_context else 'not relied on for semantic correction/priority; nonprimary/rehosted/other broad search result','content_hash_scope':'Hash of returned tool capture, not remote original document.'})
dump(P/'SOURCE_URL_INVENTORY_v1.json',{'sources':urlrecords,'direct_open_urls':['https://api.hcportal.eu/api/cryptograms/851','https://crypto.hcportal.eu/dashboard/cryptograms/851']+primary_context[:2],'access_failures':['DWDS robots.txt denial (no retry).','Public API and portal inaccessible via web.open.','Hamburg full PDF rejected by web.open: 16,553,445-byte content too large.','Warsaw full PDF web.open returned 502.','Independent unauthenticated API GET returned HTTP 466.'],'no_full_external_pdf_saved':True,'no_additional_search_queries':True})
assessment={
 'scope':'Bounded source-priority and semantic audit, not a candidate edit, source correction, fresh unknown-key cryptanalysis or publication.',
 'preferred_registered_decode':{'start':0,'direction':1,'literal':literal,'length':144,'mechanical_input_record':'reports/target_decode_v1/ALL_EIGHT_REGISTERED_DECODES_v1.json','all_eight_input_forward_ciphertexts_identical':len(set(x['forward_ciphertext'] for x in dec['results']))==1,'all_eight_input_match_count':sorted(set(x['matches_active_letters'] for x in dec['results'])),'physical_key_public':True,'public_key_url':'https://api.hcportal.eu/media/2512/29041685310199.jpg','claim_limit':'Input reports 144 active letters under supplied public physical grille. This audit does not rederive key geometry or certify the earlier cancelled/source layer.'},
 'phrases':phrases,
 'literal_assessment':{
  'London_phrase':{'spaced_literal_observation':'die London und sonstige Hafenanlage','grammar_status':'Anomalous under ordinary city-name and noun-coordination reading; London is unrepaired and Hafenanlage is singular. Spaces alone are editorial segmentation.','certainty':'Mechanical substring certain relative to the supplied decode; word division/intended syntax uncertain.','source_correction_established':False,'possible_typo_or_copying_error':'Possible hypothesis only; no independent historical antecedent or original answer establishes it.','prohibited_repair':'Do not insert, replace, pluralize or reconstruct any letter.'},
  'L_phrase':{'spaced_literal_observation':'mit L Bomben','L_status':'Unexpanded L retained. No primary terminology definition or exact antecedent established by the bounded search.','bomb_type_inferred':False,'replacement_or_repair':False},
  'brief_english_gloss_editorial':'Heavy attacks were directed against [the unresolved London/other-harbour-installation phrase] of the British capital; gasworks and railway stations were bombed with “L bombs” (L unresolved).',
  'gloss_limit':'Broad editorial sense only; it supplies neither the intended London phrase nor an expansion of L. No attack date is inferred.'},
 'external_search':{'queries_registered_before_execution':3,'queries_executed':3,'search_calls':1,'returned_capture':'reports/semantic_and_priority_review_v1/captures/REGISTERED_SEARCH_RESPONSE_v1.json','per_query_result_attribution':'The tool returned one combined batch response; do not claim separate exhaustive coverage for each query.','exact_HC851_prior_reading_found':False,'exact_historical_antecedent_found':False,'primary_L_Bomben_definition_found':False,'primary_context_limit':'Search returned broadly similar wartime attack-report language in primary newspaper scans. It did not establish this exact literal as their text. Full direct PDF opens failed or were size-limited.','negative_scope':'Finite three-query negative only. No worldwide priority, absence-of-original-answer or exhaustive literature claim.'},
 'catalogue_snapshot':{'input_file':str(input_meta.relative_to(R)),'input_sha256':sha(input_meta),'snapshot_date_from_filename':'2026-10-06','id':m['id'],'name':m['name'],'solution':m['solution']['name'],'cipher_key_id':m['cipher_key_id'],'language':m['language']['name'],'category':m['category']['name'],'date':m['date'],'date_around':m['date_around'],'updated_at':m['updated_at'],'folder':m['folder'],'tags':[x['name'] for x in m['tags']],'fresh_independent_http_recheck':'failed HTTP 466; no current-state override inferred','null_key_id_limit':'Null catalogue foreign-key field does not deny the public attached key image.','status_limit':'Catalogue snapshot only, not a historical-priority or external-acceptance certificate.'},
 'historical_priority':{'claim':'Unestablished','known_key_assisted':'Yes: grille key is publicly attached to HC851.','original_archive_answer_checked':False,'unindexed_or_unpublished_prior_readings_ruled_out':False,'worldwide_first_solution_claim_allowed':False},
 'input_hashes':[{'path':str(p.relative_to(R)),'sha256':sha(p)} for p in [R/'AGENTS.md',input_decode,input_meta]],
 'capture_hashes':allcapture,
 'mutations':'Only reports/semantic_and_priority_review_v1 artifacts written; target candidate, state, Git and source files not edited.'}
dump(P/'SEMANTIC_AND_PRIORITY_ASSESSMENT_v1.json',assessment)
report='''# HC851 bounded semantic and source-priority audit

The preferred registered `(start=0, direction=+1)` literal is retained exactly:

```text
'''+literal+'''
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
'''
(P/'SEMANTIC_AND_PRIORITY_REVIEW_v1.md').write_text(report)
print(json.dumps({'literal_positions':[x['positions_one_based_inclusive'] for x in phrases],'queries_executed':3,'literal_length':144,'catalogue_snapshot':m['solution']['name'],'status_recheck':api_receipt.get('error'),'primary_antecedent':'not established','priority':'unestablished'},ensure_ascii=False))
