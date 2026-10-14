"""Public, synthetic-only staging for the unchanged bounded runtime (MIT)."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
MODULE = Path(__file__).resolve().parent
REPO = MODULE.parent.parent
PARENT = MODULE.parent / 'czech_wordless_masked_masc'
RUNNER_HASH = 'e8358e69f4301918c5d4541979b1fd140c7691482ea809aa77ee9bcab4e80e91'
FIXED_HASH = '53aea196171de16e01a5dc7037f0fe8c6f8b26bbb32825e09bfba1861d389432'
P05_HASH = 'ecab97eb59c4d79427f7d40eece61faa8c86d15529c2fc50585c648d7e8b6e95'
RUNTIME_PINS = {
    'registered_runner.py': RUNNER_HASH,
    'FIXED_CONFIG.json': FIXED_HASH,
    'generic_solver.cpp': '651b888047c939dd0ce6e0d84805b8a4beba45eb6b0d8ebfe3ab43eb60681276',
    'quadgram_model.bin': '64f3e69c72e7e74f5c7fd3e41c90c42321ac46879d91f3b52d6f0182c4db8a64',
    'training_frequency_order.txt': '156c666c1f2c72247c67b6607a05a08b5c63e56908b4ba724e3183c3844122be',
}

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def relative_path(root, value):
    p = Path(value)
    require(not p.is_absolute() and '..' not in p.parts, 'Unsafe manifest path')
    result = (root / p).resolve()
    require(result.is_relative_to(root.resolve()), 'Manifest path escapes root')
    return result

def verify_manifest():
    manifest = load(MODULE / 'MODULE_SHA256.json')
    rows = manifest['artifacts']
    listed = [r['path'] for r in rows]
    actual = sorted(str(p.relative_to(MODULE)) for p in MODULE.rglob('*')
                    if p.is_file() and p.name != 'MODULE_SHA256.json')
    require(len(listed) == len(set(listed)) and sorted(listed) == actual,
            'Module file set differs from frozen manifest')
    for row in rows:
        p = relative_path(MODULE, row['path'])
        require(p.stat().st_size == row['bytes'] and sha(p) == row['sha256'],
                'Module bytes changed: ' + row['path'])
    return len(rows)

def verify_dependencies(grading=False):
    count = 0
    for row in load(MODULE / 'DEPENDENCY_PINS.json')['artifacts']:
        if row['phase'] == 'grading_only' and not grading:
            continue
        p = relative_path(PARENT, row['path'])
        require(p.stat().st_size == row['bytes'] and sha(p) == row['sha256'],
                'Public parent dependency changed: ' + row['path'])
        count += 1
    return count

def stage_runtime(root):
    runtime = root / 'runtime'
    runtime.mkdir()
    sources = {
        'registered_runner.py': MODULE / 'runtime/registered_runner.py',
        'FIXED_CONFIG.json': MODULE / 'runtime/FIXED_CONFIG.json',
        'generic_solver.cpp': PARENT / 'generic_solver.cpp',
        'quadgram_model.bin': PARENT / 'frozen/inference_inputs/quadgram_model.bin',
        'training_frequency_order.txt': PARENT / 'frozen/inference_inputs/training_frequency_order.txt',
    }
    for name, source in sources.items():
        require(sha(source) == RUNTIME_PINS[name], 'Frozen runtime resource changed: ' + name)
        shutil.copyfile(source, runtime / name)
        require(sha(runtime / name) == RUNTIME_PINS[name], 'Staging copy changed: ' + name)
    return runtime

def import_runner(runtime):
    spec = importlib.util.spec_from_file_location('public_frozen_bounded_runtime',
                                                 runtime / 'registered_runner.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner

def synthetic_registration(input_path, output_path, stop=None):
    if stop is None:
        stop = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=2400)
    return {
        'schema': 'DIRECT_MASKED_TRIAL_v1', 'authored_by': 'RESOURCE_WORKER_QA',
        'mode': 'SYNTHETIC_QA', 'input_path': str(input_path.resolve()),
        'input_sha256': P05_HASH, 'output_path': str(output_path.resolve()),
        'stop_utc': stop.isoformat(), 'fixed_config_sha256': FIXED_HASH,
        'core_sha256': RUNTIME_PINS['generic_solver.cpp'],
        'model_sha256': RUNTIME_PINS['quadgram_model.bin'],
        'frequency_sha256': RUNTIME_PINS['training_frequency_order.txt'],
        'runner_sha256': RUNNER_HASH,
        'budget': {'max_parallel_core_processes': 2, 'per_core_timeout_seconds': 60,
                   'max_aggregate_core_wall_seconds': 6000, 'whole_trial_seconds': 2400},
        'solver_seed': 2026101425, 'max_negatives': 0,
        'resource_validation_authorized': True,
        'resource_validation_token': 'P05_ONLY_RESOURCE_20261014',
        # Opaque compatibility digest retained by the frozen public QA branch.
        # It does not authenticate anyone or grant historical admission.
        'resource_lease_sha256': '7767215f0984f59235c0e847689df4c391c8adb69f7a6931c20c67f665709a7c',
    }

def verify_output_lock(private, expected_hash):
    lock_path = private / 'OUTPUT_LOCK.json'
    require(sha(lock_path) == expected_hash, 'Inference seal changed')
    rows = load(lock_path)['artifacts']
    names = [r['path'] for r in rows]
    actual = sorted(str(p.relative_to(private)) for p in private.rglob('*')
                    if p.is_file() and p.name != 'OUTPUT_LOCK.json')
    require(len(names) == len(set(names)) and sorted(names) == actual, 'Sealed file set changed')
    for row in rows:
        p = relative_path(private, row['path'])
        require(p.stat().st_size == row['bytes'] and sha(p) == row['sha256'],
                'Sealed inference artifact changed: ' + row['path'])
        require(p.stat().st_mode & 0o222 == 0, 'Sealed artifact remains writable')
    require(private.stat().st_mode & 0o222 == 0, 'Sealed directory remains writable')
    return len(rows)
