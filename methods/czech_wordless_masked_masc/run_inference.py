#!/usr/bin/env python3
"""Compile unchanged C++ and replay fixed masked synthetic controls without gold."""
import argparse
import array
import datetime
from pathlib import Path
import subprocess
import sys
import time
sys.dont_write_bytecode = True
from common import MODULE, FROZEN, load, require, row_pin, safe_path, save, sha, verify_pins
from masked_profile import CPP_SHA256, baseline, read_cipher

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=FROZEN)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--controls', nargs='+', default=['P05'], help='Selected IDs, or all; default P05 only')
    parser.add_argument('--compiler', default='c++')
    args = parser.parse_args()
    bundle, output = args.bundle.resolve(), args.output.resolve()
    require(not output.exists(), 'Output must be a new directory; no original output is overwritten')
    require(not output.is_relative_to(MODULE.resolve()) and not output.is_relative_to(bundle),
            'Write replay artifacts outside the module and input bundle')
    pins = load(bundle/'INFERENCE_PINS.json')
    verify_pins(bundle, pins['artifacts'])
    config = load(bundle/'inference_inputs/RUN_CONFIG.json')
    require(config['restarts'] == 18 and config['steps_per_restart'] == 100000
            and config['unknown_sentinel'] == 26 and len(config['controls']) == 9, 'Fixed original profile changed')
    controls = config['controls']
    requested = [c['id'] for c in controls] if args.controls == ['all'] else args.controls
    require(requested and len(requested) == len(set(requested))
            and set(requested) <= {c['id'] for c in controls}, 'Unknown or duplicated control ID')
    chosen = [c for c in controls if c['id'] in requested]
    require(sha(MODULE/'generic_solver.cpp') == CPP_SHA256, 'Generic solver source changed')
    output.mkdir(parents=True)
    solver = output/('generic_solver.exe' if sys.platform == 'win32' else 'generic_solver')
    compile_start = now()
    proc = subprocess.run([args.compiler, '-O3', '-std=c++17', str(MODULE/'generic_solver.cpp'),
                           '-o', str(solver)], capture_output=True, text=True, timeout=60)
    save(output/'COMPILE_RECEIPT.json', {'record_type':'New public compilation',
        'started_utc':compile_start, 'completed_utc':now(), 'exit_code':proc.returncode,
        'compiler':args.compiler, 'source_sha256':CPP_SHA256,
        'binary_sha256':sha(solver) if solver.exists() else None, 'stderr':proc.stderr})
    require(proc.returncode == 0, 'Compilation failed; see new COMPILE_RECEIPT.json')
    model = safe_path(bundle, config['model_path'])
    # The original core reads native floats. Swap only a fresh runtime copy if needed.
    if pins['byte_order'] != sys.byteorder:
        floats = array.array('f')
        floats.frombytes(model.read_bytes())
        require(floats.itemsize == 4, 'Native float is not 32 bits')
        floats.byteswap()
        model = output/'runtime_native_model.bin'
        model.write_bytes(floats.tobytes())
    frequency_path = safe_path(bundle, config['frequency_path'])
    frequency = [int(v) for v in frequency_path.read_text().split()]
    receipts = []
    for control in chosen:
        cid = control['id']
        cipher_path = safe_path(bundle, control['cipher_path'])
        cipher = read_cipher(cipher_path)
        require(len(cipher) == control['tokens'] and cipher.count(26) == control['gap_marker_count'] == 30,
                'Wrong masked synthetic input: '+cid)
        save(output/(cid+'.frequency_baseline.json'), baseline(cipher, frequency))
        start, tick = now(), time.monotonic()
        proc = subprocess.run([str(solver), str(model), str(cipher_path), str(frequency_path),
            str(control['solver_seed']), '18', '100000', str(output/(cid+'.sa.json'))],
            capture_output=True, text=True, timeout=180)
        (output/(cid+'.stdout.txt')).write_text(proc.stdout, encoding='utf-8')
        (output/(cid+'.stderr.txt')).write_text(proc.stderr, encoding='utf-8')
        receipts.append({'id':cid, 'started_utc':start, 'completed_utc':now(),
            'seconds':time.monotonic()-tick, 'exit_code':proc.returncode,
            'seed':control['solver_seed'], 'restarts':18, 'steps':100000,
            'cipher_sha256':sha(cipher_path), 'model_original_sha256':sha(safe_path(bundle, config['model_path'])),
            'output_sha256':sha(output/(cid+'.sa.json')) if (output/(cid+'.sa.json')).exists() else None})
        save(output/'RUN_RECEIPTS.json', {'record_type':'New public replay',
            'controls':receipts, 'gold_loaded_by_runner':False,
            'input_interface':'Model, masked cipher, train frequency, seed, 18 restarts, 100000 iterations, output only; unknown original lengths are withheld'})
        require(proc.returncode == 0, 'Inference failed: '+cid)
    save(output/'INFERENCE_COMPLETION.json', {'record_type':'New public replay; distinct from original frozen run',
        'at_utc':now(), 'completed_ids':[c['id'] for c in chosen],
        'all_selected_completed':True, 'all_nine_completed':len(chosen) == 9, 'gold_loaded_by_runner':False})
    save(output/'RESULT_PINS.json', {'artifacts':[row_pin(output/(c['id']+suffix), output)
        for c in chosen for suffix in ['.sa.json','.frequency_baseline.json']]})
    print('PASS: new compilation and '+str(len(chosen))+' fixed-budget masked synthetic replay(s); no grading performed')

if __name__ == '__main__':
    main()
