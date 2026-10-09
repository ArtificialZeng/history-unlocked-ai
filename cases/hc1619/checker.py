#!/usr/bin/env python3
"""Portable replay of two frozen HC1619 predictions. No optimizer or source view.

Only package-relative files are opened. Literal output and key values are never
printed. Replaying this mapping is not evidence of historical answer accuracy.
"""
import argparse
from collections import Counter, OrderedDict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
FROZEN = ROOT / 'frozen'

def require(condition, message):
    if not condition:
        raise ValueError(message)

def path(rel):
    p = (ROOT / rel).resolve()
    require(p.is_relative_to(ROOT), 'Input path escapes package')
    require(p.is_file(), 'Missing package input: '+rel)
    return p

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(rel):
    return json.loads(path(rel).read_text(encoding='utf-8'))

def verify_manifest(rel):
    manifest = load(rel)
    for row in manifest['files']:
        p = path(row['path'])
        require(sha(p) == row['sha256'], 'Input SHA-256 mismatch: '+row['path'])
        require(p.stat().st_size == row['bytes'], 'Input byte-size mismatch: '+row['path'])
    return len(manifest['files'])

def replay(packet_name, packet_filename, first_filename, source, ledger, key, registration):
    packet_rel = 'frozen/config/'+packet_filename
    first_rel = 'frozen/experiments/fixed_transfer_v1/'+first_filename
    packet, first = load(packet_rel), load(first_rel)
    saved = load('frozen/reports/independent_transfer_review_v1/REPLAY_'+packet_name.upper()+'.json')
    registered = next(x for x in registration['two_source_packets_before_target_application']
                      if x['path'] == 'config/'+packet_filename)
    require(sha(path(packet_rel)) == registered['sha256'] == first['bridge_sha256'], 'Packet pin changed')
    require(packet['source_freeze_sha256'] == sha(path('frozen/reports/independent_source_review_v1/FROZEN_SOURCE.json')), 'Source pin changed')
    mapping = packet['source_label_to_old_raw_class']
    require(set(mapping) == {x['source_label'] for x in source['classes']}, 'Incomplete source class map')
    overlays = {x['index']:x for x in packet['source_refinements']}
    require(sorted(overlays) == [8,15,58,64] and len(overlays)==len(packet['source_refinements']), 'Frozen overlay changed')
    subclass_map = {}
    for row in overlays.values():
        require(row['original_source_label']=='g', 'Unexpected source overlay base')
        sub, canonical = row['refined_source_label'], row['old_raw_class']
        require(sub not in subclass_map or subclass_map[sub]==canonical, 'Nonuniform graphical subclass projection')
        subclass_map[sub]=canonical
    require(subclass_map=={'V007_OPEN_LOWER_HOOK':'9','V007_CLOSED_LOWER_LOOP':'g'}, 'Frozen topology projection changed')
    inverse = {v:k for k,v in key.items()}
    event_map = {}
    for event in source['format_marks']:
        event_map.setdefault(event['after_group_id'],[]).append(event['visible_mark'])
    certificates, rows, grouped = [], [], OrderedDict()
    for src in ledger:
        index, label = src['index'], src['source_label']
        canonical, refined = mapping[label], label
        if index in overlays:
            overlay=overlays[index]
            require(overlay['original_source_label']==label,'Overlay source label mismatch')
            canonical, refined=overlay['old_raw_class'],overlay['refined_source_label']
        unit=key.get(canonical)
        recovered=inverse.get(unit) if unit is not None else None
        require(recovered==canonical,'Canonical inverse mismatch')
        alias=None
        if canonical=='s': neutral,alias='DELTA','DELTA_single_triangular_loop'
        elif canonical in ('g','9'): neutral,alias='g',refined
        elif canonical=='c' and label=='O0': neutral,alias='O0','C_LIKE_OPEN_ROUND_TERMINAL_VARIANT'
        elif unit is None: neutral,alias=label,'OPAQUE_UNDECODED_SOURCE_LABEL_PASSTHROUGH'
        else: neutral=recovered
        require(neutral==label,'Neutral source inverse mismatch')
        rows.append({'index':index,'line':src['line'],'group_id':src['group_id'],'position':src['position'],
                     'source_label':label,'refined_source_label':refined,'canonical_class':canonical,
                     'unit_value':unit,'known_unit_roundtrip':unit is not None})
        certificates.append({'occurrence_id':src['occurrence_id'],'index':index,'line':src['line'],
            'group_id':src['group_id'],'position':src['position'],'original_neutral_label':label,
            'original_source_class_id':src['source_class_id'],'pre_application_source_subclass':refined,
            'canonical_key_unit':canonical,'decoded_unit':unit,'inverse_key_canonical_unit':recovered,
            'source_alias_metadata':alias,'neutral_label_reconstructed_with_metadata':neutral,
            'known_canonical_key_roundtrip':unit is not None,'opaque_passthrough_is_not_decryption':unit is None,
            'original_navigation_rectangle':src['navigation_rectangle']})
        group=grouped.setdefault(src['group_id'],{'line':src['line'],'group_id':src['group_id'],'source_labels':[],'unit_values':[]})
        group['source_labels'].append(label)
        group['unit_values'].append(unit if unit is not None else '[UNMAPPED:'+label+']')
    groups=[]
    for g in grouped.values():
        g['text']=''.join(g['unit_values']);g['events_after']=event_map.get(g['group_id'],[]);groups.append(g)
    lines=[' '.join(g['text'] for g in groups if g['line']==line) for line in (1,2)]
    formatted=[' '.join(g['text']+''.join(g['events_after']) for g in groups if g['line']==line) for line in (1,2)]
    mapped=sum(r['unit_value'] is not None for r in rows)
    unknown=[r['index'] for r in rows if r['unit_value'] is None]
    expanded=sum(len(r['unit_value']) for r in rows if r['unit_value'] is not None)
    expected={'occurrences':rows,'groups':groups,'literal_physical_lines':lines,'literal_lines_with_events':formatted,
              'source_units':80,'key_covered_units':mapped,'known_expanded_letters':expanded,'unknown_positions':unknown,
              'physical_groups':12,'source_lines':2,'format_events':4,'source_sha256':registration['source_freeze_sha256'],
              'key_sha256':registration['key_sha256'],'bridge_sha256':sha(path(packet_rel)),
              'key_refit':False,'frozen_source_overwrites':0,'coverage_is_not_accuracy':True,
              'pre_application_source_refinements':packet['source_refinements'],'language_completion':False,
              'cipher_solved':False,'full_historical_reading_confirmed':False}
    for field,value in expected.items():
        require(first.get(field)==value,'Frozen first-output mismatch: '+packet_name+'/'+field)
    comparisons={'occurrence_certificate':certificates,'groups':groups,'literal_physical_lines':lines,
                 'literal_lines_with_events':formatted,'known_units':mapped,'expanded_known_letters':expanded,
                 'unknown_indices':unknown,'mechanical_differences':[],'source_occurrences':80,
                 'line_occurrences':[62,18],'physical_groups':12,'format_marks':source['format_marks'],
                 'input_packet_sha256':sha(path(packet_rel)),'first_output_sha256':sha(path(first_rel))}
    for field,value in comparisons.items():
        require(saved.get(field)==value,'Frozen independent-certificate mismatch: '+packet_name+'/'+field)
    require(mapped==(79 if packet_name=='conservative' else 80),'Wrong frozen coverage')
    require(unknown==([80] if packet_name=='conservative' else []),'Unknown not preserved')
    return {'packet':packet_name,'source_occurrences':80,'mapped_units':mapped,'unknown_indices':unknown,
            'occurrence_certificate_rows':len(certificates),'groups':12,'physical_line_counts':[62,18],
            'punctuation_events':4,'first_output_comparison_fields':len(expected),
            'independent_certificate_comparison_fields':len(comparisons),'mismatches':0,
            'first_output_sha256':sha(path(first_rel)), 'inverse_scope':'Canonical units plus frozen source aliases/layout; no raster or historical truth.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True,help='Fresh directory for aggregate replay receipt')
    args=parser.parse_args()
    dest=args.output_dir.resolve()
    require(not dest.exists(),'Replay output directory must be fresh')
    require(not dest.is_relative_to(FROZEN),'Cannot write into frozen evidence')
    verified=verify_manifest('frozen_inputs_manifest.json')
    package_verified=verify_manifest('PACKAGE_SHA256.json') if (ROOT/'PACKAGE_SHA256.json').is_file() else None
    source=load('frozen/reports/independent_source_review_v1/FROZEN_SOURCE.json')
    ledger=load('frozen/reports/independent_source_review_v1/GLYPH_OCCURRENCES.json')
    key=load('frozen/config/FROZEN_TRANSFER_KEY_v1.json')['unit_values']
    registration=load('frozen/config/TWO_PACKET_APPLICATION_REGISTRATION_v1.json')
    require(len(key)==len(set(key.values()))==22,'Frozen key size or value uniqueness changed')
    require(sha(path('frozen/config/FROZEN_TRANSFER_KEY_v1.json'))==registration['key_sha256'],'Frozen key pin changed')
    require(len(ledger)==80 and [r['index'] for r in ledger]==list(range(1,81)),'Occurrence accounting mismatch')
    require(dict(Counter(r['line'] for r in ledger))=={1:62,2:18},'Line accounting mismatch')
    require(len({r['group_id'] for r in ledger})==12 and len({r['source_class_id'] for r in ledger})==20,'Class/group count mismatch')
    require(Counter(e['visible_mark'] for e in source['format_marks'])=={',':3,'.':1},'Format event mismatch')
    for group in source['cipher_groups']:
        selected=[r for r in ledger if r['group_id']==group['group_id']]
        require([r['source_label'] for r in selected]==group['source_labels'],'Group source labels mismatch')
        require([r['position'] for r in selected]==list(range(1,len(selected)+1)),'Group position mismatch')
    results=[replay('conservative','PRE_APPLICATION_BRIDGE_PACKET_v1.json','CONSERVATIVE_FIRST_OUTPUT.json',source,ledger,key,registration),
             replay('preferred','PRE_APPLICATION_BRIDGE_PACKET_v1p1.json','PREFERRED_FIRST_OUTPUT.json',source,ledger,key,registration)]
    receipt={'status':'PASS_EXACT_FROZEN_DATA_REPLAY','case_id':'hcportal:1619','frozen_input_files_verified':verified,
             'package_payload_files_verified':package_verified,'cases':results,'historical_accuracy_known':False,
             'external_key_or_image_or_original_folder_dependency':False,'source_images_opened':False,
             'network_access_used':False,'optimizer_or_key_fit':False,'new_candidate_created':False,
             'os_level_filesystem_isolation_claimed':False}
    dest.mkdir(parents=True)
    (dest/'REPLAY_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':receipt['status'],'frozen_input_files_verified':verified,'cases':results}))

if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,StopIteration) as exc:
        print('REPLAY_FAILED: '+str(exc),file=sys.stderr);sys.exit(1)
