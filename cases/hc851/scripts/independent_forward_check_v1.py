"""Independent HC851 candidate mechanics using only the presealed own codec.

The preferred current 144 letters and publicly supplied grille are transparent
source inputs. Literal payloads are never smoothed or edited. This checker does
not import the root grille code. Physical source certification is a later step
using a separately frozen cold-source ledger, never unsealed source work.
"""
from pathlib import Path
import argparse,csv,datetime,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/independent_candidate_audit_v1'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(value.encode('utf-8')).hexdigest()
def save(name,value):
    path=OUT/name;path.write_text(json.dumps(value,indent=2)+'\n');return path

def certify_physical_source():
    """Attach frozen pixel-source provenance to every independent forward move."""
    manifestpath=ROOT/'reports/cold_source_v1/MANIFEST_v1.json';sealpath=ROOT/'reports/cold_source_v1/SEAL_v1.json'
    manifest=json.loads(manifestpath.read_text());seal=json.loads(sealpath.read_text())
    assert sha(manifestpath)=='79b54fb37f7d5e651c641fcb18aded8154a5477289b484b1b70c2ae981731307'==seal['manifest_sha256']
    for item in manifest['files']+manifest['input_originals']:
        p=Path(item['path']);p=p if p.is_absolute() else ROOT/p;assert sha(p)==item['sha256']
    prepath=ROOT/'reports/independent_method_v1/INDEPENDENT_CODEC_PRECOMPARISON_SEAL_v1.json';pre=json.loads(prepath.read_text())
    for item in pre['files']:assert sha(ROOT/item['path'])==item['sha256']
    codepath=ROOT/'scripts/independent_grille_v1.py';spec=importlib.util.spec_from_file_location('sealed_own_physical_audit_codec',codepath);codec=importlib.util.module_from_spec(spec);sys.modules[spec.name]=codec;spec.loader.exec_module(codec)
    cold=ROOT/'data/cold_source_v1';typedpath=cold/'PRIMARY_TYPED_SOURCE_v1.json';typed=json.loads(typedpath.read_text());gridpath=cold/'PHYSICAL_PUBLIC_GRILLE_GEOMETRY_v1.json';grid=json.loads(gridpath.read_text())
    coordpath=cold/'PRIMARY_TYPED_OCCURRENCES_COORDINATE_AUDIT_v2.csv';typedcoords=list(csv.DictReader(coordpath.open()));assert len(typedcoords)==144
    rawpath=cold/'PRIMARY_TYPED_ALL_PLACEMENTS_v1.json';raw=json.loads(rawpath.read_text())['records'];assert len(raw)==145
    handpath=cold/'SECONDARY_HAND_ARRAY_OCCURRENCES_v1.csv';hand=list(csv.DictReader(handpath.open()));assert len(hand)==144
    handsourcepath=cold/'SECONDARY_HAND_ARRAY_SOURCE_v1.json';handsource=json.loads(handsourcepath.read_text());grouppath=cold/'ADDITIONAL_GROUPED_WITNESS_SOURCE_v1.json';grouped=json.loads(grouppath.read_text())
    rootfreeze=json.loads((ROOT/'data/root_source_v1/ROOT_SOURCE_FREEZE_v1.json').read_text())
    cipher=rootfreeze['supplied_hand_stream'];assert typed['active_stream']==cipher and len(cipher)==144
    assert (cold/'PRIMARY_TYPED_ACTIVE_STREAM_v1.txt').read_bytes()==(ROOT/'data/root_source_v1/preferred_supplied_hand_cipher_v1.txt').read_bytes()
    assert typed['row_active_counts']==[30,30,30,30,24]
    assert grid['coarse_cut_lattice']['rows']==grid['coarse_cut_lattice']['columns']==6
    assert grid['cut_cells_count']==9 and grid['solid_cells_count']==27
    holes=tuple(sorted(r*6+c+1 for r,c in grid['holes_row_column_0based']));root_holes=tuple(sorted(r*6+c+1 for r,c in rootfreeze['physical_key']['holes_zeroindexed']));assert holes==root_holes
    codec.validate_grille(6,holes);orbits=codec.rotation_orbits(6);assert len(orbits)==9 and all(len(set(orbit)&set(holes))==1 for orbit in orbits)
    cells={(x['row']-1)*6+x['column']:x for x in grid['cell_records']};assert len(cells)==36 and {i for i,x in cells.items() if x['cutout']}==set(holes)
    coord_by_active={int(x['active_index_1based']):x for x in typedcoords};raw_by_active={x['active_index_1based']:x for x in raw if x['active_index_1based'] is not None};assert len(raw_by_active)==144
    hand_by_active={(int(x['array'])-1)*36+(int(x['row'])-1)*6+int(x['column']):x for x in hand};assert len(hand_by_active)==144
    own_results=json.loads((OUT/'ALL_EIGHT_INDEPENDENT_DECODES_v1.json').read_text());selected=next(x for x in own_results['results'] if x['start_turn']==0 and x['direction']==1);literal=selected['literal_plaintext']
    assert codec.decrypt(cipher,6,holes)==literal and codec.encrypt(literal,6,holes)==cipher
    assert 'DIELONDON' in literal and 'MITLBOMBEN' in literal # Retained bytes, never semantic repairs.
    mapping=json.loads((OUT/'ALL_144_ACTIVE_MAPPING_MECHANICAL_v1.json').read_text());full=[];secondary_differences=[]
    manifest_hashes={x['path']:x['sha256'] for x in manifest['files']}
    for x in mapping:
        active=x['active_cipher_position_1indexed'];pos=x['primary_raw_position_1indexed'];source=coord_by_active[active];placement=raw_by_active[active];secondary=hand_by_active[active]
        assert int(source['active_index_1based'])==active and source['ascii_final_visible']==cipher[active-1]==x['literal_payload_character']
        assert placement['raw_placement_index_1based']==pos and placement['ASCII_final_visible']==cipher[active-1]
        assert source['source_sha256']==typed['source_sha256']==placement['source_sha256']
        box=json.loads(source['native_box_xyxy']);assert 0<=box[0]<box[2]<=3024 and 0<=box[1]<box[3]<=1545
        turn=x['turn_in_payload_1indexed']-1;base=[]
        for h in holes:
            current=h
            for _ in range(turn):current=codec.rotate_clockwise(6,current)
            if current==x['grid_cell_1indexed']:base.append(h)
        assert len(base)==1;keycell=cells[base[0]];assert keycell['cutout']
        r=dict(x);r['physical_source_provenance']='FROZEN_PRIMARY_AND_PUBLIC_KEY_VERIFIED'
        r['primary_source']={'record_file':str(coordpath.relative_to(ROOT)),'record_file_sha256':sha(coordpath),'native_box_xyxy':box,'source_file':typed['source_path'],'source_sha256':typed['source_sha256'],'typed_row_1based':int(source['typed_row_1based']),'group_in_row_1based':int(source['source_group_in_row_1based']),'active_group_offset_1based':int(source['group_offset_1based']),'physical_group_offset_1based':placement['physical_offset_in_group_1based'],'row_crop':source['row_crop'],'row_crop_sha256':manifest_hashes[source['row_crop']],'observation_class':source['observation_class'],'earlier_layer_ascii':None if not source['earlier_layer_ascii'] else source['earlier_layer_ascii'],'uncertainty':source['uncertainty'] or None}
        r['public_key_physical_hole']={'original_hole_1indexed':base[0],'original_row_column_1indexed':[keycell['row'],keycell['column']],'native_cell_polygon_xy':keycell['native_cell_polygon_xy'],'native_crop_box_xyxy':keycell['native_crop_box_xyxy'],'crop':keycell['path'],'crop_sha256':manifest_hashes[keycell['path']],'source_file':grid['source'],'source_sha256':grid['source_sha256'],'coarse_boundary_uncertainty_pixels':grid['coarse_cut_lattice']['boundary_uncertainty_pixels'],'clockwise_turns_applied':turn,'exposed_cell_1indexed':x['grid_cell_1indexed'],'rowmajor_rank_at_turn':x['hole_rank_in_turn_1indexed']}
        r['secondary_hand_observation']={'array':int(secondary['array']),'row':int(secondary['row']),'column':int(secondary['column']),'ASCII_observation':secondary['ASCII_observation'],'ASCII_alternatives':json.loads(secondary['ASCII_alternatives']),'native_box_xyxy':json.loads(secondary['native_box_xyxy']),'source_file':handsource['source'],'source_sha256':secondary['source_sha256'],'array_crop':secondary['array_crop'],'array_crop_sha256':manifest_hashes[secondary['array_crop']],'exact_primary_character_agreement':secondary['ASCII_observation']==cipher[active-1],'primary_character_within_source_alternatives':cipher[active-1] in json.loads(secondary['ASCII_alternatives']),'source_letter_changed':False}
        if secondary['ASCII_observation']!=cipher[active-1]:secondary_differences.append({'active_position':active,'primary':cipher[active-1],'secondary':secondary['ASCII_observation'],'alternatives':json.loads(secondary['ASCII_alternatives']),'literal_plaintext_position':x['plaintext_position_1indexed'],'source_record':r['secondary_hand_observation']})
        full.append(r)
    assert len(full)==144 and [x['active_cipher_position_1indexed'] for x in full]==list(range(1,145))
    assert {x['plaintext_position_1indexed'] for x in full}==set(range(1,145))
    assert [x['active_position'] for x in secondary_differences]==[74]
    grouped_diff=[{'active_position':i+1,'primary':a,'grouped_copy':b,'grouped_copy_source_sha256':grouped['source_sha256'],'grouped_copy_native_box_xyxy':grouped['native_box_xyxy'],'source_letters_changed':False} for i,(a,b) in enumerate(zip(cipher,grouped['active_stream'])) if a!=b]
    assert grouped_diff==[{'active_position':100,'primary':'A','grouped_copy':'H','grouped_copy_source_sha256':grouped['source_sha256'],'grouped_copy_native_box_xyxy':grouped['native_box_xyxy'],'source_letters_changed':False}]
    cancelled=next(x for x in raw if x['raw_placement_index_1based']==139);assert cancelled['active_index_1based'] is None and cancelled['ASCII_final_visible'] is None and cancelled['underlay_ASCII'] is None
    overlay=next(x for x in raw if x['raw_placement_index_1based']==28);assert overlay['ASCII_final_visible']=='F' and overlay['underlay_ASCII'] is None
    full_by_raw={x['primary_raw_position_1indexed']:x for x in full};rawcert=[]
    for placement in raw:
        r={'frozen_source_record':placement,'source_file':typed['source_path'],'raw_placement_preserved':True,'active_forward_certificate':full_by_raw.get(placement['raw_placement_index_1based']),'claim':'EXPLICIT_CANCELLED_UNREADABLE_SLOT_NO_PLAINTEXT_ASSIGNED' if placement['active_index_1based'] is None else 'CURRENT_ACTIVE_CHARACTER_EXACTLY_REPRODUCED'}
        rawcert.append(r)
    save('ALL_144_ACTIVE_SOURCE_FORWARD_CERTIFICATE_v1.json',full)
    save('ALL_145_RAW_PLACEMENTS_SOURCE_CERTIFICATE_v1.json',rawcert)
    save('SOURCE_LAYER_AND_SECONDARY_DISCREPANCIES_v1.json',{'current_F_overlay_raw_28':overlay,'cancelled_raw_139':cancelled,'four_U_W_hand_shape_holds':handsource['U_W_source_holds'],'secondary_array_literal_differences':secondary_differences,'additional_grouped_copy_literal_differences':grouped_diff,'underlay_reconstructed':False,'semantic_letter_repairs':False,'scope':'Current active primary witness is authoritative for this forward certificate; secondary readings remain separately frozen.'})
    save('PHYSICAL_PUBLIC_KEY_CERTIFICATE_v1.json',{'status':'PASS_PUBLICLY_SUPPLIED_KEY_GEOMETRY_AND_ROTATION_COVERAGE','side':6,'holes_1indexed':list(holes),'source_holes_zeroindexed':grid['holes_row_column_0based'],'coarse_mask_rows':grid['rows_cutout_mask'],'cut_cells':9,'solid_cells':27,'rotation_orbits_1indexed':[list(x) for x in orbits],'one_hole_per_orbit':True,'four_turn_permutation_unique_cells':36,'source_file':grid['source'],'source_sha256':grid['source_sha256'],'physical_geometry_record':str(gridpath.relative_to(ROOT)),'physical_geometry_record_sha256':sha(gridpath),'all36native_cell_memberships_visually_checked':True,'nine_cut_cells_eight_physical_notch_window_regions':True,'finer_paper_ruling_not_silently_equal_to_coarse_cut_cells':True,'orientation_marks_literal':grid['orientation_notations'],'procedure_scope':'I initially top; moving II,III,IV to top is clockwise by geometry. Hole scanning/write-read mechanism uses precontrolled ACA-style registered row-major family, not decoded language.','boundary_uncertainty_pixels':10,'public_key_was_supplied_not_recovered':True})
    mech=json.loads((OUT/'MECHANICAL_AUDIT_SUMMARY_v1.json').read_text())
    chronology={'root_source_and_key_freeze_utc':rootfreeze['frozen_at_utc'],'root_first_all_eight_output_utc':json.loads((ROOT/'reports/target_decode_v1/ALL_EIGHT_REGISTERED_DECODES_v1.json').read_text())['generated_utc'],'cold_primary_record_freeze_utc':typed['frozen_utc'],'cold_secondary_record_freeze_utc':handsource['frozen_utc'],'cold_physical_key_record_freeze_utc':grid['frozen_utc'],'cold_full_145_placement_record_freeze_utc':json.loads(rawpath.read_text())['frozen_utc'],'cold_final_manifest_utc':manifest['created_utc'],'cold_final_seal_utc':seal['sealed_utc'],'independent_codec_precomparison_seal_utc':pre['sealed_at_utc'],'scope_note':'Root source/key freeze precedes root first output. Cold final geometry/placement/manifest seals follow root first output, but the cold worker reports no candidate exposure or decoding. This candidate audit is exposed to the approved candidate records. No global before-any-candidate or fully blinded source-observer claim.'}
    visual_receipt={'full_typed_original_view':'3024x1545 native view','full_notebook_original_view':'whole 3024x4032 source displayed with provider resize to2752x3669; detailed claims use native retained crops','native_detailed_views':['all5 typed rows','black F correction crop','last-row physical six-placement group','complete physical grille','all36 native grille-cell atlas','array3 native crop with position74 shape','lower grouped-copy native crop with position100 H'],'literal_source_values_unchanged':True,'visual_target_candidate_exposure':True,'cold_observer_candidate_exposure_reported':False,'native_row_and_key_provenance_checked':True}
    summary={'status':'PASS_CURRENT_ACTIVE_144_SOURCE_FORWARD_AUDIT_WITH_EXPLICIT_SOURCE_HOLDS','completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'primary_active_positions_certified':144,'raw_placements_preserved':145,'primary_active_bytes_match_root_preferred':True,'primary_active_bytes_match_cold_source':True,'key_nine_holes_match_root_and_cold_geometry':True,'literal_plaintext_unchanged':literal,'literal_semantic_intent':'HELD; retain DIELONDON and MITLBOMBEN exactly','all_eight_registered_decodes_independently_checked':True,'all_eight_roundtrip_active144':True,'fixed_literal_exact_registered_conventions':mech['fixed_literal_exact_conventions'],'single_orbit_legal_key_modifications':27,'equal_neighbors':mech['neighbors_exact_source_equal'],'equal_neighbor_output_groups':mech['duplicate_neighbor_output_groups'],'source_F_overlay_28_original_underlay':None,'source_cancelled_raw139_original_letter':None,'secondary_74_U_W_and_grouped_copy_100_A_H_preserved':True,'cold_source_manifest_sha256':sha(manifestpath),'cold85artifacts_and2source_original_hashes_verified':True,'independent_codec_sha256':sha(codepath),'checker_sha256':sha(Path(__file__)),'checker_imports_root_grille_code':False,'chronology':chronology,'visual_source_audit':visual_receipt,'claim_scope':'Known-key-assisted exact mechanical reading of the 144 current active primary letters under explicit cancellation role; no uncorrected145 recovery, semantic repair, exhaustive uniqueness, unknown-key discovery, priority or external acceptance claim.','remaining_source_holds':['unknown violet underlay at current F28','unknown cancelled glyph raw139 and explicitly conditional cancellation role','four handwritten U/W source alternatives','secondary literal W versus primary U at74','additional grouped-copy H versus primary A at100','geometric boundary context ±10px and unreadable stencil pencil notations']}
    save('FINAL_CANDIDATE_AUDIT_SUMMARY_v1.json',summary)
    for item in manifest['files']+manifest['input_originals']:
        p=Path(item['path']);p=p if p.is_absolute() else ROOT/p;assert sha(p)==item['sha256']
    for item in pre['files']:assert sha(ROOT/item['path'])==item['sha256']
    print(json.dumps({k:summary[k] for k in ['status','primary_active_positions_certified','raw_placements_preserved','key_nine_holes_match_root_and_cold_geometry','single_orbit_legal_key_modifications','equal_neighbors','equal_neighbor_output_groups','checker_imports_root_grille_code']}))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mechanical-only',action='store_true');parser.add_argument('--source-certify',action='store_true');args=parser.parse_args()
    if args.mechanical_only==args.source_certify:parser.error('choose exactly one of --mechanical-only or --source-certify')
    if args.source_certify:certify_physical_source();return
    OUT.mkdir(parents=True,exist_ok=True)
    prepath=ROOT/'reports/independent_method_v1/INDEPENDENT_CODEC_PRECOMPARISON_SEAL_v1.json'
    pre=json.loads(prepath.read_text())
    for item in pre['files']:assert sha(ROOT/item['path'])==item['sha256']
    codepath=ROOT/'scripts/independent_grille_v1.py'
    assert sha(codepath)=='94b5e3d7a34f60fad1262f8467b67d8a5915cca9c355590b2564d98c58ac35e1'
    spec=importlib.util.spec_from_file_location('sealed_independent_grille_v1',codepath);codec=importlib.util.module_from_spec(spec);sys.modules[spec.name]=codec;spec.loader.exec_module(codec)
    sourcepath=ROOT/'data/root_source_v1/ROOT_SOURCE_FREEZE_v1.json';source=json.loads(sourcepath.read_text())
    cipherpath=ROOT/'data/root_source_v1/preferred_supplied_hand_cipher_v1.txt';text=cipherpath.read_text();cipher=text[:-1] if text.endswith('\n') else text
    assert '\n' not in cipher and len(cipher)==144 and cipher==source['supplied_hand_stream']
    regpath=ROOT/'config/GRILLE_SEARCH_REGISTRATION_v1.json';registration=json.loads(regpath.read_text())
    policy=ROOT/'reports/ROOT_TARGET_SOURCE_POLICY_v1.json';rootresults=ROOT/'reports/target_decode_v1/ALL_EIGHT_REGISTERED_DECODES_v1.json';claimed=json.loads(rootresults.read_text())
    n=source['physical_key']['side'];coords=[tuple(h) for h in source['physical_key']['holes_zeroindexed']];assert n==6 and len(coords)==9
    holes=tuple(sorted(r*n+c+1 for r,c in coords));assert codec.validate_grille(n,holes)==holes
    orbit_table=codec.rotation_orbits(n);assert len(orbit_table)==9
    assert all(len(set(orbit)&set(holes))==1 for orbit in orbit_table)
    arrays=source['supplied_hand_arrays'];assert len(arrays)==4 and all(len(a)==6 and all(len(row)==6 for row in a) for a in arrays)
    assert ''.join(row for array in arrays for row in array)==cipher
    raw=''.join(row.replace(' ','') for row in source['primary_typed_rows_raw']);assert len(raw)==145 and raw[138]=='?'
    assert raw[:138]+raw[139:]==cipher and raw[27]=='F'
    raw_rejection=None
    try:codec.decrypt(raw,n,holes)
    except codec.GrilleError as exc:raw_rejection=str(exc)
    assert raw_rejection is not None
    starts=registration['hypothesis_budget']['start_orientations'];directions=registration['hypothesis_budget']['rotation_directions'];assert starts==[0,1,2,3] and set(directions)=={-1,1}
    results=[]
    for start in starts:
        for direction in directions:
            plain=codec.decrypt(cipher,n,holes,start_turn=start,direction=direction)
            forward=codec.encrypt(plain,n,holes,start_turn=start,direction=direction)
            previous=next(x for x in claimed['results'] if x['start']==start and x['direction']==direction)
            assert previous['plaintext_literal']==plain and previous['forward_ciphertext']==forward and forward==cipher
            results.append({'start_turn':start,'start_angle_degrees':90*start,'direction':direction,'literal_plaintext':plain,'literal_plaintext_sha256':digest(plain),'length':len(plain),'own_forward_ciphertext':forward,'cipher_sha256':digest(forward),'all_144_active_letters_match':True,'root_literal_matches_independent_decode':True,'root_forward_matches_independent_forward':True,'semantically_edited':False})
    selected=next(x for x in results if x['start_turn']==0 and x['direction']==1);literal=selected['literal_plaintext'];visit=codec.permutation(n,holes,start_turn=0,direction=1)
    mapping=[]
    for block in range(4):
        for k,cell0 in enumerate(visit):
            active=block*36+cell0+1;payload=block*36+k+1;rawpos=active if active<139 else active+1
            mapping.append({'active_cipher_position_1indexed':active,'primary_raw_position_1indexed':rawpos,'plaintext_position_1indexed':payload,'block_1indexed':block+1,'grid_cell_1indexed':cell0+1,'grid_row_zeroindexed':cell0//n,'grid_column_zeroindexed':cell0%n,'turn_in_payload_1indexed':k//9+1,'hole_rank_in_turn_1indexed':k%9+1,'source_character':cipher[active-1],'literal_payload_character':literal[payload-1],'exact_match':cipher[active-1]==literal[payload-1],'source_event':'current_visible_F_over_unknown_underlay' if rawpos==28 else None,'physical_source_provenance':'PENDING_COLD_SOURCE_FREEZE'})
    mapping.sort(key=lambda x:x['active_cipher_position_1indexed'])
    assert len(mapping)==144 and all(x['exact_match'] for x in mapping)
    assert {x['plaintext_position_1indexed'] for x in mapping}==set(range(1,145))
    fixed_conventions=[]
    for start in starts:
        for direction in directions:
            forward=codec.encrypt(literal,n,holes,start_turn=start,direction=direction);mismatch=[i+1 for i,(a,b) in enumerate(zip(forward,cipher)) if a!=b]
            fixed_conventions.append({'start_turn':start,'direction':direction,'fixed_literal_plaintext_sha256':digest(literal),'forward_ciphertext':forward,'exact_cipher_equal':forward==cipher,'matched_active_positions':144-len(mismatch),'mismatch_active_positions':mismatch,'permutation_sha256':digest(json.dumps(codec.permutation(n,holes,start_turn=start,direction=direction))),'selected_convention':start==0 and direction==1})
    orbit_by_cell={cell:orbit for orbit in orbit_table for cell in orbit}
    neighbors=[]
    for sourcehole in holes:
        for replacement in orbit_by_cell[sourcehole]:
            if replacement==sourcehole:continue
            changed=tuple(sorted(set(holes)-{sourcehole}|{replacement}));assert len(changed)==9 and codec.validate_grille(n,changed)==changed
            forward=codec.encrypt(literal,n,changed,start_turn=0,direction=1);mismatch=[i+1 for i,(a,b) in enumerate(zip(forward,cipher)) if a!=b]
            neighbors.append({'removed_hole_1indexed':sourcehole,'replacement_hole_1indexed':replacement,'removed_zeroindexed_row_column':list(divmod(sourcehole-1,n)),'replacement_zeroindexed_row_column':list(divmod(replacement-1,n)),'changed_holes_1indexed':list(changed),'same_orbit_1indexed':list(orbit_by_cell[sourcehole]),'legal_grille_coverage':True,'start_turn':0,'direction':1,'fixed_literal_plaintext_sha256':digest(literal),'forward_ciphertext':forward,'exact_cipher_equal':forward==cipher,'matched_active_positions':144-len(mismatch),'mismatch_active_positions':mismatch})
    assert len(neighbors)==27 and len({tuple(x['changed_holes_1indexed']) for x in neighbors})==27
    equal_neighbors=[x for x in neighbors if x['exact_cipher_equal']];equal_conventions=[x for x in fixed_conventions if x['exact_cipher_equal']]
    cipher_groups={}
    for i,x in enumerate(neighbors,1):cipher_groups.setdefault(x['forward_ciphertext'],[]).append(i)
    duplicated_neighbor_outputs=[{'neighbor_record_ids':ids,'forward_ciphertext':c} for c,ids in cipher_groups.items() if len(ids)>1]
    save('ALL_EIGHT_INDEPENDENT_DECODES_v1.json',{'target_source_assistance':'publicly supplied literal physical grille','cipher_sha256':digest(cipher),'independent_codec_sha256':sha(codepath),'all_registered_cases_checked':8,'all_cases_roundtrip_144':True,'results':results,'interpretation_limit':'Each of eight own decoded strings roundtrips by construction; exact roundtrip alone does not select a convention.'})
    save('ALL_144_ACTIVE_MAPPING_MECHANICAL_v1.json',mapping)
    save('FIXED_LITERAL_ALL_EIGHT_CONVENTIONS_v1.json',fixed_conventions)
    save('FIXED_LITERAL_27_SINGLE_ORBIT_NEIGHBORS_v1.json',{'cases':neighbors,'equal_to_source_cases':equal_neighbors,'equal_neighbor_forward_outputs':duplicated_neighbor_outputs,'fixed_literal_sha256':digest(literal),'full_legal_grille_key_space_size':4**9,'tested_neighborhood_size':27,'scope':'Only one hole changed within its own rotation orbit, fixed literal and convention. Not an exhaustive key or cipher-family search.'})
    summary={'status':'MECHANICAL_PASS_PHYSICAL_SOURCE_CERTIFICATE_PENDING','completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'preferred_active_length':144,'raw_transcription_extent_with_cancelled_slot':145,'raw_cancelled_position':139,'raw_current_F_overlay_position':28,'raw_145_whole_block_rejected':True,'raw_145_rejection_reason':raw_rejection,'full_square_blocks':4,'side':6,'holes_zeroindexed':[list(x) for x in coords],'holes_1indexed':list(holes),'four_rotation_coverage_unique_cells':36,'independent_codec_sha256':sha(codepath),'independent_precomparison_seal_sha256':sha(prepath),'root_grille_code_imported':False,'eight_decodes_match_root_literal_records':True,'eight_own_forwards_exact_active_144':True,'fixed_literal_exact_conventions':[{'start_turn':x['start_turn'],'direction':x['direction']} for x in equal_conventions],'single_orbit_neighbor_count':27,'neighbors_exact_source_equal':len(equal_neighbors),'duplicate_neighbor_output_groups':len(duplicated_neighbor_outputs),'literal_selected_start':0,'literal_selected_direction':1,'selected_literal':literal,'literal_semantic_edit':False,'semantic_intent_status':'HELD; DIELONDON and MITLBOMBEN remain literal, no smooth German replacement','scope':'Known-key-assisted mechanical reading of current active 144 letters only. Not an original uncorrected145 reading, unknown-key breakthrough, global uniqueness, priority or external acceptance claim.','input_records':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in [sourcepath,cipherpath,regpath,policy,rootresults]],'physical_source_certification':'PENDING_COLD_SOURCE_FREEZE'}
    save('MECHANICAL_AUDIT_SUMMARY_v1.json',summary)
    for item in pre['files']:assert sha(ROOT/item['path'])==item['sha256']
    print(json.dumps({k:summary[k] for k in ['status','preferred_active_length','eight_decodes_match_root_literal_records','single_orbit_neighbor_count','neighbors_exact_source_equal','duplicate_neighbor_output_groups','fixed_literal_exact_conventions']}))

if __name__=='__main__':main()
