#!/usr/bin/env python3
"""Focused baseline in-memory falsifiers. Frozen historical files are never edited."""
import copy,datetime,json
from pathlib import Path
import check_certificate_independent_v2 as a
c,d,key,pins,roles=a.load_actual_after_release()
base=a.verify(c,d,key,pins,punctuation_roles=roles)
neg=[]
def reject(name,edit):
    cc=copy.deepcopy(c);dd=copy.deepcopy(d);edit(cc,dd)
    try:a.verify(cc,dd,key,pins,punctuation_roles=roles)
    except (ValueError,KeyError,IndexError,TypeError) as e:neg.append({'case':name,'rejected':True,'reason':str(e)})
    else:raise AssertionError('actual tamper accepted: '+name)
opaque=next(i for i,u in enumerate(c['units']) if u['plaintext_value'] is None)
reject('opaque plaintext manufactured',lambda c,d:c['units'][opaque].update(plaintext_value='FABRICATED'))
bare=key.get(d['units']['units'][opaque]['raw_base_label'],'FABRICATED')
reject('opaque marked unit replaced by bare base fallback',lambda c,d:c['units'][opaque].update(plaintext_value=bare))
expanded=next(i for i,u in enumerate(c['units']) if u['plaintext_value'] is not None and len(u['plaintext_value'])>1)
reject('one multiletter unit truncated',lambda c,d:c['units'][expanded].update(plaintext_value=c['units'][expanded]['plaintext_value'][:-1]))
reject('one composite unit split into extra record',lambda c,d:c['units'].insert(expanded+1,copy.deepcopy(c['units'][expanded])))
mark=next(i for i,e in enumerate(d['events']['events']) if 'associated_unit_id' in e)
def foreign(c,d):
    event=d['events']['events'][mark];event['associated_unit_id']=next(u['unit_id'] for u in d['units']['units'] if u['group_id']==event['group_id'] and u['unit_id']!=event['associated_unit_id']);c['events']=copy.deepcopy(d['events']['events'])
reject('mark event moved to foreign unit with coherent certificate event',foreign)
def appropriate_base(c,d):
    event=d['events']['events'][mark];unit=next(u for u in d['units']['units'] if u['unit_id']==event['associated_unit_id']);event['primitive_component_ids'][0]=unit['primitive_component_ids'][0];c['events']=copy.deepcopy(d['events']['events'])
reject('associated mark event appropriates base primitive',appropriate_base)
def unaccounted(c,d):
    d['events']['events'][mark]['primitive_component_ids'].pop();c['events']=copy.deepcopy(d['events']['events'])
reject('detached stroke absent from mark-event accounting',unaccounted)
reject('base primitive count mislabeled',lambda c,d:d['primitives'].update(base_primitives=d['primitives']['base_primitives']-1))
reject('detached stroke count mislabeled',lambda c,d:d['primitives'].update(detached_mark_stroke_primitives=d['primitives']['detached_mark_stroke_primitives']-1))
comma=next(e for e in d['events']['events'] if e['raw_shape']==',' and e['preferred_role'] in roles)
rowindex=next(i for i,r in enumerate(c['rows']) if r['row_id']==comma['row_id'])
reject('preferred comma omitted from exact row display',lambda c,d:c['rows'][rowindex].update(literal_with_preferred_terminal_event=c['rows'][rowindex]['literal_with_preferred_terminal_event'].replace(',','')))
reject('unit-attached mark event independently emitted',lambda c,d:c['rows'][0].update(literal_with_preferred_terminal_event=c['rows'][0]['literal_with_preferred_terminal_event']+d['events']['events'][mark]['raw_shape']))
r={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_baseline_only':True,'structural_successor_models_tested':False,'baseline_candidate_sha256':a.digest(a.BASE/'data/fixed_projection_v1/CONDITIONAL_CANDIDATE_v1.json'),'checker_sha256':a.digest(Path(a.__file__)),'tamper_script_sha256':a.digest(Path(__file__)),'frozen_historical_files_unchanged':True,'additional_negative_cases':neg,'additional_negative_count':len(neg),'core_negative_count':29,'total_actual_negative_count':29+len(neg),'coverage_is_not_accuracy':True}
with (a.OUT/'ADDITIONAL_ACTUAL_TAMPER_RESULT_v1.json').open('x') as f:json.dump(r,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'additional':len(neg),'total_actual':29+len(neg),'all_rejected':True},indent=2))
