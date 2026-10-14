#!/usr/bin/env python3
"""Offline fabricated interface QA; no compiler, solver call, corpus or gold read."""
import collections
import copy
import datetime
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time

sys.dont_write_bytecode = True
from common import (PARENT, import_runner, require, stage_runtime, synthetic_registration,
                    verify_dependencies, verify_manifest)

def main():
    require(sys.version_info >= (3, 10), 'Python 3.10+ required')
    require(sys.byteorder == 'little' and hasattr(os, 'killpg'),
            'Unchanged runtime requires little endian and POSIX process groups')
    files = verify_manifest()
    dependencies = verify_dependencies()
    checks = 0
    def check(value, message):
        nonlocal checks
        require(value, message)
        checks += 1
    def refuses(fn, message):
        try:
            fn()
        except (RuntimeError, ValueError, TypeError, UnicodeError, KeyError):
            check(True, message)
            return
        raise RuntimeError('Expected refusal: ' + message)
    with tempfile.TemporaryDirectory(prefix='public-bounded-interface-') as tmp:
        root = Path(tmp)
        runtime = stage_runtime(root)
        runner = import_runner(runtime)
        code = [0, 1, 2, 26, 3, 4, 5, 6, 7, 26, 8, 9, 0, 2, 4, 26, 1, 3, 5]
        inp = root / 'fabricated.numeric.txt'
        inp.write_text(' '.join(map(str, code)) + '\n')
        check(runner.read_numeric(inp) == code, 'Canonical numeric parse')
        for text in ('0 1 2', '0 1 2 -1', '0 1 2 +1', '0 1 2 01', '0 1 2 1.0',
                     '0 1 2 1e0', '0 1 2 True', '0 1 2 27', '0 1 2 a', '0 1 2 NaN'):
            bad = root / 'malformed.txt'
            bad.write_text(text)
            refuses(lambda: runner.read_numeric(bad), 'Reject malformed numeric tokens')
        key = list(range(26))
        check(runner.strict_key(key) == key, 'Strict bijection accepts identity')
        for bad in (key[:-1], key + [26], [0]*26, [True] + key[1:], [0.0] + key[1:],
                    list(range(1, 27)), tuple(key), 'abcdefghijklmnopqrstuvwxyz'):
            refuses(lambda: runner.strict_key(bad), 'Reject malformed or coercible key')
        pinfile = root / 'pin.txt'
        pinfile.write_text('fabricated pin payload\n')
        runner.pin(pinfile, runner.sha(pinfile))
        check(True, 'Correct byte pin accepted')
        for bad in ('0'*64, 'A'*64, '', 'not-a-digest'):
            refuses(lambda: runner.pin(pinfile, bad), 'Wrong pin rejected')
        reg = synthetic_registration(PARENT / 'frozen/inference_inputs/P05.cipher.txt',
                                     root / 'unused-public-output')
        check(runner.validate_registration(reg).tzinfo is not None, 'Public synthetic registration accepted')
        for field, value in (('mode','OTHER'), ('authored_by','ROOT_CENTRAL'),
                             ('input_sha256','0'*64), ('core_sha256','0'*64),
                             ('fixed_config_sha256','0'*64), ('model_sha256','0'*64),
                             ('frequency_sha256','0'*64), ('runner_sha256','absent'),
                             ('solver_seed',2026101426), ('max_negatives',1),
                             ('resource_validation_authorized',False),
                             ('resource_validation_token','invalid'),
                             ('resource_lease_sha256','0'*64),
                             ('stop_utc','2026-01-01T00:00:00')):
            bad = copy.deepcopy(reg); bad[field] = value
            refuses(lambda: runner.validate_registration(bad), 'Registration constraint rejected')
        bad = copy.deepcopy(reg); bad['unregistered_payload'] = 'fabricated'
        refuses(lambda: runner.validate_registration(bad), 'Unknown registration field rejected')
        bad = copy.deepcopy(reg); del bad['budget']
        refuses(lambda: runner.validate_registration(bad), 'Missing budget rejected')
        for field in reg['budget']:
            bad = copy.deepcopy(reg); bad['budget'][field] += 1
            refuses(lambda: runner.validate_registration(bad), 'Changed fixed budget rejected')
        historical = copy.deepcopy(reg)
        historical.update(mode='HISTORICAL', authored_by='ROOT_CENTRAL',
                          solver_seed=2026101457, max_negatives=99)
        refuses(lambda: runner.validate_registration(historical), 'Historical registration without central admission refused')
        for seed in range(2026101501, 2026101600):
            shuffled = runner.shuffle_known(code, seed)
            check(collections.Counter(x for x in shuffled if x != 26) ==
                  collections.Counter(x for x in code if x != 26), 'Fabricated shuffle histogram preserved')
            check([i for i,x in enumerate(shuffled) if x == 26] ==
                  [i for i,x in enumerate(code) if x == 26], 'Fabricated shuffle gaps preserved')
            check(shuffled == runner.shuffle_known(code, seed), 'Shuffle deterministic at seed')
        scorer = runner.Scorer(runtime / 'quadgram_model.bin')
        check(scorer.sentinel_cells_checked == 74465, 'All sentinel cells checked')
        scores = scorer.score(code, key)
        check(scores['constant_sentinel_score'] == scorer.score(code, key[::-1])['constant_sentinel_score'],
              'Sentinel penalty independent of key')
        check(scores['all_quadgram_windows'] == len(code)-3 and
              scores['fully_observed_quadgram_windows'] + scores['sentinel_containing_quadgram_windows'] == len(code)-3,
              'Quadgram denominator decomposition')
        base = runner.baseline(code, key, scorer)
        check(base['known_character_count'] == len(code)-code.count(26) and
              all(base['plain'][i] == ' ' for i,c in enumerate(code) if c == 26), 'Baseline excludes sentinel')
        trials = [{'restart':r, 'key':key.copy(), 'plain':runner.render(code,key),
                   'score':scores['score']} for r in range(18)]
        result = {'seed':123, 'restarts':18, 'steps':100000, 'trials':trials,
                  'key':key.copy(), 'plain':runner.render(code,key), 'score':scores['score']}
        validated = runner.validate_result(result, code, 123, scorer)
        check(validated['winner_restart'] == 0 and validated['restarts_checked'] == 18,
              'Fabricated first-tie selection and complete trial validation')
        for field, value in (('seed',124), ('steps',99999), ('restarts',17),
                             ('trials',trials[:-1]), ('plain','x'*len(code))):
            bad = copy.deepcopy(result); bad[field] = value
            refuses(lambda: runner.validate_result(bad, code, 123, scorer), 'Malformed result rejected')
        bad = copy.deepcopy(result); bad['trials'][0]['score'] += .01
        refuses(lambda: runner.validate_result(bad, code, 123, scorer), 'Changed trial score rejected')
        # Exercise refusal before any process launch with fabricated numeric input.
        stop = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=20)
        probes = root / 'budget-probes'; probes.mkdir()
        for kind in ('expired','stop_event','aggregate','parallel'):
            budget = runner.Budget(probes, time.monotonic(), stop)
            if kind == 'expired': budget.deadline = time.monotonic()-1
            if kind == 'stop_event': budget.stop.set()
            if kind == 'aggregate': budget.total = 5990
            if kind == 'parallel': budget.active = {'fake-a':None, 'fake-b':None}
            refuses(lambda: budget.run('must_not_launch',root/'absent',inp,123,
                                        lambda:None,scorer), 'Budget refusal before launch: '+kind)
            check(budget.started == 0, 'No process launched for budget refusal')
        # The only child-process call is a dummy sleeper with a dummy sleeper child.
        # It performs no inference. Both receive the same POSIX group STOP signal.
        dummy = root / 'dummy_process.py'
        dummy.write_text('#!' + sys.executable + '\n' +
            'import pathlib,signal,subprocess,sys,time\n'
            'base=pathlib.Path(__file__).parent\n'
            'child_code="import pathlib,signal,sys,time; p=pathlib.Path(sys.argv[1]); '
            'signal.signal(signal.SIGTERM,lambda a,b:(p.write_text(\\\"stopped\\\"),sys.exit(0))); '
            'pathlib.Path(sys.argv[2]).write_text(\\\"ready\\\"); time.sleep(120)"\n'
            'child=subprocess.Popen([sys.executable,"-B","-c",child_code,str(base/"child-stopped"),str(base/"child-ready")])\n'
            'def stop(a,b):\n'
            ' child.wait(timeout=2); (base/"parent-stopped").write_text("stopped"); sys.exit(0)\n'
            'signal.signal(signal.SIGTERM,stop)\n'
            'time.sleep(120)\n')
        dummy.chmod(0o700)
        budget = runner.Budget(probes,time.monotonic(),stop)
        records, errors = [], []
        def run_dummy():
            try:
                records.append(budget.run('dummy_stop',dummy,inp,123,lambda:None,scorer))
            except Exception as exc:
                errors.append(str(exc))
        worker = threading.Thread(target=run_dummy)
        worker.start()
        deadline = time.monotonic()+4
        while not (root/'child-ready').exists() and time.monotonic()<deadline:
            time.sleep(.01)
        ready = (root/'child-ready').exists()
        budget.stop.set()
        worker.join(timeout=5)
        if worker.is_alive():
            budget.kill_groups(); worker.join(timeout=3)
        check(ready and not worker.is_alive() and not errors, 'Dummy process-group STOP completed')
        check((root/'child-stopped').exists() and (root/'parent-stopped').exists(),
              'STOP terminated dummy parent and child')
        check(len(records) == 1 and records[0]['termination_reason'] == 'STOP_OR_WHOLE_WALL'
              and budget.completed == 0 and not budget.active, 'STOP receipt reports incomplete dummy call')
    print(json.dumps({'record_type':'New offline fabricated interface QA; separate from original 234 probes',
        'checks_passed':checks,'checks_failed':0,'module_files_hashed':files,
        'public_inference_dependencies_hashed':dependencies,'fabricated_shuffle_seeds':99,
        'sentinel_cells_checked':74465,'dummy_process_group_STOP_controls':1,
        'actual_solver_calls':0,'historical_target_calls':0,'gold_read':False,
        'compiler_invoked':False,'network_used':False},sort_keys=True))

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'status':'FAIL','error':str(error)}),file=sys.stderr)
        sys.exit(2)
