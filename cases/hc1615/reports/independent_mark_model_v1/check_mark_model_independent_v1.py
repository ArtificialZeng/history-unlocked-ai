#!/usr/bin/env python3
"""Independent stdlib audit. No decoder imports; never writes source or candidate."""
import copy, datetime, hashlib, json, unicodedata
from pathlib import Path

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

EXPECTED_MODEL_SHA = 'd6158ec6c3b5a67651d995fbe7783da783baa01c9c286b84206cab873066d3ee'
OPERATOR = {'name':'preserve_visible_caron_after_base_map','scope':'Only source-uncovered wholeunits','required_mark_count':1,'required_raw_shape':'detachedtwo-strokeupperchevron','required_literal_source_type':'CARON_LIKE shape only','required_mark_strokes':2,'required_base_value_length':1,'plaintext_combining_mark':'U+030C','plaintext_normalization':'NFC explicit','known_whole_unit_precedence':True}

def derive(u,key):
    whole=u['preferred_raw_unit_label']
    if whole in key:return key[whole],'known_whole_unit_table'
    marks=u['mark_attributes'];base=key.get(u['raw_base_label'])
    if len(marks)==1 and isinstance(base,str) and len(base)==1 and base.isalpha():
        m=marks[0]
        if m.get('raw_shape')==OPERATOR['required_raw_shape'] and m.get('literal_source_type')==OPERATOR['required_literal_source_type'] and len(m.get('stroke_components',[]))==OPERATOR['required_mark_strokes']:
            return unicodedata.normalize('NFC',base+'\u030c'),'base_map_plus_preserved_caron_HYPOTHESIS'
    return None,'uncovered_without_rule'

def symbolic_profile(u):
    # Intrinsic/uncertain allographic entry strokes remain carried data, not a predicted mark.
    detached=tuple((m.get('raw_shape'),m.get('literal_source_type'),tuple(m.get('stroke_components',[]))) for m in u['mark_attributes'] if m.get('raw_shape')==OPERATOR['required_raw_shape'] and m.get('literal_source_type')==OPERATOR['required_literal_source_type'])
    return (u['preferred_raw_unit_label'],u['raw_base_label'],detached)

def verify(c, docs, key, pins, donor_sha=EXPECTED_DONOR_SHA, punctuation_roles=('comma/terminalpunctuation',)):
    us, ps, gs, rs, es = (docs[n][k] for n,k in [('units','units'),('primitives','primitive_components'),('groups','groups'),('rows','rows'),('events','events')])
    ids = [u['unit_id'] for u in us]
    require(len(ids)==len(set(ids)), 'source unit IDs unique')
    require([u['global_preferred_unit_ordinal'] for u in us]==list(range(1,len(us)+1)), 'source global ordinal order')
    require(c['schema']=='HC1615_MARK_CARRY_CERTIFICATE_v1', 'schema')
    require(c['mode']=='DECLARED_FIXED_PRIOR_ALPHABET_PLUS_MARK_HYPOTHESIS', 'mode')
    require(c['key_values']==key, 'exact fixed key dictionary')
    require(c['donor_key_sha256']==donor_sha, 'donor byte pin')
    require(all(isinstance(v,str) and v for v in key.values()), 'nonempty string key values')
    require(len(set(key.values()))==len(key), 'injective per-unit dictionary values')
    inverse={v:k for k,v in key.items()}
    require(c['source_pins']==pins, 'complete source pin dictionary')
    require(c['events']==es, 'all events exact object equality and order')
    require(len(c['units'])==len(us), 'unit count')
    require(c['structural_model']==OPERATOR,'exact registered operator')
    require(c['model_sha256']==EXPECTED_MODEL_SHA,'registered model byte pin')
    values = {}
    interpretations=[]
    for u,v in zip(us,c['units']):
        value,rule=derive(u,key)
        interpretations.append({'unit_id':u['unit_id'],'rule':rule})
        expected={'unit_id':u['unit_id'],'raw_unit_label':u['preferred_raw_unit_label'],'mark_attributes':u['mark_attributes'],'plaintext_value':value}
        require(v==expected, 'complete exact unit lookup/mark/order: '+u['unit_id'])
        values[u['unit_id']]=expected['plaintext_value']
        if expected['plaintext_value'] is not None:
            if rule=='known_whole_unit_table':
                require(inverse[expected['plaintext_value']]==u['preferred_raw_unit_label'],'fixed whole-unit inverse')
            else:
                decomposed=unicodedata.normalize('NFD',value)
                require(len(decomposed)==2 and decomposed[1]=='\u030c' and inverse[decomposed[0]]==u['raw_base_label'],'structural inverse base plus caron')
    require(c['unit_interpretations']==interpretations,'every derived rule and order exact')
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
    return {'units':len(us),'primitive_components':len(ps),'base_primitives':docs['primitives'].get('base_primitives',len(ps)),'detached_mark_stroke_primitives':docs['primitives'].get('detached_mark_stroke_primitives',0),'associated_mark_events':sum('associated_unit_id' in e for e in es),'punctuation_emitted_roles':list(punctuation_roles),'covered_units':sum(v is not None for v in values.values()),'marked_unit_records':sum(bool(u['mark_attributes']) for u in us),'mark_attributes':sum(len(u['mark_attributes']) for u in us),'groups':len(gs),'rows':len(rs),'events':len(es),'expanded_NFC_letter_characters':sum(len(v) for v in values.values() if v is not None),'used_raw_classes':sorted({u['preferred_raw_unit_label'] for u in us}),'unused_fixed_raw_classes':sorted(set(key)-{u['preferred_raw_unit_label'] for u in us}),'literal_rows':[r['literal_with_preferred_terminal_event'] for r in expected_rows]}


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

def greedy_encrypt(text,units,key,punctuation):
    """No unit IDs/positions in inverse lookup. Longest dictionary value first."""
    require(text==unicodedata.normalize('NFC',text),'literal text NFC')
    inverse={v:k for k,v in key.items()}
    catalog={}
    marked={}
    for u in units:
        profile=symbolic_profile(u)
        catalog.setdefault(u['preferred_raw_unit_label'],set()).add(profile)
        value,rule=derive(u,key)
        if rule=='base_map_plus_preserved_caron_HYPOTHESIS':marked.setdefault(u['raw_base_label'],set()).add(profile)
    ordered=sorted(inverse,key=lambda v:(-len(v),v))
    tokens=[];offset=0
    while offset<len(text):
        ch=text[offset]
        if ch in [' ','\n']:
            tokens.append(('format',ch));offset+=1;continue
        if ch in punctuation:
            tokens.append(('punctuation',ch));offset+=1;continue
        whole=next((v for v in ordered if text.startswith(v,offset)),None)
        if whole is not None:
            raw=inverse[whole];profiles=catalog.get(raw,{(raw,raw,())})
            require(len(profiles)==1,'ambiguous whole-glyph profile without position exceptions')
            tokens.append(('unit',next(iter(profiles))));offset+=len(whole);continue
        decomp=unicodedata.normalize('NFD',ch)
        require(len(decomp)==2 and decomp[1]=='\u030c' and decomp[0] in inverse,'unsupported plaintext character')
        rawbase=inverse[decomp[0]]
        require(len(decomp[0])==1,'single-letter inverse base')
        profiles=marked.get(rawbase,set())
        require(len(profiles)==1,'ambiguous/missing structural profile; no position exception permitted')
        tokens.append(('unit',next(iter(profiles))));offset+=1
    return tokens

def source_tokens(docs,roles):
    us=docs['units']['units'];gs=docs['groups']['groups'];rs=docs['rows']['rows'];es=docs['events']['events'];umap={u['unit_id']:u for u in us};tokens=[]
    for rowindex,r in enumerate(rs):
        groups=[g for g in gs if g['physical_row']==r['physical_row']]
        for groupindex,g in enumerate(groups):
            for ordinal,uid in enumerate(g['unit_ids'],1):
                tokens.append(('unit',symbolic_profile(umap[uid])))
                tokens.extend(('punctuation',e['raw_shape']) for e in es if e['row_id']==r['row_id'] and e['group_id']==g['group_id'] and e.get('after_local_unit_ordinal')==ordinal and e['preferred_role'] in roles)
            if groupindex+1<len(groups):tokens.append(('format',' '))
        if rowindex+1<len(rs):tokens.append(('format','\n'))
    return tokens

def verify_files(root,donor,verify_native=False):
    root=Path(root);donor=Path(donor)
    cfgpath=root/'config/MARK_CARRY_MODEL_v1.json'
    require(digest(cfgpath)==EXPECTED_MODEL_SHA,'exact registered configuration bytes')
    cfg=load(cfgpath);require(cfg['additional_structural_operator']==OPERATOR,'operator registration exact')
    require(cfg['existing_table_entries_unchanged'] is True and cfg['additional_arbitrary_letter_values']==0 and cfg['source_edits']==0 and cfg['per_position_exceptions']==0,'no refit/repair/exception')
    require(cfg['donor_key_sha256']==EXPECTED_DONOR_SHA and digest(donor)==EXPECTED_DONOR_SHA,'actual supplied donor file bytes')
    key=load(donor)['unit_values']
    for rel,h in cfg['source_pins'].items():
        p=Path(rel);require(not p.is_absolute() and '..' not in p.parts,'safe relative source pin')
        require(digest(root/p)==h,'strict source file pin: '+rel)
    d={n:load(root/'data/source_v1'/f'SOURCE_{n.upper()}_v1.json') for n in ['units','primitives','groups','rows','events']}
    cp=root/'data/mark_carry_projection_v1/MARK_CARRY_CANDIDATE_v1.json';c=load(cp);roles=cfg['punctuation_emission_roles']
    result=verify(c,d,key,cfg['source_pins'],punctuation_roles=roles)
    rp=root/'data/mark_carry_projection_v1/LITERAL_ROWS_v1.txt'
    require(rp.read_text()=='\n'.join(result['literal_rows'])+'\n','exact literal file, no editorial changes')
    text='\n'.join(result['literal_rows']);punct={e['raw_shape'] for e in d['events']['events'] if e['preferred_role'] in roles}
    enc=greedy_encrypt(text,d['units']['units'],key,punct);expected=source_tokens(d,roles)
    require(enc==expected,'whole-text longest-match symbolic encryption and formatting exact')
    native_files=[]
    if verify_native:
        for row in d['rows']['rows']:
            require(digest(root/row['path'])==row['PNG_SHA256'],'native row PNG bytes')
            native_files.append(row['path'])
    result.update({'arithmetic_PASS':True,'greedy_text_encryption_PASS':True,'greedy_token_count':len(enc),'inverse_unit_count':sum(t[0]=='unit' for t in enc),'punctuation_tokens':sum(t[0]=='punctuation' for t in enc),'space_tokens':sum(t==('format',' ') for t in enc),'rowbreak_tokens':sum(t==('format','\n') for t in enc),'greedy_convention':'longest complete fixed-table value; decomposablecaron inversebase plus mark; no source position exceptions','intrinsic_allograph_predicted':False,'all_source_mark_attributes_carried':True,'native_file_hashes_verified':len(native_files),'native_validation_scope':'PNG file hashes only; sealedcoldsourcepixel replays are separate','source_pins_verified':len(cfg['source_pins']),'candidate_sha256':digest(cp),'literal_sha256':digest(rp),'model_sha256':digest(cfgpath),'donor_key_sha256':digest(donor),'checker_sha256':digest(Path(__file__)),'root_decoder_imported':False,'source_edits':0,'key_refits_or_extensions':0,'physical_caron_function_is_hypothesis':True,'blind_claim':False})
    return result,c,d,key,cfg

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Standalone HC1615 mark-carry certificate and whole-text symbolic encryption audit')
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--donor-key',required=True,type=Path,help='Explicit unchanged byte-pinned donor key file; configuration absolute donor path is not used')
    parser.add_argument('--verify-native',action='store_true',help='Also require the seven native row PNG files and check their file hashes')
    parser.add_argument('--tamper',action='store_true',help='Run meaningful in-memory negative certificate/source tests')
    args=parser.parse_args()
    result,c,d,key,cfg=verify_files(args.root,args.donor_key,args.verify_native)
    if args.tamper:
        result['core_tamper_cases']=tamper_checks(c,d,key,cfg['source_pins'],punctuation_roles=cfg['punctuation_emission_roles'])
    result['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(json.dumps(result,ensure_ascii=False,indent=2))
