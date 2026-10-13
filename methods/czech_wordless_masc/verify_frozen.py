#!/usr/bin/env python3
"""Offline verification of all portable frozen artifacts, scores, trials and metrics."""
import array
import collections
import json
import random
import sys
from common import MODULE, FROZEN, load, require, safe_path, sha, verify_pins
from grade_controls import grade

def main():
    pins=load(MODULE/'MODULE_SHA256.json')
    verify_pins(MODULE,pins['artifacts'])
    verify_pins(FROZEN,load(FROZEN/'INFERENCE_PINS.json')['artifacts'])
    manifest=load(FROZEN/'inference_inputs/CONTROL_MANIFEST.json')
    config=load(FROZEN/'FROZEN_RUN_CONFIG.json')
    require(sha(MODULE/'generic_solver.cpp')=='651b888047c939dd0ce6e0d84805b8a4beba45eb6b0d8ebfe3ab43eb60681276','C++ source differs from original')
    model=array.array('f');model.frombytes(safe_path(FROZEN,manifest['model_path']).read_bytes())
    if sys.byteorder!='little':model.byteswap()
    require(model.itemsize==4 and len(model)==27**4,'Wrong model layout')
    freq=[int(v) for v in safe_path(FROZEN,manifest['frequency_path']).read_text().split()]
    require(sorted(freq)==list(range(26)), 'Invalid training-frequency permutation')
    controls={r['id']:r for r in manifest['controls']}
    def score(text):
        nums=[ord(c)-97 for c in text]
        return sum(model[((nums[i]*27+nums[i+1])*27+nums[i+2])*27+nums[i+3]] for i in range(len(nums)-3))
    checked_trials=0
    for cid, control in controls.items():
        cipher=[int(v) for v in safe_path(FROZEN,control['cipher_path']).read_text().split()]
        require(len(cipher)==control['length'] and all(0<=c<26 for c in cipher),'Invalid synthetic input: '+cid)
        result=load(FROZEN/'inference_outputs'/(cid+'.sa.json'))
        require(result['seed']==control['seed'] and result['restarts']==18 and result['steps']==100000 and len(result['trials'])==18,'Fixed seed/budget mismatch: '+cid)
        require(config['restarts_per_main_control']==18 and config['steps_per_restart']==100000,'Original budget mismatch')
        for index, trial in enumerate(result['trials']):
            require(trial['restart']==index and sorted(trial['key'])==list(range(26)),'Invalid trial key/index: '+cid)
            require(''.join(chr(trial['key'][c]+97) for c in cipher)==trial['plain'],'Invalid trial decode: '+cid)
            require(score(trial['plain'])==trial['score'],'Incorrect trial score: '+cid)
            checked_trials+=1
        winner=max(result['trials'],key=lambda r:r['score'])
        require(all(result[k]==winner[k] for k in ['key','plain','score']), 'Main-run winner mismatch: '+cid)
        require(result['cipher_solved'] is False, 'Generic solver status field changed')
        baseline=load(FROZEN/'inference_outputs'/(cid+'.frequency_baseline.json'))
        hist=collections.Counter(cipher);order=sorted(range(26),key=lambda c:(-hist[c],c));key=[0]*26
        for c,p in zip(order,freq):key[c]=p
        require(key==baseline['key'] and baseline['plain']==''.join(chr(key[c]+97) for c in cipher),'Frequency baseline differs: '+cid)
        if control['kind']=='matched_frequency_shuffle':
            matched=[int(v) for v in safe_path(FROZEN,controls[control['matched_positive']]['cipher_path']).read_text().split()]
            shuffled=matched[:];random.Random(control['seed']).shuffle(shuffled)
            require(shuffled==cipher and matched!=cipher and collections.Counter(matched)==hist,'Shuffle does not reproduce: '+cid)
    ids=list(controls);report=grade(FROZEN,FROZEN/'inference_outputs',ids)
    audit=load(MODULE/'provenance/INDEPENDENT_AUDIT_SUMMARY.json')
    require(audit['checks_passed']==156 and audit['checks_failed']==0,'Original audit summary changed')
    require(report['aggregate']==audit['aggregate'],'Aggregate differs from original independent audit')
    metrics=load(FROZEN/'METRICS.json')
    require(report['aggregate']['exact_plaintexts']==metrics['exact_plaintexts']==6,'Exact count differs')
    require(report['aggregate']['characters_correct']==metrics['micro_character_correct']==2400,'Character count differs')
    require(report['aggregate']['characters_denominator']==metrics['micro_character_denominator']==2400,'Character denominator differs')
    require(report['aggregate']['baseline_characters_correct']==metrics['baseline_micro_character_correct']==596,'Baseline count differs')
    require(metrics['inference_completed_utc']<metrics['gold_first_opened_by_grader_utc']<=metrics['graded_utc'],'Recorded grading order differs')
    originals=load(MODULE/'provenance/ORIGINAL_ARTIFACT_HASHES.json')['artifacts']
    for row in originals:
        if row.get('public_bytes_identical'):
            require(sha(safe_path(MODULE,row['public_path']))==row['sha256'],'Public original bytes changed')
    print(json.dumps({'status':'PASS','record_type':'current offline artifact verification, not new inference or new independent source audit','module_files_hash_verified':len(pins['artifacts']),'retained_controls_verified':len(controls),'retained_trials_verified':checked_trials,'aggregate':report['aggregate'],'original_independent_checks_passed':156,'historical_targets_solved':0}))

if __name__=='__main__':main()
