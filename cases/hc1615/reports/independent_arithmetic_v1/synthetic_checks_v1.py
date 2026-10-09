#!/usr/bin/env python3
"""Neutral toy fixtures only. No historical source/key/candidate file is opened."""
import copy,datetime,json
from pathlib import Path
import check_certificate_independent_v1 as a

def fixture():
    key={'X':'a','Y':'b','XY_MARK':'ab'}; pins={'SYNTHETIC_SOURCE_ONLY':'a'*64}; donor='b'*64
    rows=[]
    for i in (1,2):
        rows.append({'row_id':f'TOY_R{i}','physical_row':i,'row_order':i,'path':f'SYNTHETIC_ROW_{i}.png','source_native_row_box_xyxy':[i,0,i+1,1],'PNG_SHA256':str(i)*64,'RGB_SHA256':str(i+2)*64,'unit_ids':[],'preferred_row_unit_count':0})
    labels=[(1,1,'X',1),(1,1,'Y',1),(1,1,'XY_MARK',2),(1,2,'SYNTHETIC_UNKNOWN',1),(2,1,'Y',1),(2,1,'X',1)]
    us=[];ps=[];gs=[];local={};groupkeys=[]
    for ordinal,(rownum,gnum,label,nprim) in enumerate(labels,1):
        row=rows[rownum-1];gid=f'TOY_R{rownum}G{gnum}'
        if gid not in groupkeys:groupkeys.append(gid)
        local[gid]=local.get(gid,0)+1;uid=f'{gid}U{local[gid]}'
        pids=[f'{uid}P{j+1}' for j in range(nprim)]
        marks=[{'raw_shape':'SYNTHETIC detached mark','preferred_association':'toy unit','alternative':'toy unresolved role','role':'synthetic only'}] if ordinal in (3,5) else []
        us.append({'unit_id':uid,'global_preferred_unit_ordinal':ordinal,'row_id':row['row_id'],'physical_row':rownum,'group_id':gid,'local_unit_ordinal':local[gid],'preferred_raw_unit_label':label,'mark_attributes':marks,'primitive_component_ids':pids,'primitive_span':{'start_component_id':pids[0],'end_component_id':pids[-1]},'native_row_crop':row['path'],'source_native_row_box_xyxy':row['source_native_row_box_xyxy'],'row_PNG_SHA256':row['PNG_SHA256'],'row_RGB_SHA256':row['RGB_SHA256']})
        for pid in pids:ps.append({'component_id':pid,'unit_id':uid,'row_id':row['row_id'],'group_id':gid,'whole_native_row_source':row['path'],'source_native_row_box_xyxy':row['source_native_row_box_xyxy'],'row_RGB_SHA256':row['RGB_SHA256']})
        row['unit_ids'].append(uid);row['preferred_row_unit_count']+=1
    for gid in groupkeys:
        members=[u for u in us if u['group_id']==gid];row=rows[members[0]['physical_row']-1]
        gs.append({'group_id':gid,'physical_row':row['physical_row'],'unit_ids':[u['unit_id'] for u in members],'preferred_unit_count':len(members),'native_row_crop':row['path'],'source_native_row_box_xyxy':row['source_native_row_box_xyxy'],'row_RGB_SHA256':row['RGB_SHA256']})
    events=[]
    for row,group,shape,role in [(rows[1],gs[2],'.','terminalpunctuation'),(rows[0],gs[1],'SYNTHETIC SPECK','unassigned synthetic trace')]:
        events.append({'event_id':f'{row["row_id"]}_TOY_EVENT','row_id':row['row_id'],'group_id':group['group_id'],'after_local_unit_ordinal':len(group['unit_ids']),'raw_shape':shape,'preferred_role':role,'native_row_crop':row['path'],'source_native_row_box_xyxy':row['source_native_row_box_xyxy'],'row_PNG_SHA256':row['PNG_SHA256'],'row_RGB_SHA256':row['RGB_SHA256']})
    docs={'units':{'units':us,'preferred_unit_count':6,'row_unit_counts':[4,2]},'primitives':{'primitive_components':ps,'base_primitive_count':7},'groups':{'groups':gs,'group_count':3},'rows':{'rows':rows,'row_count':2},'events':{'events':events}}
    c={'schema':'HC1615_FIXED_UNIT_CERTIFICATE_v1','mode':'DECLARED_FIXED_PRIOR_ALPHABET_TRANSFER','donor_key_sha256':donor,'key_values':key.copy(),'source_pins':pins.copy(),'units':[{'unit_id':u['unit_id'],'raw_unit_label':u['preferred_raw_unit_label'],'mark_attributes':copy.deepcopy(u['mark_attributes']),'plaintext_value':key.get(u['preferred_raw_unit_label'])} for u in us],'groups':[{'group_id':g['group_id'],'unit_ids':g['unit_ids'].copy(),'literal_base':text,'all_units_covered':covered} for g,text,covered in zip(gs,['abab','[UNKNOWN]','ba'],[True,False,True])],'rows':[{'row_id':r['row_id'],'unit_ids':r['unit_ids'].copy(),'literal_base':text,'literal_with_preferred_terminal_event':display} for r,text,display in zip(rows,['abab [UNKNOWN]','ba'],['abab [UNKNOWN]','ba.'])],'events':copy.deepcopy(events),'counts':{'preferred_units':6,'covered_units':5,'groups':3,'rows':2,'events':2}}
    return c,docs,key,pins,donor

if __name__=='__main__':
    c,d,key,pins,donor=fixture();r=a.verify(c,d,key,pins,donor)
    assert r['units']==6 and r['primitive_components']==7 and r['expanded_plaintext_characters']==6 and r['covered_units']==5
    negatives=a.tamper_checks(c,d,key,pins,donor)
    for name,index,value in [('opaque letter manufactured',3,'a'),('composite expanded value truncated',2,'a')]:
        bad=copy.deepcopy(c);bad['units'][index]['plaintext_value']=value
        try:a.verify(bad,d,key,pins,donor)
        except ValueError as e:negatives.append({'case':name,'rejected':True,'reason':str(e)})
        else:raise AssertionError('synthetic bad value accepted')
    noninjective=dict(key);noninjective['XY_MARK']='a';bad=copy.deepcopy(c);bad['key_values']=noninjective
    try:a.verify(bad,d,noninjective,pins,donor)
    except ValueError as e:negatives.append({'case':'noninjective per-unit inverse rejected','rejected':True,'reason':str(e)})
    else:raise AssertionError('ambiguous dictionary inverse accepted')
    actual_gate_rejected=False
    try:a.load_actual_after_release()
    except ValueError as e:actual_gate_rejected=True;gate_reason=str(e)
    assert actual_gate_rejected
    result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'synthetic_fixture_only':True,'historical_source_key_candidate_reads':0,'positive':r,'negative_cases':negatives,'negative_count':len(negatives),'actual_release_gate_rejection':gate_reason,'checker_sha256':a.digest(Path(a.__file__)),'synthetic_script_sha256':a.digest(Path(__file__)),'root_decoder_imported':False,'old_case_data_imported':False}
    with (a.OUT/'PRE_RELEASE_SYNTHETIC_CHECKS_v1.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['positive','negative_cases']},indent=2))
