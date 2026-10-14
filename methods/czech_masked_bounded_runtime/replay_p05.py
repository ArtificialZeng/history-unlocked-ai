#!/usr/bin/env python3
"""Replay only public synthetic P05; seal inference artifacts before grading."""
import argparse
import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
from common import (MODULE, PARENT, REPO, P05_HASH, RUNNER_HASH, import_runner,
                    load, require, save, sha, stage_runtime, synthetic_registration,
                    verify_dependencies, verify_manifest, verify_output_lock)

def grade(private, runner, code):
    # This function is called only after completion and seal verification.
    verify_dependencies(grading=True)
    gold = next(r for r in load(PARENT / 'frozen/grading_gold/gold.json')['controls']
                if r['id'] == 'P05')
    result = load(private / 'positive.sa.json')
    key = runner.strict_key(result['key'])
    origins = gold['cipher_token_to_original_position']
    observed = [i for i, c in enumerate(code) if c != 26]
    require(len(origins) == len(code), 'Gold coordinate map length differs')
    require([i for i, p in enumerate(origins) if p is None] ==
            [i for i, c in enumerate(code) if c == 26], 'Gold gap coordinates differ')
    require([p for p in origins if p is not None] == gold['known_original_positions'],
            'Known-position denominator differs')
    require(len(observed) + gold['unknown_original_character_count'] == gold['original_length'],
            'Original-character denominator differs')
    require(result['plain'] == runner.render(code, key), 'Returned key/render differs')
    inverse = [key.index(p) for p in range(26)]
    expected = [gold['plain'][origins[i]] for i in observed]
    correct = sum(result['plain'][i] == e for i, e in zip(observed, expected))
    gold_forward = sum(inverse[ord(e)-97] == code[i] for i, e in zip(observed, expected))
    require(correct == gold_forward, 'Recovery forward arithmetic differs')
    require(all(code[i] == gold['enc_plain_to_cipher'][ord(e)-97]
                for i, e in zip(observed, expected)), 'Gold/input forward mismatch')
    types = sorted(set(code) - {26})
    base = load(private / 'frequency_baseline.json')
    errors = [{'cipher_token_index': i, 'original_plain_index': origins[i],
               'cipher_symbol': code[i], 'expected_letter': e,
               'returned_letter': result['plain'][i]}
              for i, e in zip(observed, expected) if result['plain'][i] != e]
    return {
        'record_type': 'New public synthetic P05 replay; separate from frozen original records',
        'graded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'known_characters_correct': correct, 'known_characters': len(observed),
        'observed_mappings_correct': sum(key[c] == gold['dec_cipher_to_plain'][c] for c in types),
        'observed_mappings': len(types), 'retained_known_position_errors': errors,
        'candidate_key_forward_correct': sum(inverse[ord(result['plain'][i])-97] == code[i]
                                             for i in observed),
        'gold_recovery_forward_correct': gold_forward,
        'baseline_known_characters_correct': sum(base['plain'][i] == e
                                               for i, e in zip(observed, expected)),
        'unknown_original_characters': gold['unknown_original_character_count'],
        'unknown_characters_recovered_or_graded': False,
        'all_nine_original_controls_retested': False, 'historical_target_calls': 0,
        'negative_solver_calls': 0, 'gold_read_after_verified_inference_seal': True,
        'result_sha256': sha(private / 'positive.sa.json'),
        'bytes_identical_to_retained_P05': sha(private / 'positive.sa.json') ==
                                         sha(PARENT / 'frozen/inference_outputs/P05.sa.json'),
        'restarts': result['restarts'], 'steps_per_restart': result['steps'],
        'retained_trials': len(result['trials']),
        'data_license': 'CC BY-NC-SA 4.0',
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(sys.version_info >= (3, 10), 'Python 3.10+ required')
    require(sys.byteorder == 'little' and hasattr(__import__('os'), 'killpg'),
            'Unchanged runtime requires little endian and POSIX process groups')
    require(shutil.which('c++'), 'An existing C++17 compiler named c++ is required')
    verify_manifest()
    verify_dependencies()
    output = args.output.resolve()
    require(not output.exists(), 'Output directory must be new')
    require(not output.is_relative_to(REPO), 'Keep generated output outside the checkout')
    output.mkdir(parents=True)
    runtime = stage_runtime(output)
    inputs = output / 'inputs'
    inputs.mkdir()
    inp = inputs / 'P05.cipher.txt'
    shutil.copyfile(PARENT / 'frozen/inference_inputs/P05.cipher.txt', inp)
    require(sha(inp) == P05_HASH, 'Public P05 input differs')
    registration = output / 'SYNTHETIC_REGISTRATION.json'
    save(registration, synthetic_registration(inp, output / 'inference'))
    registration_hash = sha(registration)
    argv = [sys.executable, '-B', str(runtime / 'registered_runner.py'),
            '--registration', str(registration),
            '--expected-registration-sha256', registration_hash]
    with (output / 'runner.stdout.txt').open('wb') as stdout, \
         (output / 'runner.stderr.txt').open('wb') as stderr:
        completed = subprocess.run(argv, stdout=stdout, stderr=stderr, timeout=2460)
    require(completed.returncode == 0, 'Runtime refused or incomplete; inspect external runner receipts')
    summary = load(output / 'inference/ROOT_SAFE_RUNTIME_SUMMARY.json')
    require(summary['status'] == 'COMPLETE' and summary['mode'] == 'SYNTHETIC_QA',
            'Synthetic replay incomplete')
    require(summary['core_calls_started'] == summary['core_calls_completed'] == 1 and
            summary['negative_calls_started'] == summary['negative_calls_completed'] == 0,
            'Unexpected solver calls')
    require(summary['registration_sha256'] == registration_hash and
            sha(registration) == registration_hash and summary['runner_sha256'] == RUNNER_HASH,
            'Registration/runner receipt differs')
    private = output / 'inference/private'
    sealed_files = verify_output_lock(private, summary['output_lock_sha256'])
    runner = import_runner(runtime)
    metrics = grade(private, runner, runner.read_numeric(inp))
    metrics.update(inference_completed_utc=summary['completed_utc'],
                   output_lock_sha256=summary['output_lock_sha256'],
                   sealed_inference_artifacts_checked=sealed_files,
                   registration_sha256=registration_hash,
                   aggregate_core_wall_seconds=summary['aggregate_core_wall_seconds'],
                   all_core_calls_within_60_seconds=summary['all_core_calls_within_60_seconds'])
    save(output / 'REPLAY_METRICS.json', metrics)
    save(output / 'REPLAY_LICENSE.json', {
        'code': 'MIT', 'model_frequency_fixture_and_outputs': 'CC BY-NC-SA 4.0',
        'attribution': 'UD_Czech-PDTC / Charles University, Prague; project modifications by Zijian Zeng',
        'licence_and_source_notices': 'methods/czech_masked_bounded_runtime/THIRD_PARTY_NOTICES.md'})
    print(json.dumps({k: metrics[k] for k in (
        'known_characters_correct', 'known_characters', 'observed_mappings_correct',
        'observed_mappings', 'baseline_known_characters_correct', 'candidate_key_forward_correct',
        'gold_recovery_forward_correct', 'bytes_identical_to_retained_P05',
        'gold_read_after_verified_inference_seal', 'historical_target_calls',
        'result_sha256', 'retained_trials')}, sort_keys=True))

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'FAILED_OR_REFUSED', 'error': str(error)}), file=sys.stderr)
        sys.exit(2)
