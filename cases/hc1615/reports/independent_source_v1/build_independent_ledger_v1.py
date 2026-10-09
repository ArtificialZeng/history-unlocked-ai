from pathlib import Path
from PIL import Image
import json,hashlib,datetime
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
ROWS=[(750,314,1106,385),(750,385,1106,445),(750,445,1106,501),(750,500,1106,561),(750,560,1106,615),(750,615,1106,682),(750,681,1106,750)]
GROUPS=[
 [['t','3'],['d','h+CARON_LIKE','5','d','4','s','5'],['d','4']],
 [['b','h','5','7','5'],['6'],['f'],['t','2','R_MARK','2']],
 [['m','6'],['c','8','6','t','g','6'],['2','c','d','6']],
 [['d','f','3','7','5'],['f','h','5','8','3','2']],
 [['t','8','3','2','r','3','2'],['b','2','c','2']],
 [['d','4','c','g','m','5'],['f','5','4','m','5']],
 [['d','f','2','7'],['b','5','b','3','2','c']]
]
SHA=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
RGB=lambda im:hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
palette=json.loads((ROOT/'sources/reference_palette/RAW_GRAPHIC_PALETTE_PROVENANCE_v2.json').read_text())
refs={i['raw_shape_mnemonic']:{k:i[k] for k in ['raw_shape_mnemonic','source_line','source_physical_word','local_position_in_preferred_word','atlas_native_xyxy','source_ledger_uncertainty']} for i in palette['items']}
orig=Image.open(ROOT/'sources/raw/HC1615_picture_original.jpg'); upright=orig.transpose(Image.Transpose.ROTATE_90)
ledger={'schema':'HC1615_independent_cold_source_v1','frozen_utc':now,'authority':'Whole native row plus ordinal position; primitive spans are ordered graphical accounting, never exclusive pixel masks.','semantic_exposure':{'key_values':False,'target_plaintext':False,'prior_plaintext':False,'models_or_candidates':False,'primary_preferences_at_freeze':False},'palette_exposure':'Raw prototype atlas/provenance/release note only. Donor palette v2 is explicitly post-donor-inference, broad word contexts and qualified s edge retained. No donor full ciphertext or plaintext read.','source_pins':[],'rows':[],'units':[],'primitives':[],'events':[],'context_events':[{'type':'PRINTED_GREETING','scope':'Picture side two printed blue ordinary-language lines; outside coded body.'},{'type':'HANDWRITTEN_DATE','raw_context':'31. XII. 1901.','scope':'Below coded row 7, outside coded body.'},{'type':'ADDRESS_FACE','scope':'Complete face viewed; ordinary postal/address matter, no additional coded band observed.'}],'grammar':{'unit':'One main body, with clear detached upper mark retained in the same preferred compound graphical unit. No semantic interpretation.','mark':'CARON_LIKE when dark detached downward-pointed v shape; h composition remains opaque; r composition may be called R_MARK solely by donor source prototype correspondence.','gap':'Visible inter-group space, not a guaranteed linguistic word boundary.','punctuation':'Row 4 final comma-like and row 7 final dot preferred punctuation; cipher-role alternatives preserved.','7_shape':'7/y naming variation retained; small upper hook/dot-like detail preferred part of recurring 7-like body rather than an additional unit/mark.','alternatives_global':['All inferred mnemonic identities are graphical proposals, not historical alphabet facts.','All connectors may have pen-stroke ambiguity; no exclusive connected-component partition claimed.','Punctuation could instead be encoded opaque marks; that alternative was not run.','Detached carons could be independent graphical events; preferred compound role is frozen without value.']}}
for rel in ['sources/raw/HC1615_picture_original.jpg','sources/raw/HC1615_address_original.jpg','sources/raw/HC1615_API_detail.response','sources/provenance/HC1615_picture.receipt.json','sources/provenance/HC1615_address.receipt.json','sources/provenance/HC1615_API.receipt.json','sources/reference_palette/RAW_GRAPHIC_MNEMONIC_ATLAS_v2.png','sources/reference_palette/RAW_GRAPHIC_PALETTE_PROVENANCE_v2.json','sources/reference_palette/SOURCE_ONLY_RELEASE_NOTE_v2.md']:
 p=ROOT/rel; pin={'path':str(p),'sha256':SHA(p),'bytes':p.stat().st_size}
 if p.suffix.lower() in ['.jpg','.png']:
  im=Image.open(p);pin.update(native_dimensions=list(im.size),RGB_sha256=RGB(im))
 ledger['source_pins'].append(pin)
uid=pid=eid=0
for rn,groups in enumerate(GROUPS,1):
 b=ROWS[rn-1]; crop=upright.crop(b); saved=Image.open(OUT/f'row_{rn:02d}_native.png')
 assert saved.size==crop.size and saved.tobytes()==crop.tobytes()
 row={'row':rn,'upright_box_xyxy':list(b),'original_box_xyxy':[1785-b[3],b[0],1785-b[1],b[2]],'native_RGB_size':list(crop.size),'native_RGB_sha256':RGB(crop),'crop_path':f'row_{rn:02d}_native.png','actual_viewed':True,'units':[],'physical_groups':[],'preferred_main_body_count':sum(map(len,groups)),'notes':'Foreground ink traceable across gray watermark; no cleanup, no per-glyph masks.'}
 ordinal=0
 for gn,tokens in enumerate(groups,1):
  gr={'group':gn,'unit_ids':[],'literal_gap_after':'VISIBLE_SPACE' if gn<len(groups) else None}
  for local,label in enumerate(tokens,1):
   uid+=1;ordinal+=1;pid+=1; unit_id=f'U{uid:03d}'; base='h' if label=='h+CARON_LIKE' else ('r' if label=='R_MARK' else label)
   prim=[f'P{pid:03d}'];ledger['primitives'].append({'id':prim[0],'row':rn,'main_body_ordinal':ordinal,'role':'MAIN_BODY','shape':base,'unit':unit_id})
   mark='CARON_LIKE' if label in ['h+CARON_LIKE','R_MARK'] else None
   if mark:
    pid+=1; prim.append(f'P{pid:03d}');ledger['primitives'].append({'id':prim[-1],'row':rn,'main_body_ordinal':ordinal,'role':'DETACHED_UPPER_MARK','shape':mark,'unit':unit_id,'association':'Over this base body, preferred adjunct; independent mark-event alternative retained.'})
   refkey='r+CARON_LIKE' if label=='R_MARK' else base
   u={'id':unit_id,'row':rn,'row_ordinal':ordinal,'physical_group':gn,'group_local_ordinal':local,'preferred_raw_unit':label,'base_shape':base,'literal_mark':mark,'primitive_span':prim,'source_authority':{'raw_file':'sources/raw/HC1615_picture_original.jpg','row_native_crop':row['crop_path'],'ordinal':ordinal,'exclusive_mask':False},'confidence':'high' if label not in ['h+CARON_LIKE','s','r'] else 'medium','prototype':refs.get(refkey),'alternatives':[],'notes':[]}
   if base=='d':u['alternatives'].append({'raw_unit':'a-like','reason':'Cursive d/a visual naming alternative, ascender favors donor d class.'})
   if base=='7':u['alternatives'].append({'raw_unit':'y-like','reason':'Same recurring 7/y-like body, not a semantic alias.'});u['notes'].append('Upper hook/dot-like detail retained within body; separate tiny-mark role remains possible but not preferred.')
   if base=='4':u['notes'].append('Angular 4-like body may be more triangular/open in some positions; shape retained, not normalized from meaning.')
   if base=='r' and label!='R_MARK':u['alternatives'].append({'raw_unit':'n-like','reason':'Small single hooked/shoulder shape; raw r prototype favored.'})
   if label=='s':u['alternatives'].append({'raw_unit':'4-like','reason':'Small triangular/open body; donor s prototype favors s, donor s edge is explicitly qualified.'})
   if label=='h+CARON_LIKE':u['alternatives'] += [{'raw_unit':'h+HAT_LIKE','reason':'Fine upper strokes; downward v is preferred.'},{'raw_unit':'h plus independent CARON_EVENT','reason':'Compound-vs-event role is not independently known.'}];u['notes'].append('Visible detached caron over h-like base, not bare h; no permitted compound prototype/semantic value established. Keep opaque.')
   if label=='R_MARK':u['alternatives'].append({'raw_unit':'r plus independent CARON_EVENT','reason':'Unit composition remains a hypothesis.'});u['notes'].append('Explicit donor atlas r+CARON_LIKE L3W9 local3 matches base and detached v. R_MARK is a graphical class only; no value read.')
   ledger['units'].append(u);row['units'].append(unit_id);gr['unit_ids'].append(unit_id)
   eid+=1;ledger['events'].append({'id':f'E{eid:03d}','type':'UNIT','row':rn,'unit_id':unit_id,'primitive_span':prim})
  row['physical_groups'].append(gr)
  if gn<len(groups):
   eid+=1;ledger['events'].append({'id':f'E{eid:03d}','type':'VISIBLE_SPACE','row':rn,'after_group':gn,'preferred_role':'formatting_gap','alternative':'Spacing may be nonlinguistic.'})
 if rn in [4,7]:
  pid+=1;punct='COMMA_LIKE' if rn==4 else 'DOT_LIKE';pr=f'P{pid:03d}'
  ledger['primitives'].append({'id':pr,'row':rn,'role':'PUNCTUATION','shape':punct,'after_main_body_ordinal':ordinal})
  eid+=1;ledger['events'].append({'id':f'E{eid:03d}','type':'PUNCTUATION','row':rn,'shape':punct,'primitive_span':[pr],'preferred_role':'punctuation','alternative':'opaque_encoded_unit_unrun'})
 if rn<7:
  eid+=1;ledger['events'].append({'id':f'E{eid:03d}','type':'ROW_BREAK','row':rn,'next_row':rn+1})
 ledger['rows'].append(row)
ledger['counts']={'units':len(ledger['units']),'main_body_primitives':77,'detached_mark_primitives':2,'punctuation_primitives':2,'primitives':len(ledger['primitives']),'rows':7,'physical_groups':sum(map(len,GROUPS)),'space_events':11,'row_break_events':6,'punctuation_events':2,'ordered_events':len(ledger['events']),'uncertainty_preserved':True,'counts_are_for_frozen_preferred_grammar_not_unique_historical_truth':True}
assert ledger['counts']['units']==77 and ledger['counts']['primitives']==81 and ledger['counts']['ordered_events']==96
flatten=[p for u in ledger['units'] for p in u['primitive_span']]+[e['primitive_span'][0] for e in ledger['events'] if e['type']=='PUNCTUATION']
assert len(flatten)==len(set(flatten))==81 and set(flatten)=={p['id'] for p in ledger['primitives']}
(OUT/'INDEPENDENT_COLD_SOURCE_LEDGER_v1.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
receipt={'freeze_utc':now,'actual_native_views':['sources/raw/HC1615_picture_original.jpg','sources/raw/HC1615_address_original.jpg','reports/independent_source_v1/picture_complete_native90ccw.png']+[f'reports/independent_source_v1/row_{i:02d}_native.png' for i in range(1,8)]+['sources/reference_palette/RAW_GRAPHIC_MNEMONIC_ATLAS_v2.png'],'tool':'tools.view_image detail original; all emitted as images','source_only':True,'primary_preferences_seen':False,'source_KEY_P_models_seen':False,'native_rgb_replay_all_7':True,'complete_both_faces_viewed':True,'rotation':'PIL integer ROTATE_90 counterclockwise, no filtering/cleanup/resampling','image_box_policy':'Whole row boxes and ordinal authority, never exclusive unit masks.','read_instructions':['AGENTS.md','README.md','RESEARCH_PROTOCOL_v1.md','PROJECT_STATE.json','config/REGISTRATION_v1.json'],'read_errors':'Initially requested wrong protocol/registration filenames, both missing; corrected to README-defined names. No other artifacts exposed.'}
(OUT/'ACTUAL_VIEW_AND_EXPOSURE_RECEIPT_v1.json').write_text(json.dumps(receipt,indent=2)+'\n')
report='''# HC1615 independent cold source freeze v1\n\nOwn preferences are frozen before primary-ledger access and before target lookup. I read no semantic dictionary values, old/current plaintext, solver, candidate, model, HC1617 body, or HC1519 target. The permitted limited raw prototype palette was actually viewed; its post-donor-inference and broad-context/qualified-edge status is retained. Both full native target faces, upright full picture and every whole native row were actually viewed.\n\nThe preferred source grammar has **77 graphical units**, seven rows, 18 visible groups, 81 accounted primitives, two detached upper marks, two punctuation primitives, 11 visible spaces, six row breaks, and 96 ordered unit/format/punctuation events. It is a frozen graphical proposal, not unique historical truth. Every preferred unit has native-row/ordinal provenance, primitive-span accounting and retained alternatives. All seven crop RGB payloads replay exactly.\n\nThe row-1 fourth main body is **h+CARON_LIKE**, with visible detached upper v shape; it is not bare h and remains an opaque compound. Row-2 tenth body is **R_MARK**, based solely on explicit source-correspondence to donor atlas r+CARON_LIKE at L3W9/local3. No meaning is known. Alternative separate mark-event roles are retained. Recurring 7/y-like upper hook/dot details are preferred part of the base body, with the alternative tiny-mark interpretation stated.\n\nSmall row-1 s-like form retains a 4-like alternative, all d-like forms retain a cursive a-like alternative, and bare r retains n-like naming uncertainty. Row-4 comma and row-7 dot are preferred punctuation with opaque cipher-role alternatives. Physical spaces are formatting evidence, not inferred linguistic word boundaries.\n\nThe gray watermark collides with text but no complete row is lost. Native foreground strokes remain visible; no cleanup, exact glyph mask or inferred-language correction was used. Complete source audit is still pending comparison to the separately sealed primary ledger; timing alone does not pass a gate.\n'''
(OUT/'INDEPENDENT_SOURCE_REPORT_v1.md').write_text(report)
manifest={'frozen_utc':now,'stage':'COLD_INDEPENDENT_PREFERENCES_BEFORE_PRIMARY','files':[]}
for p in sorted(OUT.rglob('*')):
 if p.is_file() and p.name not in ['INDEPENDENT_SOURCE_MANIFEST_v1.json','INDEPENDENT_SOURCE_SEAL_v1.json']:
  item={'path':str(p.relative_to(OUT)),'sha256':SHA(p),'bytes':p.stat().st_size}
  if p.suffix=='.png':item['RGB_sha256']=RGB(Image.open(p))
  manifest['files'].append(item)
(OUT/'INDEPENDENT_SOURCE_MANIFEST_v1.json').write_text(json.dumps(manifest,indent=2)+'\n')
seal={'frozen_utc':now,'ledger_sha256':SHA(OUT/'INDEPENDENT_COLD_SOURCE_LEDGER_v1.json'),'manifest_sha256':SHA(OUT/'INDEPENDENT_SOURCE_MANIFEST_v1.json'),'primary_preferences_seen':False,'semantic_values_seen':False}
(OUT/'INDEPENDENT_SOURCE_SEAL_v1.json').write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps(seal));print(ledger['counts'])
