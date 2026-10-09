#!/usr/bin/env python3
"""HC1615 manual-source replay only. No key/OCR/decoder/model/language imports."""
from pathlib import Path
from PIL import Image
import json,re,hashlib,datetime,collections
P=Path(__file__).resolve().parents[2];D=P/'data/source_v1';R=P/'reports/source_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def tokens(s):return re.findall(r'\{[^}]+\}|[a-z0-9]|[^\w\s]',s)
rawp=P/'sources/raw/HC1615_picture_original.jpg';raw=Image.open(rawp).convert('RGB');rawsha=sha(rawp)
m=json.loads((D/'MANUAL_PREFERRED_RAW_UNITS_v1.json').read_text());rp=json.loads((R/'ROW_CROP_PROVENANCE_v1.json').read_text())['rows'];units=[];comps=[];groups=[];rows=[];events=[];counter=0
for ri,row in enumerate(m['rows'],1):
 prov=rp[ri-1];assert Image.open(P/prov['path']).convert('RGB').tobytes()==raw.crop(prov['source_native_row_box_xyxy']).transpose(Image.Transpose.ROTATE_90).tobytes();rids=[];rc=0
 rows.append(dict(prov,preferred_raw_format=' '.join(row['groups']),row_order=ri,reading_direction='left-to-right/top-to-bottom preferredphysicalorder',unit_ids=rids))
 for gi,text in enumerate(row['groups'],1):
  gid=f'R{ri:02d}G{gi:02d}';uids=[];li=0;labels=[]
  for atom in tokens(text):
   if atom in ',.':events.append({'event_id':f'{gid}E{len(events)+1:02d}','row_id':row['row_id'],'group_id':gid,'after_local_unit_ordinal':li,'raw_shape':atom,'preferred_role':'comma/terminalpunctuation','alternative_role':'cipherformat/unitrole notsemanticallyinterpreted','native_row_crop':prov['path'],'source_native_row_box_xyxy':prov['source_native_row_box_xyxy'],'row_PNG_SHA256':prov['PNG_SHA256'],'row_RGB_SHA256':prov['RGB_SHA256']});continue
   marked=atom.startswith('{');label=atom[1:-1] if marked else atom;base=('h' if label=='H_MARK_UNASSIGNED' else 'r') if marked else label;li+=1;counter+=1;rc+=1;uid=f'{gid}U{li:02d}';cid=f'{gid}C{li:02d}';rids.append(uid);uids.append(uid);labels.append(label);span=[cid];markattrs=[];alts=[]
   core={'component_id':cid,'unit_id':uid,'row_id':row['row_id'],'group_id':gid,'local_base_ordinal':li,'raw_graphic_component':base+'-like baselinecore','role':'baselineprimitive inpreferredunit','native_row_crop':prov['path'],'source_native_row_box_xyxy':prov['source_native_row_box_xyxy'],'row_RGB_SHA256':prov['RGB_SHA256']}
   comps.append(core)
   if marked:
    markattrs=[{'raw_shape':'detachedtwo-strokeupperchevron','literal_source_type':'CARON_LIKE shape only','stroke_components':['leftshortstroke','rightshortstroke'],'preferred_association':'sameunitbaselinecore, wholegraph keptdistinct frombarebase','semantic_role':None,'known_raw_prototype_match':label=='R_MARK'}]
    for j,shape in enumerate(['leftupperstroke','rightupperstroke'],1):
     mid=f'{gid}C{li:02d}M{j:02d}';span.append(mid);comps.append({'component_id':mid,'unit_id':uid,'row_id':row['row_id'],'group_id':gid,'raw_graphic_component':shape,'role':'uppermarkstroke; notindependentcipherletter inpreferredgrammar','native_row_crop':prov['path'],'source_native_row_box_xyxy':prov['source_native_row_box_xyxy'],'row_RGB_SHA256':prov['RGB_SHA256']})
    alts=['markindependentfrombase vsonecompositeunit','newmarkedfontclass ifdonorgraphicidentityunsupported']
    if label=='H_MARK_UNASSIGNED':alts.insert(0,'R_MARK/corevariant graphicalalternative held, notforced')
    events.append({'event_id':uid+'_MARK','row_id':row['row_id'],'group_id':gid,'associated_unit_id':uid,'raw_shape':'detachedtwo-strokeupperchevron','primitive_component_ids':span[1:],'preferred_role':'unitattachedgraphmark','semantic_role':None,'source_native_row_box_xyxy':prov['source_native_row_box_xyxy'],'native_row_crop':prov['path'],'row_RGB_SHA256':prov['RGB_SHA256']})
   elif base=='r':markattrs=[{'raw_shape':'small upperentry/hook near rcore','preferred_association':'intrinsicbaseentrystroke','alternative':'uppermarkroleheld; no clearlydetachedchevron assigned','semantic_role':None}]
   if base in ['m','n']:alts.append('cursive entry/exit humps confusable; preferredcurrentoutline retained')
   u={'unit_id':uid,'occurrence_id':uid,'global_preferred_unit_ordinal':counter,'row_id':row['row_id'],'physical_row':ri,'group_id':gid,'physical_gap_group':gi,'local_unit_ordinal':li,'raw_base_label':base,'raw_label':label,'preferred_raw_unit_label':label,'primitive_component_ids':span,'primitive_span':{'start_component_id':span[0],'end_component_id':span[-1]},'mark_attributes':markattrs,'visual_alternatives':alts,'confidence':'preferredvisiblecurrentoutline; markedclass/grammar alternatives explicit','current_layer':'visiblecurrentblackink','earlier_layer':None,'earlier_layer_status':'unknown, no inventedolderletters','source_RAW_SHA256':rawsha,'source_native_row_box_xyxy':prov['source_native_row_box_xyxy'],'aligned_row_box_xyxy':prov['integer90CCW_bbox'],'native_row_crop':prov['path'],'row_PNG_SHA256':prov['PNG_SHA256'],'row_RGB_SHA256':prov['RGB_SHA256'],'provenance_precision':'FullnativeROW authority plusgroup/localordinal, notexclusiveglyphmask/wordbox'};units.append(u)
  joins=[]
  for j in range(len(labels)-1):
   pair=labels[j]+labels[j+1]
   if pair in ['bh','fh']:joins.append({'unit_ids':uids[j:j+2],'raw_primitive_labels':pair,'preferred_units':2,'alternative':'onecompoundunit ifindependentgraphicalsourcegrammar later supports; no key/wordchoice'})
  groups.append({'group_id':gid,'physical_row':ri,'physical_gap_group':gi,'raw_preferred_display':text,'unit_ids':uids,'preferred_unit_count':len(uids),'join_or_composite_holds':joins,'native_row_crop':prov['path'],'source_native_row_box_xyxy':prov['source_native_row_box_xyxy'],'row_RGB_SHA256':prov['RGB_SHA256'],'boundary_basis':'visiblelargerphysicalgap, notsemanticwordboundary'})
 rows[-1]['preferred_row_unit_count']=rc
put(D/'SOURCE_UNITS_v1.json',{'units':units,'preferred_unit_count':len(units),'row_unit_counts':[r['preferred_row_unit_count'] for r in rows],'preferred_unitgrammar':'eachbaselineglyphcore oneunit; two markedcore+detachedchevron compositions eachoneunit; fourupperstrokes preservedascomponents','unique_historical_unit_count':None,'semantic_values_seen':False})
put(D/'SOURCE_PRIMITIVES_v1.json',{'primitive_components':comps,'base_primitives':len(units),'detached_mark_stroke_primitives':4,'totalpreferred_components':len(comps)})
put(D/'SOURCE_GROUPS_v1.json',{'groups':groups,'group_count':len(groups)})
put(D/'SOURCE_ROWS_v1.json',{'rows':rows,'row_count':7,'ordinaryprintedgreeting_date_address_excluded':True})
put(D/'SOURCE_EVENTS_v1.json',{'events':events,'raw_format_rows':[r['preferred_raw_format'] for r in rows],'allgaps_physicalrows_markprimitives_comma_period_preserved':True})
put(D/'SOURCE_CLASSES_v1.json',{'preferred_rawunit_counts':dict(sorted(collections.Counter(u['raw_label'] for u in units).items())),'no26alphabetforcing':True,'distinctmarkedclasses':['R_MARK','H_MARK_UNASSIGNED'],'marks_meaning_withheld':True,'one_sourceclass_unassigned_to_knownpalette':True})
put(D/'SOURCE_PIXEL_REPLAY_v1.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'all7nativefullROW_RGB_raw90CCW_replay':True,'allunits_component_spans_rowsourcepins':True,'preferred_units':len(units),'primitive_components':len(comps),'no_key_decoder_P_model_read':True,'source_identity_or_semantic_uniqueproof':False})
print({'units':len(units),'rows':[r['preferred_row_unit_count'] for r in rows],'components':len(comps),'groups':len(groups),'events':len(events)})
