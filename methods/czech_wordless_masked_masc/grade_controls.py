#!/usr/bin/env python3
"""Grade known original positions only, after recorded selected replay completion."""
import argparse
import collections
import datetime
import hashlib
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from common import MODULE, FROZEN, load, require, safe_path, save, verify_pins
from masked_profile import baseline, read_cipher, render

def grade(bundle, results, ids):
    gold = {r['id']:r for r in load(bundle/'grading_gold/gold.json')['controls']}
    config = load(bundle/'inference_inputs/RUN_CONFIG.json')
    controls = {r['id']:r for r in config['controls']}
    frequency = [int(v) for v in safe_path(bundle, config['frequency_path']).read_text().split()]
    rows, negatives, failures = [], [], []
    totals = collections.Counter()
    for cid in ids:
        control = controls[cid]
        code = read_cipher(safe_path(bundle, control['cipher_path']))
        result = load(results/(cid+'.sa.json'))
        key, plain = result['key'], result['plain']
        require(len(plain) == len(code) and render(code, key) == plain, 'Invalid candidate decode: '+cid)
        require(result['seed'] == control['solver_seed'] and result['restarts'] == 18
                and result['steps'] == 100000 and len(result['trials']) == 18, 'Wrong replay budget: '+cid)
        observed = [i for i, c in enumerate(code) if c != 26]
        inverse = [key.index(p) for p in range(26)]
        candidate_forward = sum(inverse[ord(plain[i])-97] == code[i] for i in observed)
        if cid not in gold:
            matched = read_cipher(safe_path(bundle, controls[control['matched_positive']]['cipher_path']))
            histogram_ok = collections.Counter(c for c in code if c != 26) == collections.Counter(c for c in matched if c != 26)
            gaps_ok = [i for i,c in enumerate(code) if c == 26] == [i for i,c in enumerate(matched) if c == 26]
            require(histogram_ok and gaps_ok, 'Negative control profile changed: '+cid)
            negatives.append({'id':cid, 'matched_positive':control['matched_positive'],
                'observed_symbols':len(observed), 'gap_markers':code.count(26),
                'histogram_preserved':histogram_ok, 'gap_locations_preserved':gaps_ok,
                'score':result['score'], 'score_per_quadgram':result['score']/(len(code)-3),
                'returned_plaintext_key_forward_known_tokens_correct':candidate_forward,
                'inference_budget_restarts':18, 'inference_budget_steps':100000,
                'no_significance_or_historical_probability':True})
            continue
        truth = gold[cid]
        origins = truth['cipher_token_to_original_position']
        require(len(origins) == len(code), 'Original-position map length differs: '+cid)
        require([i for i,p in enumerate(origins) if p is None] == [i for i,c in enumerate(code) if c == 26], 'Gap map differs: '+cid)
        require([p for p in origins if p is not None] == truth['known_original_positions'], 'Known denominator map differs: '+cid)
        expected = ''.join(truth['plain'][origins[i]] for i in observed)
        predicted = ''.join(plain[i] for i in observed)
        correct = sum(a == b for a,b in zip(predicted, expected))
        exact = predicted == expected
        observed_types = sorted(set(code)-{26})
        key_correct = sum(key[c] == truth['dec_cipher_to_plain'][c] for c in observed_types)
        gold_forward = sum(inverse[ord(truth['plain'][origins[i]])-97] == code[i] for i in observed)
        require(correct == gold_forward, 'Recovery-based forward arithmetic differs: '+cid)
        require(all(code[i] == truth['enc_plain_to_cipher'][ord(truth['plain'][origins[i]])-97] for i in observed), 'Gold/input forward mismatch: '+cid)
        base = baseline(code, frequency)
        base_predicted = ''.join(base['plain'][i] for i in observed)
        base_correct = sum(a == b for a,b in zip(base_predicted, expected))
        base_exact = base_predicted == expected
        unknown_count = truth['unknown_original_character_count']
        require(len(observed) + unknown_count == truth['original_length'], 'Known/original denominator differs: '+cid)
        rows.append({'id':cid, 'original_length':truth['original_length'],
            'known_characters':len(observed), 'known_characters_correct':correct,
            'known_character_accuracy':correct/len(observed), 'exact_known_position_stream':exact,
            'observed_key_types':len(observed_types), 'observed_key_types_correct':key_correct,
            'returned_plaintext_key_forward_known_tokens_correct':candidate_forward,
            'returned_plaintext_key_forward_known_tokens_total':len(observed),
            'known_gold_with_returned_key_forward_correct':gold_forward,
            'baseline_known_characters_correct':base_correct, 'baseline_exact_known_stream':base_exact,
            'unknown_original_characters':unknown_count, 'gap_markers':code.count(26),
            'score':result['score'], 'score_per_quadgram':result['score']/(len(code)-3),
            'document_id_sha256':hashlib.sha256(truth['document_id'].encode()).hexdigest()})
        totals.update({'original_characters':truth['original_length'], 'known_characters':len(observed),
            'known_characters_correct':correct, 'exact_known_position_streams':int(exact),
            'observed_key_types':len(observed_types), 'observed_key_types_correct':key_correct,
            'candidate_forward_known_tokens_correct':candidate_forward,
            'candidate_forward_known_tokens_total':len(observed),
            'gold_forward_with_returned_key_correct':gold_forward,
            'baseline_known_characters_correct':base_correct, 'baseline_exact_known_streams':int(base_exact),
            'unknown_original_characters':unknown_count})
        for i in observed:
            if plain[i] != truth['plain'][origins[i]]:
                failures.append({'id':cid, 'cipher_token_index':i, 'original_plain_index':origins[i],
                    'cipher_symbol':code[i], 'expected_letter':truth['plain'][origins[i]], 'returned_letter':plain[i]})
    names = ['original_characters','known_characters','known_characters_correct','exact_known_position_streams',
        'observed_key_types','observed_key_types_correct','candidate_forward_known_tokens_correct',
        'candidate_forward_known_tokens_total','gold_forward_with_returned_key_correct',
        'baseline_known_characters_correct','baseline_exact_known_streams','unknown_original_characters']
    aggregate = {name:totals[name] for name in names}
    denominator = aggregate['known_characters']
    aggregate['known_character_accuracy'] = aggregate['known_characters_correct']/denominator if denominator else None
    aggregate['baseline_known_character_accuracy'] = aggregate['baseline_known_characters_correct']/denominator if denominator else None
    return {'selected_control_ids':ids, 'positive_count':len(rows), 'negative_count':len(negatives),
        'aggregate':aggregate, 'positives':rows, 'negatives':negatives,
        'wrong_observed_positions':failures, 'unknown_original_positions_recovered_or_graded':False,
        'forward_metric_definition':'Candidate/key forward consistency tests output compatibility; gold under the returned key measures recovery on known original positions.',
        'scores_are_probabilities':False, 'historical_targets_solved':0}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=FROZEN)
    parser.add_argument('--results', type=Path, required=True)
    args = parser.parse_args()
    bundle, results = args.bundle.resolve(), args.results.resolve()
    require(not results.is_relative_to(MODULE.resolve()), 'Write replay grades outside the module checkout')
    require(not (results/'REPLAY_METRICS.json').exists(), 'Replay metrics already exist')
    completion = load(results/'INFERENCE_COMPLETION.json')
    require(completion['all_selected_completed'] and completion['gold_loaded_by_runner'] is False,
            'Grading requires completed selected replay inference')
    verify_pins(bundle, load(bundle/'INFERENCE_PINS.json')['artifacts'])
    verify_pins(results, load(results/'RESULT_PINS.json')['artifacts'])
    report = grade(bundle, results, completion['completed_ids'])
    full_profile = report['positive_count'] == 6 and report['negative_count'] == 3
    report.update({'record_type':'New public replay grading; original frozen metrics remain separate',
        'graded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'inference_completed_utc':completion['at_utc'], 'full_original_profile_tested':full_profile,
        'profile_pass':(report['aggregate']['exact_known_position_streams'] >= 5
            and report['aggregate']['known_character_accuracy'] >= .99
            and report['aggregate']['candidate_forward_known_tokens_correct'] == report['aggregate']['candidate_forward_known_tokens_total']) if full_profile else None})
    save(results/'REPLAY_METRICS.json', report)
    print(__import__('json').dumps({'positive_count':report['positive_count'], 'aggregate':report['aggregate'],
        'retained_known_position_errors':len(report['wrong_observed_positions']), 'full_original_profile_tested':full_profile,
        'original_frozen_metrics_changed':False}))

if __name__ == '__main__':
    main()
