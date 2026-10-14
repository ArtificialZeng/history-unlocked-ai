#!/usr/bin/env python3
"""Offline standard-library verification; no network, compiler or inference run."""
import collections
import hashlib
import json
import random
import sys
sys.dont_write_bytecode = True
from common import MODULE, FROZEN, load, require, safe_path, sha, verify_pins
from grade_controls import grade
from masked_profile import CPP_SHA256, MODEL_SHA256, apply_masks, baseline, gap_windows, make_masks, permutation, read_cipher, read_model, render, score

def main():
    checks = 0
    def check(value, message):
        nonlocal checks
        checks += 1
        require(value, message)
    pins = load(MODULE/'MODULE_SHA256.json')
    expected_files = {r['path'] for r in pins['artifacts']}
    actual_files = {str(p.relative_to(MODULE)) for p in MODULE.rglob('*') if p.is_file()}
    check(actual_files == expected_files | {'MODULE_SHA256.json'}, 'Module manifest does not cover its complete file set')
    verify_pins(MODULE, pins['artifacts'])
    verify_pins(FROZEN, load(FROZEN/'INFERENCE_PINS.json')['artifacts'])
    config = load(FROZEN/'inference_inputs/RUN_CONFIG.json')
    profile = load(FROZEN/'PROFILE_PREREGISTRATION.json')
    check(sha(MODULE/'generic_solver.cpp') == CPP_SHA256, 'C++ source differs from original')
    check(sha(safe_path(FROZEN, config['model_path'])) == MODEL_SHA256, 'Train-only model bytes differ')
    check(config['restarts'] == 18 and config['steps_per_restart'] == 100000 and config['unknown_sentinel'] == 26,
          'Fixed original profile budget/sentinel changed')
    check(profile['lengths'] == [400,400,500,500,600,600] and profile['sentinel'] == 26, 'Original registration differs')
    model = read_model(safe_path(FROZEN, config['model_path']))
    frequency = [int(v) for v in safe_path(FROZEN, config['frequency_path']).read_text().split()]
    check(sorted(frequency) == list(range(26)), 'Wrong training-frequency ordering')
    floor = model[27**4-1]
    sentinel_cells = 0
    for a in range(27):
        for b in range(27):
            for c in range(27):
                for d in range(27):
                    if 26 in (a,b,c,d):
                        check(model[((a*27+b)*27+c)*27+d] == floor, 'Sentinel quadgram is not the constant floor')
                        sentinel_cells += 1
    controls = {c['id']:c for c in config['controls']}
    check(list(controls) == ['P01','P02','P03','P04','P05','P06','N01','N02','N03'], 'Control inventory differs')
    gold = load(FROZEN/'grading_gold/gold.json')['controls']
    old = load(MODULE/'REBUILD_EXCLUSIONS.json')
    check(len(old['document_ids']) == len(set(old['document_ids'])) == 6, 'Old-six exclusion inventory differs')
    check([hashlib.sha256(i.encode()).hexdigest() for i in old['document_ids']] == old['document_id_sha256'], 'Old-six ID hashes differ')
    metadata = load(FROZEN/'BUILD_METADATA.json')
    check(old['document_id_sha256'] == metadata['old_document_id_sha256'], 'Old-six exclusion differs from original build')
    check(len({g['document_id'] for g in gold}) == 6 and not {g['document_id'] for g in gold} & set(old['document_ids']), 'New documents overlap old controls')
    for number, g in enumerate(gold):
        cid, control = g['id'], controls[g['id']]
        code = read_cipher(safe_path(FROZEN, control['cipher_path']))
        check(g['original_length'] == len(g['plain']) == profile['lengths'][number], 'Original length differs: '+cid)
        check(g['permutation_seed'] == control['solver_seed'] == profile['permutation_seeds'][number], 'Permutation seed differs: '+cid)
        check(g['mask_seed'] == profile['mask_seeds'][number], 'Mask seed differs: '+cid)
        enc, dec = permutation(g['permutation_seed'])
        check(enc == g['enc_plain_to_cipher'] and dec == g['dec_cipher_to_plain'], 'Seeded permutation differs: '+cid)
        masks = make_masks(len(g['plain']), g['mask_seed'])
        check(masks == g['masks'], 'Seeded masks or actual gap lengths differ: '+cid)
        check(sum(m['kind'] == 'unknown_run' for m in masks) == g['unknown_runs'] == 13
              and sum(m['kind'] == 'single_erasure' for m in masks) == g['single_erasures'] == 17, 'Mask counts differ: '+cid)
        masked = set()
        for m in masks:
            positions = set(range(m['start'], m['start']+m['length']))
            check(not masked & positions and all(0 <= i < len(g['plain']) for i in positions), 'Overlapping/outside mask: '+cid)
            check(m['length'] == 1 if m['kind'] == 'single_erasure' else 2 <= m['length'] <= 5, 'Actual gap length differs: '+cid)
            masked |= positions
        rebuilt, origins = apply_masks(g['plain'], enc, masks)
        check(rebuilt == code and origins == g['cipher_token_to_original_position'], 'Input/original-coordinate replay differs: '+cid)
        check([i for i in range(len(g['plain'])) if i not in masked] == g['known_original_positions'], 'Known denominator differs: '+cid)
        check(len(masked) == g['unknown_original_character_count'], 'Unknown original count differs: '+cid)
    audit = load(MODULE/'provenance/INDEPENDENT_AUDIT_SUMMARY.json')
    audit_gaps = {r['id']:r for r in audit['gap_scoring_denominators']}
    trials = 0
    for cid, control in controls.items():
        code = read_cipher(safe_path(FROZEN, control['cipher_path']))
        check(len(code) == control['tokens'] and code.count(26) == control['gap_marker_count'] == 30, 'Cipher profile differs: '+cid)
        check(sha(safe_path(FROZEN, control['cipher_path'])) == control['cipher_sha256'], 'Cipher hash differs: '+cid)
        result = load(FROZEN/'inference_outputs'/(cid+'.sa.json'))
        check(result['seed'] == control['solver_seed'] and result['restarts'] == 18 and result['steps'] == 100000 and len(result['trials']) == 18, 'Retained fixed budget differs: '+cid)
        for index, trial in enumerate(result['trials']):
            check(trial['restart'] == index, 'Restart index differs: '+cid)
            check(render(code, trial['key']) == trial['plain'], 'Retained trial rendering differs: '+cid)
            check(score(trial['plain'], model) == trial['score'], 'Retained trial score differs: '+cid)
            trials += 1
        winner = max(result['trials'], key=lambda r:r['score'])
        check(all(result[k] == winner[k] for k in ['key','plain','score']), 'First highest-score winner differs: '+cid)
        check(result['cipher_solved'] is False, 'Generic core status field differs: '+cid)
        check(load(FROZEN/'inference_outputs'/(cid+'.frequency_baseline.json')) == baseline(code, frequency), 'Frequency baseline differs: '+cid)
        gaps = gap_windows(code)
        check(all(gaps[k] == audit_gaps[cid][k] for k in gaps), 'Score denominator differs: '+cid)
        check(floor*gaps['sentinel_containing_windows'] == audit_gaps[cid]['constant_floor_penalty'], 'Constant gap penalty differs: '+cid)
        if control['kind'] != 'positive':
            matched = read_cipher(safe_path(FROZEN, controls[control['matched_positive']]['cipher_path']))
            observed = [c for c in matched if c != 26]
            random.Random(control['solver_seed']).shuffle(observed)
            it = iter(observed)
            shuffled = [26 if c == 26 else next(it) for c in matched]
            check(shuffled == code and matched != code, 'Seeded observed-only shuffle differs: '+cid)
            check(collections.Counter(code) == collections.Counter(matched), 'Negative histogram differs: '+cid)
            check([i for i,c in enumerate(code) if c == 26] == [i for i,c in enumerate(matched) if c == 26], 'Negative gap locations differ: '+cid)
    report = grade(FROZEN, FROZEN/'inference_outputs', list(controls))
    metrics = load(FROZEN/'METRICS.json')
    check(report['aggregate'] == metrics['aggregate'] == audit['aggregate'], 'Original aggregate arithmetic differs')
    check(report['positives'] == metrics['positives'] and report['negatives'] == metrics['negatives'], 'Per-control metrics differ')
    check(report['wrong_observed_positions'] == load(FROZEN/'grading_gold/FAILURES.json')['wrong_observed_positions'], 'Retained failure coordinates differ')
    check(len(report['wrong_observed_positions']) == 1 and report['wrong_observed_positions'][0]['id'] == 'P05', 'P05 failure lost')
    check(audit['checks_passed'] == 3156 and audit['checks_failed'] == 0 and audit['independent_binary_replay_performed'] is False, 'Original audit scope differs')
    execution = load(MODULE/'provenance/ORIGINAL_EXECUTION_SUMMARY.json')
    check(execution['finished_utc'] < execution['grading_started_utc'] <= execution['grading_finished_utc'], 'Recorded original grading order differs')
    check(execution['all_nine_finished_successfully'] and len(execution['records']) == 9, 'Original execution count differs')
    check(execution['first_safe_administration']['producer_late_seconds'] == 146.531442
          and execution['first_safe_administration']['referee_late_seconds'] == 40.326905, 'Administrative lateness provenance differs')
    packaging = load(MODULE/'provenance/PACKAGING_CHECK_SUMMARY.json')
    replay = packaging['fresh_P05_replay']
    check(packaging['checks_passed'] == 19 and packaging['checks_failed'] == 0
          and packaging['one_fresh_solver_process_only'] is True, 'Separate packaging check scope differs')
    check(replay['restarts'] == 18 and replay['steps'] == 100000 and replay['retained_trials'] == 18
          and replay['bytes_identical_to_original'] is True
          and replay['output_sha256'] == sha(FROZEN/'inference_outputs/P05.sa.json'), 'Recorded separate P05 replay differs')
    check(replay['known_characters_correct'] == 537 and replay['known_characters'] == 538
          and replay['candidate_key_forward_correct'] == 538 and replay['gold_recovery_forward_correct'] == 537
          and replay['retained_known_errors'] == 1 and replay['whole_original_profile_retested'] is False,
          'P05 packaging failure or forward distinction differs')
    for row in load(MODULE/'provenance/ORIGINAL_ARTIFACT_HASHES.json')['artifacts']:
        if row.get('public_path'):
            path = safe_path(MODULE, row['public_path'])
            check(sha(path) == row['public_sha256'], 'Public adaptation hash differs: '+row['public_path'])
            if row.get('public_bytes_identical'):
                check(sha(path) == row['sha256'], 'Original public bytes differ: '+row['public_path'])
    print(json.dumps({'status':'PASS', 'record_type':'Current offline artifact verification; no new inference or independent raw-source audit',
        'module_files_hash_verified':len(pins['artifacts']), 'retained_controls_verified':len(controls),
        'retained_trials_verified':trials, 'current_checks_passed':checks, 'sentinel_model_cells_checked':sentinel_cells,
        'aggregate':report['aggregate'], 'original_independent_checks_passed':3156,
        'retained_known_position_errors':len(report['wrong_observed_positions']), 'historical_targets_solved':0}))

if __name__ == '__main__':
    main()
