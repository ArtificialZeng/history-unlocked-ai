#!/usr/bin/env python3
"""Independent stdlib audit. No decoder imports; never writes source or candidate."""
import copy, datetime, hashlib, json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
EXPECTED_DONOR_SHA = '267fac542b3cc9b3fbb5d788b8d867a0c37de0fa1f4ffefe16776256e1835273'

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def unique_object(pairs):
    d = {}
    for k,v in pairs:
        if k in d: raise ValueError('duplicate JSON key: '+k)
        d[k] = v
    return d

def load(p): return json.loads(p.read_text(), object_pairs_hook=unique_object)
def require(test, message):
    if not test: raise ValueError(message)

def verify(c, docs, key, pins, donor_sha=EXPECTED_DONOR_SHA, punctuation_roles=('terminalpunctuation',)):
    us, ps, gs, rs, es = (docs[n][k] for n,k in [('units','units'),('primitives','primitive_components'),('groups','groups'),('rows','rows'),('events','events')])
    ids = [u['unit_id'] for u in us]
    require(len(ids)==len(set(ids)), 'source unit IDs unique')
    require([u['global_preferred_unit_ordinal'] for u in us]==list(range(1,len(us)+1)), 'source global ordinal order')
    require(c['schema']=='HC1615_FIXED_UNIT_CERTIFICATE_v1', 'schema')
    require(c['mode']=='DECLARED_FIXED_PRIOR_ALPHABET_TRANSFER', 'mode')
    require(c['key_values']==key, 'exact fixed key dictionary')
    require(c['donor_key_sha256']==donor_sha, 'donor byte pin')
    require(all(isinstance(v,str) and v for v in key.values()), 'nonempty string key values')
    require(len(set(key.values()))==len(key), 'injective per-unit dictionary values')
    inverse={v:k for k,v in key.items()}
    require(c['source_pins']==pins, 'complete source pin dictionary')
    require(c['events']==es, 'all events exact object equality and order')
    require(len(c['units'])==len(us), 'unit count')
    values = {}
    for u,v in zip(us,c['units']):
        expected={'unit_id':u['unit_id'],'raw_unit_label':u['preferred_raw_unit_label'],'mark_attributes':u['mark_attributes'],'plaintext_value':key.get(u['preferred_raw_unit_label'])}
        require(v==expected, 'complete exact unit lookup/mark/order: '+u['unit_id'])
        values[u['unit_id']]=expected['plaintext_value']
        if expected['plaintext_value'] is not None:
            require(inverse[expected['plaintext_value']]==u['preferred_raw_unit_label'], 'unit-level inverse')
    pids=[p['component_id'] for p in ps]
    require(len(pids)==len(set(pids)), 'unique primitive IDs')
    require([p for u in us for p in u['primitive_component_ids']]==pids, 'ordered primitive partition')
    pmap={p['component_id']:p for p in ps}
    rmap={r['row_id']:r for r in rs}
    require(len(rmap)==len(rs), 'unique row IDs')
    for u in us:
        pp=u['primitive_component_ids']; require(bool(pp), 'nonempty primitive span')
        require(u['primitive_span']=={'start_component_id':pp[0],'end_component_id':pp[-1]}, 'exact primitive span')
        r=rmap[u['row_id']]
        require(u['native_row_crop']==r['path'] and u['source_native_row_box_xyxy']==r['source_native_row_box_xyxy'] and u['row_PNG_SHA256']==r['PNG_SHA256'] and u['row_RGB_SHA256']==r['RGB_SHA256'], 'unit native row provenance')
        for pid in pp:
            p=pmap[pid]
            require(all(p[f]==u[f] for f in ['unit_id','row_id','group_id']), 'primitive owner')
            require(p.get('native_row_crop',p.get('whole_native_row_source'))==r['path'] and p['source_native_row_box_xyxy']==r['source_native_row_box_xyxy'] and p['row_RGB_SHA256']==r['RGB_SHA256'], 'primitive native row provenance')
    require(docs['units']['preferred_unit_count']==len(us), 'source preferred count')
    if 'totalpreferred_components' in docs['primitives']:
        nbase=sum('local_base_ordinal' in p for p in ps)
        require(docs['primitives']['totalpreferred_components']==len(ps) and docs['primitives']['base_primitives']==nbase and docs['primitives']['detached_mark_stroke_primitives']==len(ps)-nbase, 'complete base/detached-stroke primitive census')
    else:
        require(docs['primitives']['base_primitive_count']==len(ps), 'primitive source count')
    require(docs['groups']['group_count']==len(gs) and docs['rows']['row_count']==len(rs), 'source group/row count')
    require([i for g in gs for i in g['unit_ids']]==ids, 'complete ordered group partition')
    require([i for r in rs for i in r['unit_ids']]==ids, 'complete ordered row partition')
    require([r['row_order'] for r in rs]==list(range(1,len(rs)+1)), 'row order')
    if 'row_unit_counts' in docs['units']:
        require(docs['units']['row_unit_counts']==[len(r['unit_ids']) for r in rs], 'source row count vector')
    expected_groups=[]
    for g in gs:
        selected=[u for u in us if u['group_id']==g['group_id']]
        require(g['unit_ids']==[u['unit_id'] for u in selected] and g['preferred_unit_count']==len(selected), 'group membership/count')
        require([u['local_unit_ordinal'] for u in selected]==list(range(1,len(selected)+1)), 'group local order')
        r=rmap[selected[0]['row_id']]
        require(all(u['row_id']==r['row_id'] and u['physical_row']==g['physical_row'] for u in selected), 'group row ownership')
        require(g['native_row_crop']==r['path'] and g['source_native_row_box_xyxy']==r['source_native_row_box_xyxy'] and g['row_RGB_SHA256']==r['RGB_SHA256'], 'group native row provenance')
        expected_groups.append({'group_id':g['group_id'],'unit_ids':g['unit_ids'],'literal_base':''.join(values[i] if values[i] is not None else '[UNKNOWN]' for i in g['unit_ids']),'all_units_covered':all(values[i] is not None for i in g['unit_ids'])})
    require(c['groups']==expected_groups, 'exact complete grouped literal')
    expected_rows=[]
    for r in rs:
        selected=[u for u in us if u['row_id']==r['row_id']]
        require(r['unit_ids']==[u['unit_id'] for u in selected] and r['preferred_row_unit_count']==len(selected), 'row membership/count')
        rowgroups=[g for g in gs if g['physical_row']==r['physical_row']]
        require([i for g in rowgroups for i in g['unit_ids']]==r['unit_ids'], 'row/group order')
        text=' '.join(g['literal_base'] for g in expected_groups if g['group_id'] in {x['group_id'] for x in rowgroups})
        row_emitted=[e for e in es if e['row_id']==r['row_id'] and e['preferred_role'] in punctuation_roles]
        display_groups=[]
        for g in rowgroups:
            chunks=[]
            for ordinal,uid in enumerate(g['unit_ids'],1):
                chunks.append(values[uid] if values[uid] is not None else '[UNKNOWN]')
                chunks.extend(e['raw_shape'] for e in row_emitted if e['group_id']==g['group_id'] and e.get('after_local_unit_ordinal')==ordinal)
            display_groups.append(''.join(chunks))
        require(all('after_local_unit_ordinal' in e and 1<=e['after_local_unit_ordinal']<=len(next(g for g in rowgroups if g['group_id']==e['group_id'])['unit_ids']) for e in row_emitted), 'registered punctuation after a source unit')
        expected_rows.append({'row_id':r['row_id'],'unit_ids':r['unit_ids'],'literal_base':text,'literal_with_preferred_terminal_event':' '.join(display_groups)})
    require(c['rows']==expected_rows, 'exact rows and preferred terminal display')
    require(len({e['event_id'] for e in es})==len(es), 'unique event IDs')
    associated_mark_primitives=[]
    umap={u['unit_id']:u for u in us}
    for e in es:
        r=rmap[e['row_id']]
        require(e['native_row_crop']==r['path'] and e['source_native_row_box_xyxy']==r['source_native_row_box_xyxy'] and e['row_RGB_SHA256']==r['RGB_SHA256'], 'event native row provenance')
        if 'row_PNG_SHA256' in e:require(e['row_PNG_SHA256']==r['PNG_SHA256'],'event PNG metadata')
        own=[g for g in gs if g['group_id']==e['group_id']]
        require(len(own)==1 and own[0]['physical_row']==r['physical_row'],'event group/row ownership')
        if 'associated_unit_id' in e:
            u=umap[e['associated_unit_id']]
            require(u['row_id']==e['row_id'] and u['group_id']==e['group_id'],'mark event associated unit owner')
            require(bool(e['primitive_component_ids']) and all(pid in u['primitive_component_ids'] for pid in e['primitive_component_ids']),'mark event primitive span ownership')
            require(all('local_base_ordinal' not in pmap[pid] for pid in e['primitive_component_ids']),'mark event cannot appropriate base primitive')
            associated_mark_primitives.extend(e['primitive_component_ids'])
        else:
            require('after_local_unit_ordinal' in e and 0<=e['after_local_unit_ordinal']<=len(own[0]['unit_ids']),'ordinal event placement')
    if 'totalpreferred_components' in docs['primitives']:
        mark_ids=[p['component_id'] for p in ps if 'local_base_ordinal' not in p]
        require(len(associated_mark_primitives)==len(set(associated_mark_primitives)) and set(associated_mark_primitives)==set(mark_ids),'every detached mark stroke has exactly one associated mark event')
    require(c['counts']=={'preferred_units':len(us),'covered_units':sum(v is not None for v in values.values()),'groups':len(gs),'rows':len(rs),'events':len(es)}, 'exact certificate counts')
    return {'units':len(us),'primitive_components':len(ps),'base_primitives':docs['primitives'].get('base_primitives',len(ps)),'detached_mark_stroke_primitives':docs['primitives'].get('detached_mark_stroke_primitives',0),'associated_mark_events':sum('associated_unit_id' in e for e in es),'punctuation_emitted_roles':list(punctuation_roles),'covered_units':sum(v is not None for v in values.values()),'marked_unit_records':sum(bool(u['mark_attributes']) for u in us),'mark_attributes':sum(len(u['mark_attributes']) for u in us),'groups':len(gs),'rows':len(rs),'events':len(es),'expanded_plaintext_characters':sum(len(v) for v in values.values() if v is not None),'used_raw_classes':sorted({u['preferred_raw_unit_label'] for u in us}),'unused_fixed_raw_classes':sorted(set(key)-{u['preferred_raw_unit_label'] for u in us}),'literal_rows':[r['literal_with_preferred_terminal_event'] for r in expected_rows]}


def load_actual_after_release():
    # Fail closed before opening any historical source, donor values or candidate.
    gate=OUT/'TRUSTED_SOURCE_AUDIT_RELEASE_v1.json'
    require(gate.exists(),'explicit root source-audit release absent; no target/source/key opened')
    release=load(gate)
    require(release.get('target_projection_audit_released') is True and release.get('case')=='HC1615','invalid explicit release; no target/source/key opened')
    interface=load(OUT/'LOCKED_PUNCTUATION_INTERFACE_v1.json')
    require(interface['root_policy_locked_before_actual_read'] is True,'preprojection punctuation interface required')
    lock=load(BASE/'config/FIXED_PROJECTION_LOCK_v1.json')
    require(lock['independent_cold_source_audit_complete'] is True and lock['key_refit_or_extension'] is False and lock['single_fixed_lookup'] is True,'frozen mode gate')
    for rel,sha in lock['source_pins'].items(): require(digest(BASE/rel)==sha,'source pin '+rel)
    donor=Path(lock['donor_key_path']); require(digest(donor)==EXPECTED_DONOR_SHA,'actual donor byte pin')
    key=load(donor)['unit_values']
    docs={n:load(BASE/'data/source_v1'/f'SOURCE_{n.upper()}_v1.json') for n in ['units','primitives','groups','rows','events']}
    c=load(BASE/'data/fixed_projection_v1/CONDITIONAL_CANDIDATE_v1.json')
    return c,docs,key,lock['source_pins'],interface['punctuation_roles']

def tamper_checks(c,docs,key,pins,donor_sha=EXPECTED_DONOR_SHA,punctuation_roles=('terminalpunctuation',)):
    cases=[]
    def reject(name,change):
        cc=copy.deepcopy(c); dd=copy.deepcopy(docs); change(cc,dd)
        try: verify(cc,dd,key,pins,donor_sha,punctuation_roles)
        except (ValueError,KeyError,IndexError,TypeError) as e: cases.append({'case':name,'rejected':True,'reason':str(e)})
        else: raise ValueError('tamper accepted: '+name)
    reject('unit omitted',lambda c,d:c['units'].pop())
    reject('unit order reversed',lambda c,d:c['units'].reverse())
    reject('raw label changed',lambda c,d:c['units'][0].update(raw_unit_label=c['units'][0]['raw_unit_label']+'_WRONG'))
    reject('plaintext changed',lambda c,d:c['units'][0].update(plaintext_value=(c['units'][0]['plaintext_value'] or '')+'WRONG'))
    marked=next((i for i,u in enumerate(c['units']) if u['mark_attributes']),None)
    if marked is not None:reject('mark dropped',lambda c,d:c['units'][marked].update(mark_attributes=[]))
    else:reject('mark fabricated',lambda c,d:c['units'][0].update(mark_attributes=[{'fabricated':True}]))
    firstkey=next(iter(key))
    reject('key refit',lambda c,d:c['key_values'].update({firstkey:key[firstkey]+'WRONG'}))
    reject('key extension',lambda c,d:c['key_values'].update({'SYNTHETIC_EXTENSION':'WRONG'}))
    reject('donor pin changed',lambda c,d:c.update(donor_key_sha256='0'*64))
    if pins:reject('source pin dropped',lambda c,d:c['source_pins'].pop(next(iter(c['source_pins']))))
    reject('group omitted',lambda c,d:c['groups'].pop())
    reject('group order reversed',lambda c,d:c['groups'].reverse())
    reject('group unit omitted',lambda c,d:c['groups'][0]['unit_ids'].pop())
    reject('group spelling changed',lambda c,d:c['groups'][0].update(literal_base=c['groups'][0]['literal_base']+'WRONG'))
    reject('coverage flag inverted',lambda c,d:c['groups'][0].update(all_units_covered=not c['groups'][0]['all_units_covered']))
    reject('row unit omitted',lambda c,d:c['rows'][0]['unit_ids'].pop())
    reject('row text changed',lambda c,d:c['rows'][0].update(literal_base=c['rows'][0]['literal_base']+'WRONG'))
    reject('row display changed',lambda c,d:c['rows'][0].update(literal_with_preferred_terminal_event=c['rows'][0]['literal_with_preferred_terminal_event']+'WRONG'))
    if c['events']:
        reject('event omitted',lambda c,d:c['events'].pop())
        reject('event shape changed',lambda c,d:c['events'][0].update(raw_shape=c['events'][0]['raw_shape']+'WRONG'))
    else:reject('event introduced',lambda c,d:c['events'].append({'fabricated':True}))
    if len(c['events'])>1:reject('event order reversed',lambda c,d:c['events'].reverse())
    reject('source primitive span changed',lambda c,d:d['units']['units'][0]['primitive_span'].update(end_component_id='WRONG'))
    reject('primitive duplicated',lambda c,d:d['primitives']['primitive_components'].append(copy.deepcopy(d['primitives']['primitive_components'][0])))
    reject('primitive owner changed',lambda c,d:d['primitives']['primitive_components'][0].update(unit_id='WRONG'))
    reject('source group order changed',lambda c,d:d['groups']['groups'][0]['unit_ids'].reverse())
    reject('source row order changed',lambda c,d:d['rows']['rows'].reverse())
    terminals=[i for i,e in enumerate(docs['events']['events']) if e['preferred_role'] in punctuation_roles]
    if terminals:
        def move(c,d):
            d['events']['events'][terminals[0]]['after_local_unit_ordinal']=0;c['events']=copy.deepcopy(d['events']['events'])
        reject('terminal moved and certificate event copied coherently',move)
    reject('native row PNG metadata changed',lambda c,d:d['rows']['rows'][0].update(PNG_SHA256='0'*64))
    reject('covered count changed',lambda c,d:c['counts'].update(covered_units=c['counts']['covered_units']+1))
    try:unique_object([('a',1),('a',2)])
    except ValueError:cases.append({'case':'duplicate JSON object key','rejected':True})
    return cases

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--actual',action='store_true');args=p.parse_args()
    if args.actual:
        c,d,k,pins,roles=load_actual_after_release()
        result=verify(c,d,k,pins,punctuation_roles=roles)
        result['tamper_cases']=tamper_checks(c,d,k,pins,punctuation_roles=roles)
        rowfile=BASE/'data/fixed_projection_v1/LITERAL_ROWS_v1.txt'
        require(rowfile.read_text()=='\n'.join(result['literal_rows'])+'\n','literal rows file exact')
        for row in d['rows']['rows']:require(digest(BASE/row['path'])==row['PNG_SHA256'],'native row PNG bytes')
        result.update(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),arithmetic_PASS=True,code_sha256=digest(Path(__file__)),candidate_sha256=digest(BASE/'data/fixed_projection_v1/CONDITIONAL_CANDIDATE_v1.json'),source_pins_verified=len(pins),root_decoder_imported=False)
        with (OUT/'INDEPENDENT_ARITHMETIC_RESULT_v1.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
        print(json.dumps(result,ensure_ascii=False,indent=2))
    else:p.error('Only explicit --actual invokes the released historical audit. Use synthetic_checks_v1.py for synthetic tests.')
