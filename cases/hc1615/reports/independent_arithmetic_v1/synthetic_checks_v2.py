#!/usr/bin/env python3
"""Toy v2 schema adaptation: two two-stroke marks, inner comma, final period."""
import copy,datetime,json
from pathlib import Path
import check_certificate_independent_v2 as a
from synthetic_checks_v1 import fixture as initial_fixture

def fixture():
    c,d,key,pins,donor=initial_fixture();us=d['units']['units'];ps=[];marks=[]
    for u in us:
        marked=bool(u['mark_attributes'])
        ids=[u['unit_id']+'BASE']+([u['unit_id']+'MARK1',u['unit_id']+'MARK2'] if marked else [])
        u['primitive_component_ids']=ids;u['primitive_span']={'start_component_id':ids[0],'end_component_id':ids[-1]}
        for i,pid in enumerate(ids):
            p={'component_id':pid,'unit_id':u['unit_id'],'row_id':u['row_id'],'group_id':u['group_id'],'native_row_crop':u['native_row_crop'],'source_native_row_box_xyxy':u['source_native_row_box_xyxy'],'row_RGB_SHA256':u['row_RGB_SHA256']}
            if i==0:p['local_base_ordinal']=u['local_unit_ordinal']
            ps.append(p)
        if marked:marks.append({'event_id':u['unit_id']+'TOY_MARK_EVENT','row_id':u['row_id'],'group_id':u['group_id'],'associated_unit_id':u['unit_id'],'raw_shape':'SYNTHETIC CHEVRON','primitive_component_ids':ids[1:],'preferred_role':'synthetic associated mark','semantic_role':None,'native_row_crop':u['native_row_crop'],'source_native_row_box_xyxy':u['source_native_row_box_xyxy'],'row_RGB_SHA256':u['row_RGB_SHA256']})
    d['primitives']={'primitive_components':ps,'base_primitives':6,'detached_mark_stroke_primitives':4,'totalpreferred_components':10}
    r=d['rows']['rows'][0];g=d['groups']['groups'][0]
    comma={'event_id':'TOY_COMMA','row_id':r['row_id'],'group_id':g['group_id'],'after_local_unit_ordinal':2,'raw_shape':',','preferred_role':'commapunctuation','alternative_role':'toy role only','native_row_crop':r['path'],'source_native_row_box_xyxy':r['source_native_row_box_xyxy'],'row_PNG_SHA256':r['PNG_SHA256'],'row_RGB_SHA256':r['RGB_SHA256']}
    period=c['events'][0]
    events=marks+[comma,period];d['events']['events']=events;c['events']=copy.deepcopy(events);c['counts']['events']=4
    c['rows'][0]['literal_with_preferred_terminal_event']='ab,ab [UNKNOWN]'
    return c,d,key,pins,donor,['commapunctuation','terminalpunctuation']

if __name__=='__main__':
    c,d,key,pins,donor,roles=fixture();r=a.verify(c,d,key,pins,donor,roles)
    assert r['units']==6 and r['primitive_components']==10 and r['base_primitives']==6 and r['detached_mark_stroke_primitives']==4 and r['associated_mark_events']==2 and r['expanded_plaintext_characters']==6
    neg=a.tamper_checks(c,d,key,pins,donor,roles)
    def reject(name,edit):
        cc=copy.deepcopy(c);dd=copy.deepcopy(d);edit(cc,dd)
        try:a.verify(cc,dd,key,pins,donor,roles)
        except (ValueError,KeyError,TypeError,IndexError) as e:neg.append({'case':name,'rejected':True,'reason':str(e)})
        else:raise AssertionError('bad v2 trace accepted: '+name)
    reject('opaque value manufactured',lambda c,d:c['units'][3].update(plaintext_value='a'))
    reject('expanded unit truncated',lambda c,d:c['units'][2].update(plaintext_value='a'))
    def wrong_owner(c,d):
        d['events']['events'][0]['associated_unit_id']=d['units']['units'][0]['unit_id'];c['events']=copy.deepcopy(d['events']['events'])
    reject('associated mark ownership changed with copied event',wrong_owner)
    def take_base(c,d):
        d['events']['events'][0]['primitive_component_ids'][0]=d['units']['units'][2]['primitive_component_ids'][0];c['events']=copy.deepcopy(d['events']['events'])
    reject('mark event appropriates base primitive with copied event',take_base)
    def omit_mark(c,d):
        d['events']['events'][0]['primitive_component_ids'].pop();c['events']=copy.deepcopy(d['events']['events'])
    reject('detached mark stroke omitted from event accounting',omit_mark)
    reject('base primitive census changed',lambda c,d:d['primitives'].update(base_primitives=5))
    reject('detached mark stroke census changed',lambda c,d:d['primitives'].update(detached_mark_stroke_primitives=3))
    reject('comma removed from row display',lambda c,d:c['rows'][0].update(literal_with_preferred_terminal_event='abab [UNKNOWN]'))
    reject('mark event emitted as text',lambda c,d:c['rows'][0].update(literal_with_preferred_terminal_event='ab,SYNTHETIC CHEVRONab [UNKNOWN]'))
    rejected=False
    try:a.load_actual_after_release()
    except ValueError as e:rejected=True;reason=str(e)
    assert rejected
    result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'schema_only_adapter_before_actual_source_values_or_P':True,'historical_source_values_key_candidate_reads':0,'positive':r,'negative_cases':neg,'negative_count':len(neg),'actual_release_gate_rejection':reason,'checker_sha256':a.digest(Path(a.__file__)),'synthetic_script_sha256':a.digest(Path(__file__)),'root_decoder_imported':False,'old_case_data_imported':False}
    with (a.OUT/'PRE_RELEASE_SYNTHETIC_CHECKS_v2.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['positive','negative_cases']},indent=2))
