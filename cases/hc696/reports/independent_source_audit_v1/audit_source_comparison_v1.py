#!/usr/bin/env python3
"""Read-only source inputs; writes audit files only in this report directory."""
import datetime
import hashlib
import json
from pathlib import Path
from PIL import Image

BASE=Path(__file__).resolve().parent
ROOT=BASE.parent.parent
PRIMARY=ROOT/'reports/independent_source_review_v1'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def dump(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

own=load(BASE/'OWN_SOURCE_FREEZE_v1.json')
own_manifest=load(BASE/'OWN_FREEZE_MANIFEST_v1.json')
for name,h in own_manifest.items(): assert sha(BASE/name)==h,('own freeze changed',name)
pm=load(PRIMARY/'freeze_manifest_v1.json')
assert sha(PRIMARY/'freeze_manifest_v1.json')=='480412b221d352eab67b9b40b5087c6012adda332b336ac314e77e712e2575de'
assert pm['sealed_utc']=='2026-10-05T15:23:18.302809+00:00'
assert sha(PRIMARY/'source_ledger_v1.json')=='ce61b3011b69e846b123b49e873806fca6fb5e36467dfe20f3d3093696bce375'
primary=load(PRIMARY/'source_ledger_v1.json')
pe=load(PRIMARY/'marks_and_layer_events_v1.json')['events']
im=Image.open(ROOT/'sources/raw/HC696_original.jpg')
assert im.size==(3024,4032)
assert sha(ROOT/'sources/raw/HC696_original.jpg')==own['source_sha256']==primary['source_sha256']
a,b=own['sites'],primary['occurrences']
assert len(a)==len(b)==180
disagreements=[];box_pairs=[];identity_agreements=[]
for x,y in zip(a,b):
    assert x['index_1based']==y['global_position']
    assert (x['row'],x['group'],x['site'])==(y['line'],y['group'],y['position_in_group'])
    if x['final_visible']!=y['visible_final_uppercase']:
        disagreements.append({'own':x,'primary':y})
    else:
        identity_agreements.append({'position':x['position'],'primary_id':y['occurrence_id'],'value':x['final_visible']})
    q=x['bbox_original_px'];r=y['bbox_original_xyxy']
    assert 0<=q[0]<q[2]<=3024 and 0<=q[1]<q[3]<=4032
    overlaps=min(q[2],r[2])>max(q[0],r[0]) and min(q[3],r[3])>max(q[1],r[1])
    box_pairs.append({'position':x['position'],'own_bbox':q,'primary_bbox':r,'overlaps':overlaps,
                      'center_dx_abs_px':abs((q[0]+q[2]-r[0]-r[2])/2),
                      'center_dy_abs_px':abs((q[1]+q[3]-r[1]-r[3])/2)})
assert not disagreements
assert all(x['overlaps'] for x in box_pairs)
stream=''.join(y['visible_final_uppercase'] for y in b)
assert stream==own['compact_visible_final']
assert hashlib.sha256(stream.encode()).hexdigest()==own['compact_utf8_sha256']
held=[x['global_position'] for x in b if x['typed_underlayer_identity'] is None]
assert held==[23,66,80,132,172]
own_held=[s['index_1based'] for s in a if any(s['position']==e['position'] for e in own['dark_letter_events'])]
assert own_held==held
events_map={'D01':'E01','D02':'E02','D03':'E04','D04':'E05','D05':'E06','U01':'E07','U02':'E08','U03':'E09','U04':'E10','M01':['E13','E14','E15'],'M02':'E17','M03':'E16','M04':'E11','M05':'E18','M06':'E12'}

# These are deliberately separate from the immutable own first reading.
addendum={
    'stage':'post-comparison source-only addendum; not part of independent first-freeze inventory',
    'change_to_180_letter_string':False,
    'crossing_event':{'position':'R03G04P02','primary_id':'C077','primary_event':'E03','final_visible':'W',
                      'bbox_original_px':[1660,1160,1770,1290],
                      'observed_from_own_new_raw_crop':'An oblique dark/violet stroke crosses the upper-left/interior portion of the typed W; original two-trough W outline remains clear.',
                      'status':'Ink irregularity or extraneous crossing; no second letter identity or replacement history inferred.',
                      'independence_limit':'Own pre-comparison image crops contained this site, but first-freeze event inventory did not flag it. The primary crop filename and later ledger drew attention to it.',
                      'own_crop':'crops/postfreeze_r3g4p2_crossing_4x.png'},
    'extra_intrablock_spacing':{'row':3,'group':6,'visual':'LNA JT','after_site':3,
                               'source_evidence':'Own new original crop shows approximately 80 px pitch L-N-A, about 120 px A-J, about 80 px J-T.',
                               'own_crop':'crops/postfreeze_r3g6_spacing_2x.png',
                               'independence_limit':'Not explicitly preserved by the first own freeze or its pre-comparison addendum; identified from primary layout note then checked against original source.'},
    'bbox_refinements':[{'position':f'R03G06P{i:02d}','bbox_original_px':[x-38,1150,x+38,1250],
                         'reason':'Original crop has centers near stated x; enlarged A-J gap shifted original first-pass approximate centers.'}
                        for i,x in enumerate([2565,2645,2725,2845,2925],1)],
    'earlier_layer_holds':held,
    'letter_discrepancies':[],
}
dump(BASE/'POST_COMPARISON_SOURCE_ADDENDUM_v1.json',addendum)
result={
    'schema':'HC696_independent_source_comparison_v1',
    'inputs':{'own_freeze_sha256':sha(BASE/'OWN_SOURCE_FREEZE_v1.json'),
              'primary_manifest_sha256':sha(PRIMARY/'freeze_manifest_v1.json'),
              'primary_ledger_sha256':sha(PRIMARY/'source_ledger_v1.json'),
              'original_jpeg_sha256':own['source_sha256']},
    'final_layer':{'compared_sites':180,'identity_agreements':180,'identity_disagreements':0,
                   'geometry_agrees':True,'compact_utf8_sha256':own['compact_utf8_sha256']},
    'identity_agreements':identity_agreements,'letter_discrepancies':disagreements,
    'earlier_layer':{'both_observers_held_positions':held,'both_observers_named_underlying_alternatives':False,
                     'source_only_resolution':'Five hidden violet identities remain unresolved; each readable final dark letter could replace a different letter or reinforce the same letter.'},
    'event_map':events_map,
    'four_underline_occurrence_pairs':[[5,6],[11,12],[101,102],[107,108]],
    'source_inventory_discrepancies':[
        {'type':'own first-freeze omitted separate small crossing event','position':'R03G04P02','primary_event':'E03','letter_change':False,'record':'POST_COMPARISON_SOURCE_ADDENDUM_v1.json'},
        {'type':'own first-freeze omitted explicit fourth internal gap','row':3,'group':6,'after_site':3,'letter_change':False,'record':'POST_COMPARISON_SOURCE_ADDENDUM_v1.json'},
        {'type':'inventory granularity','own':'M01 combines heading, dashed rule and red stroke','primary':['E13','E14','E15'],'substantive_observation_change':False},
        {'type':'manual provenance windows differ','note':'All 180 corresponding windows overlap. Own first-pass x centers for R03G06 were approximate and were refined from the post-comparison original crop. Different box extents do not establish letter identities.'},
    ],
    'source_layout':{'agreed_internal_gap_sites':[[2,5,2],[2,6,4],[3,5,2]],
                     'post_comparison_added_gap_site':[3,6,3]},
    'bbox_comparison':{'overlapping_pairs':sum(x['overlaps'] for x in box_pairs),
                       'max_absolute_horizontal_center_difference_px':max(x['center_dx_abs_px'] for x in box_pairs),
                       'max_absolute_vertical_center_difference_px':max(x['center_dy_abs_px'] for x in box_pairs),
                       'pairs':box_pairs},
}
dump(BASE/'COMPARISON_v1.json',result)

transforms={
    **{f'row_{i}.png':{'bbox':box,'scale':1} for i,box in enumerate([(140,670,2970,870),(140,900,2990,1090),(160,1120,2990,1320),(170,1350,2970,1540),(170,1560,2970,1760),(180,1780,2970,1980)],1)},
    **{name+'_2x.png':{'bbox':box,'scale':2} for name,box in {'r1g5':(1970,700,2450,830),'r3g2':(630,1160,1080,1300),'r3g4':(1550,1140,1970,1280),'r5g3':(1090,1600,1530,1750),'r6g5':(2020,1780,2440,1920),'header':(90,400,1270,630),'row2_lastblocks':(2000,900,3020,1060),'row5_lastblock':(2470,1580,2960,1740),'r1underline1':(440,740,735,885),'r1underline2':(1060,740,1300,850),'r4underline1':(1110,1400,1280,1510),'r4underline2':(1620,1390,1810,1490),'postfreeze_r3g6_spacing':(2500,1120,2980,1280)}.items()},
    'postfreeze_r3g4p2_crossing_4x.png':{'bbox':(1600,1160,1740,1250),'scale':4},
}
crop_records=[]
for name,t in transforms.items():
    box=t['bbox'];scale=t['scale'];derived=im.crop(box)
    if scale!=1: derived=derived.resize((derived.width*scale,derived.height*scale),Image.Resampling.NEAREST)
    actual=Image.open(BASE/'crops'/name)
    assert actual.size==derived.size and actual.tobytes()==derived.tobytes(),name
    crop_records.append({'file':'crops/'+name,'source':'sources/raw/HC696_original.jpg','bbox_original_px':box,
                         'transform':'native crop' if scale==1 else f'native crop then {scale}x nearest-neighbor pixel replication',
                         'dimensions_px':actual.size,'pixel_equality_to_transform':True,'sha256':sha(BASE/'crops'/name)})
dump(BASE/'OWN_CROP_MANIFEST_v1.json',{'source_sha256':own['source_sha256'],'crops':crop_records})
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
exposure={
    'written_utc':now,
    'own_first_freeze_file_mtime_utc':datetime.datetime.fromtimestamp((BASE/'OWN_SOURCE_FREEZE_v1.json').stat().st_mtime,datetime.timezone.utc).isoformat(),
    'initial_own_exposure':own['exposures'],
    'adoption_receipt_metadata_exposure':'The explicitly permitted adoption receipt also includes fetch receipts (IDs, URLs, dates, bytes and hashes) for HC725 and HC770. No images or actual cipher transcriptions from those cases were accessed.',
    'after_own_seal_before_primary_content':['Primary report directory file names, including E03_W_crossing crop names; no file contents at this listing step.'],
    'primary_content_gate':'Parent reported primary seal complete with expected manifest/ledger hashes; hashes were verified before programmatic comparison.',
    'primary_source_documents_read':['FINDINGS_v1.md','freeze_manifest_v1.json','source_ledger_v1.json','marks_and_layer_events_v1.json','noncipher_ledger_v1.json'],
    'post_comparison_pixel_views':['Own crop postfreeze_r3g4p2_crossing_4x.png','Own crop postfreeze_r3g6_spacing_2x.png'],
    'non_content_notice':'Parent reported that a root program search had run after primary seal. This agent received no search result contents, method details, keys, plaintext or candidate strings.',
    'chronology_limit':'Own first freeze demonstrably predates own primary-ledger reading. No claim is made that it predates every program run elsewhere; own first-freeze mtime is later than primary seal timestamp.',
    'forbidden_exposures':{'root_state_docs':False,'cipher_method_code':False,'key':False,'candidate_or_plaintext':False,'experiments':False,'other_puzzle_cipher_images_or_transcriptions':False},
    'network_calls':0,'root_state_changes':False,'git_actions':False,
}
dump(BASE/'EXPOSURE_v1.json',exposure)
(BASE/'FINDINGS_v1.md').write_text('''# HC696 independent own-reading source audit v1

The independently frozen visible final source agrees with the primary sealed source ledger at **all 180 sites**, in the same six rows and 36 five-site blocks. No letter discrepancy was found. The compact UTF-8 string without newline has SHA-256 `acbd3cdb6d67070b5b9573dab48441b202d738999f71f03d8e1f1ba0aa89bc8d`.

```
CIUSW INBAX ERHPB WPXOQ YKPVA GUSRB
KWXKJ UKILR WBCJW MTYLZ WUSUF CBKDA
UGTKS NKJFS JLZGM MWZWB EKKMN LNAJT
SQMZL JCIMS WIFNE NEQPN SWQRC CPNLM
MQNSD MLWMK ZHKHL ENXJI VKPMW ASSHI
NKDJR ZCWJT BFPNG BQZGP HWZYO EKNCL
```

The five large dark letter overlays agree specifically at C023/R01G05P03=P, C066/R03G02P01=N, C080/R03G04P05=B, C132/R05G03P02=H, and C172/R06G05P02=W. The native final outlines have respectively one upper bowl, two uprights and a descending diagonal, two stacked bowls, two uprights and a midbar, and two low troughs. Neither observer can identify the violet letter hidden underneath any of the five. No restricted underlying alternative set is defensible. Replacement versus reinforcement of the same letter remains unresolved from original pixels alone.

The four underline pairs agree at C005–C006, C011–C012, C101–C102, and C107–C108. The cross-block first underline is preserved as a mark. The I at C150 is directly readable despite extra ink at/below its lower-right serif. The check-like shape, magenta 4, red margin stroke, thin blue vertical stroke below the cipher, mixed-case heading, dashed rule and red heading stroke were inventoried by both observers. The preferred heading text is `Anglický text čís. 7`; diacritic spelling remains tentative and was not used as a crib.

Two inventory omissions in the own first freeze are preserved honestly. A small darker crossing/top irregularity at C077/R03G04P02 was not separately flagged in the initial own ledger. The primary crop filename and later source ledger drew attention to it; a new crop made directly from the original confirms the crossing while the final W remains clear. Whether it is extraneous handwriting or a print irregularity is unresolved; no second alphabetic identity is supported. The enlarged internal gap in row 3 group 6 (`LNA JT`) was also not explicitly recorded initially. A new original crop confirms approximately 80 px pitch at L–N–A, 120 px A–J, and 80 px J–T. The earlier own source-only addendum already retained the row 3 group 5 `EK KMN` gap before primary content was read. Row 2 `WU SUF` and `CBKD A` gaps agree. No letter choice changed after comparison.

All 180 corresponding original-coordinate provenance windows overlap. These are manual occurrence windows, not exact ink boundaries. Different row-height boxes account for vertical-center differences; the own first-pass centers in row 3 group 6 were rough enough to need refinements. The additive post-comparison record provides better native-coordinate windows for that group. This does not silently rewrite the first source freeze. Every crop was verified pixel-for-pixel against a native crop of the original, followed only by stated integer nearest-neighbor replication where used.

The independent own first string, holds and per-site evidence are immutable in `OWN_SOURCE_FREEZE_v1.json`, with their original hashes in `OWN_FREEZE_MANIFEST_v1.json`. `COMPARISON_v1.json` carries all 180 agreement rows, event correspondences, layout/inventory discrepancies and box comparisons. `POST_COMPARISON_SOURCE_ADDENDUM_v1.json` retains additions without changing the initial reading. The input primary manifest/ledger hashes match the parent-supplied seal values.

Actual exposure is recorded in `EXPOSURE_v1.json`. The own first freeze was written at 2026-10-05T15:27:19.970665+00:00, before this agent read any primary ledger contents. Primary source seal time is 2026-10-05T15:23:18.302809+00:00. No claim is made that the own freeze predates every program output elsewhere. A parent notice disclosed only the existence of a root program search; this agent received no method, key, candidate or plaintext contents. The permitted adoption receipt contains fetch receipts for HC725 and HC770; no actual cipher image or transcription from those cases was accessed. No network, Git or root-state action was performed.
''',encoding='utf-8')
(BASE/'SOURCE_SEAL_v1.md').write_text('''# Independent source audit seal v1

SOURCE_SEAL: own first reading frozen before own primary-ledger exposure; source-only comparison complete.

180/180 visible final letter identities agree. Five hidden violet-layer identities remain unresolved. Two own first-freeze mark/layout omissions are recorded additively; no source letter changed after comparison. No method/key/candidate/plaintext content was read.

Original immutable own hashes are retained in OWN_FREEZE_MANIFEST_v1.json. The final source-audit artifact hashes are in AUDIT_MANIFEST_v1.json.
''',encoding='utf-8')
paths=sorted(p for p in BASE.rglob('*') if p.is_file() and p.name not in {'AUDIT_MANIFEST_v1.json','AUDIT_MANIFEST_v1.sha256'})
manifest={'schema':'HC696_independent_source_audit_manifest_v1','sealed_utc':now,'files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size} for p in paths],
          'source_inputs':[{'path':str(ROOT/'sources/raw/HC696_original.jpg'),'sha256':own['source_sha256']},
                           {'path':str(PRIMARY/'freeze_manifest_v1.json'),'sha256':sha(PRIMARY/'freeze_manifest_v1.json')},
                           {'path':str(PRIMARY/'source_ledger_v1.json'),'sha256':sha(PRIMARY/'source_ledger_v1.json')}]}
dump(BASE/'AUDIT_MANIFEST_v1.json',manifest)
(BASE/'AUDIT_MANIFEST_v1.sha256').write_text(sha(BASE/'AUDIT_MANIFEST_v1.json')+'  AUDIT_MANIFEST_v1.json\n',encoding='utf-8')
print(json.dumps({'identity_agreements':180,'letter_discrepancies':0,'earlier_layer_holds':held,'verified_crop_transforms':len(crop_records),
                  'manifest_sha256':sha(BASE/'AUDIT_MANIFEST_v1.json')},indent=2))
