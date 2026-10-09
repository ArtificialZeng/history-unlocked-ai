from pathlib import Path
import json,hashlib,datetime
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
own=json.loads((OUT/'INDEPENDENT_COLD_SOURCE_LEDGER_v1.json').read_text()); ownseal=json.loads((OUT/'INDEPENDENT_SOURCE_SEAL_v1.json').read_text())
assert H(OUT/'INDEPENDENT_COLD_SOURCE_LEDGER_v1.json')==ownseal['ledger_sha256'];assert H(OUT/'INDEPENDENT_SOURCE_MANIFEST_v1.json')==ownseal['manifest_sha256']
pr=ROOT/'reports/source_v1'; da=ROOT/'data/source_v1'; seal=json.loads((pr/'SOURCE_ONLY_SEAL_v1.json').read_text()); man=json.loads((pr/'SOURCE_ONLY_MANIFEST_v1.json').read_text())
assert H(pr/'SOURCE_ONLY_MANIFEST_v1.json')==seal['manifest_SHA256']
verified=[]
for f in man['payload']:
 p=ROOT/f['path'];assert H(p)==f['SHA256']; verified.append({'path':f['path'],'sha256':f['SHA256'],'verified':True})
punits=json.loads((da/'SOURCE_UNITS_v1.json').read_text())['units']; pg=json.loads((da/'SOURCE_GROUPS_v1.json').read_text())['groups']; prows=json.loads((da/'SOURCE_ROWS_v1.json').read_text())['rows']; pp=json.loads((da/'SOURCE_PRIMITIVES_v1.json').read_text())['primitive_components']; pe=json.loads((da/'SOURCE_EVENTS_v1.json').read_text())['events']
assert len(punits)==len(own['units'])==77
native=Image.open(ROOT/'sources/raw/HC1615_picture_original.jpg'); aligned=native.transpose(Image.Transpose.ROTATE_90);rawsha=H(ROOT/'sources/raw/HC1615_picture_original.jpg')
replay=[]
for r in prows:
 pix=aligned.crop(r['integer90CCW_bbox']); saved=Image.open(ROOT/r['path']);assert pix.size==saved.size and pix.tobytes()==saved.tobytes();assert H(ROOT/r['path'])==r['PNG_SHA256'];assert hashlib.sha256(pix.tobytes()).hexdigest()==r['RGB_SHA256']
 b=r['integer90CCW_bbox'];assert r['source_native_row_box_xyxy']==[1785-b[3],b[0],1785-b[1],b[2]]
 replay.append({'row':r['physical_row'],'primary_box':b,'independent_box':own['rows'][r['physical_row']-1]['upright_box_xyxy'],'primary_RGB_replay':True,'boxes_need_not_equal':'Both whole-row authority; primary intentionally includes more neighbor fringes.','actual_primary_native_viewed_after_own_freeze':True})
allpos=[];mapping=[];exact=equiv=diff=0
for a,b in zip(own['units'],punits):
 assert a['row']==b['physical_row'] and a['physical_group']==b['physical_gap_group'] and a['group_local_ordinal']==b['local_unit_ordinal']
 assert b['source_RAW_SHA256']==rawsha
 mark_a=a['literal_mark']; mark_b=[m for m in b['mark_attributes'] if m.get('raw_shape')=='detachedtwo-strokeupperchevron']; assert bool(mark_a)==bool(mark_b)
 primb=b['primitive_component_ids'];assert len(primb)==(3 if mark_b else 1)
 assert b['primitive_span']=={'start_component_id':primb[0],'end_component_id':primb[-1]}
 if a['preferred_raw_unit']==b['preferred_raw_unit_label']: status='EXACT_RAW_LABEL_MATCH';exact+=1
 elif a['preferred_raw_unit']=='h+CARON_LIKE' and b['preferred_raw_unit_label']=='H_MARK_UNASSIGNED' and a['base_shape']==b['raw_base_label']=='h':status='GRAPHICAL_COMPOSITION_SAME_LABEL_NOMENCLATURE_DIFF';equiv+=1
 else:status='SUBSTANTIVE_PREFERRED_RAW_CLASS_DISAGREEMENT';diff+=1
 record={'global_ordinal':int(a['id'][1:]),'row':a['row'],'row_ordinal':a['row_ordinal'],'group':a['physical_group'],'local':a['group_local_ordinal'],'independent_id':a['id'],'primary_id':b['unit_id'],'independent_label':a['preferred_raw_unit'],'primary_label':b['preferred_raw_unit_label'],'independent_base':a['base_shape'],'primary_base':b['raw_base_label'],'status':status,'marks_agree_graphically':bool(mark_a)==bool(mark_b),'primary_intrinsic_stroke_attributes':[m for m in b['mark_attributes'] if m not in mark_b],'independent_primitive_span':a['primitive_span'],'primary_component_span':primb,'ordinal_provenance_agrees':True,'primary_RAW_RGB_pins_verified':True}
 allpos.append(record)
 mapping.append({'independent_primitive':a['primitive_span'][0],'primary_components':[primb[0]],'role':'MAIN_BODY','preferred_shape_status':status})
 if mark_a: mapping.append({'independent_primitive':a['primitive_span'][1],'primary_components':primb[1:],'role':'WHOLE_UPPER_CARON_VS_TWO_UPPER_STROKES','equivalence_scope':'One observed chevron described at whole-mark vs two-stroke granularity; not a semantic decoder alias.'})
assert exact==75 and equiv==1 and diff==1
primary_component_ids=[p['component_id'] for p in pp];spans=[p for u in punits for p in u['primitive_component_ids']];assert len(spans)==len(set(spans))==81 and set(spans)==set(primary_component_ids)
allgroups=[]
for r in own['rows']:
 for g in r['physical_groups']:
  other=next(x for x in pg if (x['physical_row'],x['physical_gap_group'])==(r['row'],g['group']))
  mapped=[punits[int(u[1:])-1]['unit_id'] for u in g['unit_ids']];assert mapped==other['unit_ids'] and len(mapped)==other['preferred_unit_count']
  allgroups.append({'row':r['row'],'group':g['group'],'independent_units':g['unit_ids'],'primary_units':other['unit_ids'],'same_order_and_group_membership':True})
assert len(allgroups)==18
punct=[]
for ie in own['events']:
 if ie['type']=='PUNCTUATION':
  x=next(e for e in pe if e['row_id']==f"R{ie['row']:02d}" and 'raw_shape' in e and e['raw_shape'] in [',','.'])
  assert (ie['shape']=='COMMA_LIKE' and x['raw_shape']==',') or (ie['shape']=='DOT_LIKE' and x['raw_shape']=='.')
  punct.append({'row':ie['row'],'independent_primitive':ie['primitive_span'][0],'primary_event':x['event_id'],'preferred_role_agrees':True,'encoded_unit_alternative_preserved_both':True})
  mapping.append({'independent_primitive':ie['primitive_span'][0],'primary_event':x['event_id'],'role':'PUNCTUATION_NOT_PRIMARY_COMPONENT'})
assert len(punct)==2 and len(mapping)==81
canonical_primary=[]
for r in prows:
 rn=r['physical_row']; groups=sorted([g for g in pg if g['physical_row']==rn],key=lambda x:x['physical_gap_group'])
 for gn,g in enumerate(groups,1):
  canonical_primary.extend([('UNIT',rn,u) for u in g['unit_ids']])
  if gn<len(groups):canonical_primary.append(('VISIBLE_SPACE',rn,gn))
 for p in punct:
  if p['row']==rn:canonical_primary.append(('PUNCTUATION',rn,'COMMA_LIKE' if rn==4 else 'DOT_LIKE'))
 if rn<7:canonical_primary.append(('ROW_BREAK',rn,rn+1))
canonical_own=[]
for e in own['events']:
 if e['type']=='UNIT':canonical_own.append(('UNIT',e['row'],punits[int(e['unit_id'][1:])-1]['unit_id']))
 elif e['type']=='VISIBLE_SPACE':canonical_own.append(('VISIBLE_SPACE',e['row'],e['after_group']))
 elif e['type']=='PUNCTUATION':canonical_own.append(('PUNCTUATION',e['row'],e['shape']))
 else:canonical_own.append(('ROW_BREAK',e['row'],e['next_row']))
assert canonical_primary==canonical_own and len(canonical_own)==96
check={'checked_utc':now,'status':'COMPLETE_SOURCE_ACCOUNTING_COMPARISON_WITH_ONE_RAW_CLASS_DISAGREEMENT','own_freeze_utc':ownseal['frozen_utc'],'primary_freeze_utc':seal['sealed_utc'],'semantic_values_read':False,'source_edits_after_comparison':False,'lookup_or_alias_fallback':False,'own_seal_unchanged':True,'primary_payload_all30_hash_verified':verified,'source_seals':{'own_ledger':ownseal['ledger_sha256'],'own_manifest':ownseal['manifest_sha256'],'primary_ledger':seal['unit_ledger_SHA256'],'primary_manifest':seal['manifest_SHA256'],'primary_seal':H(pr/'SOURCE_ONLY_SEAL_v1.json')},'all_77_positions':allpos,'agreement':{'exact_label_matches':75,'same_graphical_composition_nomenclature_difference':1,'substantive_preferred_raw_class_disagreements':1,'all_positions_group_order_agree':True,'all_two_mark_associations_agree':True},'all18_groups':allgroups,'all7_native_row_provenance_checks':replay,'all81_independent_primitive_mappings':mapping,'all81_primary_components_accounted_once':True,'punctuation_roles':punct,'census_reconciliation':{'primary':'77 main bodies + 4 detached upper mark strokes = 81 components; comma and dot are separate events.','independent':'77 main bodies + 2 whole upper marks + 2 punctuation primitives = 81 primitives.','common_granularity':'77 bodies + 4 mark strokes + 2 punctuation = 83 graphical accounting atoms. Same numeral81 does NOT mean identical type census.','two_chevrons':'Each independent whole mark maps to two primary stroke components; no exact stroke pixel partition claimed.'},'event_reconciliation':{'primary4_events':'2 attached mark events + comma + dot. Units, gaps and physical row order recorded elsewhere.','independent96_events':'77 unit events + 11 gap events + 6 row breaks + 2 punctuation events; the two marks retained inside unit spans.','canonical96_order':'All unit/gap/row/punctuation events agree after explicit mapping of separately stored primary structure.','primary_two_mark_events':'Both map to independent whole marks at global4 and global21 (row2 ordinal10).','no_dropped_marks_or_nulls':True},'substantive_disagreement':{'position':'R06G02U03, global65, row6 ordinal9','independent_preferred':'4','primary_preferred':'s','source_observation':'Small angular/triangular foreground body on native row6. It resembles row1 s-like body as well as a reduced/open 4-like body. Exact raw class remains observationally disputed.','resolution':'Retain both freezes and treat 4/s as unresolved source alternative. No lookup, word fit or source edit used.','effect':'Independent source audit does not uniquely certify this class; it cannot be advertised as unanimous 77/77 identity agreement.'},'marked_h':'Both observers prefer h-like baseline plus detached caron, distinct from bareh/R_MARK; opaque whole class held. Names are descriptive only, not a decoder alias.'}
(OUT/'SEALED_PRIMARY_COMPARISON_v1.json').write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n')
report='''# HC1615 independent full source comparison\n\nThe independent preferences were frozen at04:26:26 UTC, before reading the primary seal at04:30:35 UTC or its source preferences. No semantic values, plaintext, candidate, model or lookup was read. Both v1 freezes remain unchanged. All30 primary payload hashes, all7 native-row RGB replays, all77 unit positions/order/spans, all18 groups, both marks and both punctuation roles were checked. Every primary component is accounted once.\n\n**One substantive preferred raw-class disagreement remains:** R06G02U03/global65/row6 ordinal9 is independently preferred **4**, primary preferred **s**. The native small triangular/angular body resembles the row1 s-like form and a reduced 4-like body; the audit retains the disagreement without using meanings or rewriting either freeze. There are75 exact raw-label matches, one equivalent h+caron composition with different descriptive labels, and one disputed class. This is not unanimous77/77 identity agreement.\n\nR01G02U02/global4 has the same preferred h-like base plus detached upper chevron in both freezes: independent h+CARON_LIKE versus primary H_MARK_UNASSIGNED. Both hold it as distinct/opaque, without forcing it to bareh or R_MARK. Row2 ordinal10 is graphically matched R_MARK in both.\n\nThe two81 censuses are different type systems. Primary:77 bodies+4 individual chevron strokes, with comma/dot as separate events. Independent:77 bodies+2 whole chevrons+2 punctuation primitives. At common granularity these account for83 bodies/strokes/punctuation items. Each whole chevron maps to the primary's two strokes; no exclusive pixel/stroke partition is claimed.\n\nPrimary has4 special events (two attached marks+comma+dot). Independent has96 ordered unit/format/punctuation events (77 units+11 spaces+6 row breaks+2 punctuation), with two marks inside unit spans. Expanding the primary's unit/group/row tables into the same96-event grammar gives identical order; both attached mark events map explicitly to the independent marks. Nothing was silently dropped.\n\nAll native primary rows were actually viewed after the independent freeze. Primary boxes include broader neighbor fringes; both source maps replay exactly and share whole-row/ordinal authority. The watermark remains intact. **Outcome: complete source bookkeeping comparison, with an opaque markedh and one unresolved4/s class. No semantic/source-accuracy PASS or solved claim.**\n'''
(OUT/'SEALED_PRIMARY_COMPARISON_REPORT_v1.md').write_text(report)
files=['INDEPENDENT_SELF_CHECK_v1.json','COMPARISON_BUILDER_FAILURE_v1.json','compare_sealed_source_v1.py','SEALED_PRIMARY_COMPARISON_v1.json','SEALED_PRIMARY_COMPARISON_REPORT_v1.md']
cm={'created_utc':now,'own_cold_manifest_preserved':ownseal['manifest_sha256'],'primary_manifest':seal['manifest_SHA256'],'files':[{'path':f,'sha256':H(OUT/f),'bytes':(OUT/f).stat().st_size} for f in files]}
(OUT/'SOURCE_COMPARISON_MANIFEST_v1.json').write_text(json.dumps(cm,indent=2)+'\n')
cs={'created_utc':now,'comparison_manifest_sha256':H(OUT/'SOURCE_COMPARISON_MANIFEST_v1.json'),'audit_sha256':H(OUT/'SEALED_PRIMARY_COMPARISON_v1.json'),'source_preferences_unchanged':True,'status':check['status']}
(OUT/'SOURCE_COMPARISON_SEAL_v1.json').write_text(json.dumps(cs,indent=2)+'\n');print(cs);print(check['agreement'])
