#!/usr/bin/env python3
"""Post-inference synthetic grading. Never overwrite the original frozen metrics."""
import argparse
import datetime
from pathlib import Path
from common import FROZEN, load, require, safe_path, save, verify_pins

def grade(bundle, results, ids):
    gold={r['id']:r for r in load(bundle/'grading_gold/gold.json')['controls']}
    controls={r['id']:r for r in load(bundle/'inference_inputs/CONTROL_MANIFEST.json')['controls']}
    rows=[];negatives=[]
    for cid in ids:
        control=controls[cid];cipher=[int(v) for v in safe_path(bundle,control['cipher_path']).read_text().split()]
        result=load(results/(cid+'.sa.json'));baseline=load(results/(cid+'.frequency_baseline.json'))
        require(len(result['plain'])==len(cipher) and sorted(result['key'])==list(range(26)), 'Invalid candidate length or key')
        require(result['plain']==''.join(chr(result['key'][c]+97) for c in cipher), 'Candidate decode differs')
        inverse=[result['key'].index(p) for p in range(26)]
        candidate_forward=sum(inverse[ord(p)-97]==c for p,c in zip(result['plain'],cipher))
        if cid not in gold:
            negatives.append({'id':cid,'length':len(cipher),'score':result['score'],'no_known_plaintext_claim':True});continue
        truth=gold[cid];observed=set(cipher)
        require(len(truth['plain'])==len(cipher), 'Wrong gold length')
        require([truth['enc_plain_to_cipher'][ord(p)-97] for p in truth['plain']]==cipher, 'Gold does not reconstruct input')
        rows.append({'id':cid,'length':len(cipher),'exact_plaintext':result['plain']==truth['plain'],'characters_correct':sum(a==b for a,b in zip(result['plain'],truth['plain'])),'observed_key_correct':sum(result['key'][c]==truth['dec_cipher_to_plain'][c] for c in observed),'observed_key_denominator':len(observed),'baseline_characters_correct':sum(a==b for a,b in zip(baseline['plain'],truth['plain'])),'baseline_exact_plaintext':baseline['plain']==truth['plain'],'candidate_forward_correct':candidate_forward,'gold_forward_correct':sum(truth['enc_plain_to_cipher'][ord(p)-97]==c for p,c in zip(result['plain'],cipher))})
    aggregate={'exact_plaintexts':sum(r['exact_plaintext'] for r in rows),'characters_correct':sum(r['characters_correct'] for r in rows),'characters_denominator':sum(r['length'] for r in rows),'observed_key_correct':sum(r['observed_key_correct'] for r in rows),'observed_key_denominator':sum(r['observed_key_denominator'] for r in rows),'baseline_characters_correct':sum(r['baseline_characters_correct'] for r in rows),'baseline_exact_plaintexts':sum(r['baseline_exact_plaintext'] for r in rows),'candidate_forward_correct':sum(r['candidate_forward_correct'] for r in rows),'gold_forward_correct':sum(r['gold_forward_correct'] for r in rows)}
    return {'selected_control_ids':ids,'positive_count':len(rows),'negative_count':len(negatives),'aggregate':aggregate,'positives':rows,'negatives':negatives,'scores_are_probabilities':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,default=FROZEN)
    parser.add_argument('--results',type=Path,required=True)
    args=parser.parse_args();bundle=args.bundle.resolve();results=args.results.resolve()
    require(not results.is_relative_to(FROZEN.resolve()), 'Use verify_frozen.py for original artifacts; grading writes new replay only')
    complete=load(results/'INFERENCE_COMPLETION.json')
    require(complete['all_selected_completed'], 'Grading requires completed selected inference runs')
    verify_pins(results,load(results/'RESULT_PINS.json')['artifacts'])
    ids=complete['completed_ids'];report=grade(bundle,results,ids)
    report.update({'record_type':'new public replay grading, not original frozen metrics','graded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inference_completed_utc':complete['at_utc'],'full_six_positive_profile_tested':report['positive_count']==6})
    require(not (results/'REPLAY_METRICS.json').exists(), 'Replay metrics already exist')
    save(results/'REPLAY_METRICS.json',report)
    print(__import__('json').dumps({'positive_count':report['positive_count'],'aggregate':report['aggregate'],'original_frozen_metrics_changed':False}))

if __name__=='__main__':main()
