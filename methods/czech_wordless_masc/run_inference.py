#!/usr/bin/env python3
"""Compile unchanged C++ and run selected synthetic controls; never load gold."""
import argparse
import array
import collections
import datetime
from pathlib import Path
import subprocess
import sys
import time
from common import MODULE, FROZEN, load, require, row_pin, safe_path, save, sha, verify_pins

CPP_SHA256='651b888047c939dd0ce6e0d84805b8a4beba45eb6b0d8ebfe3ab43eb60681276'

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,default=FROZEN)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--controls',nargs='+',default=['P06'],help='Selected IDs, or all; default P06 only')
    parser.add_argument('--compiler',default='c++')
    args=parser.parse_args()
    bundle=args.bundle.resolve(); output=args.output.resolve()
    require(not output.exists(), 'Output must be a new directory; no frozen output is overwritten')
    require(not output.is_relative_to(FROZEN.resolve()), 'Output cannot be inside frozen/')
    pins=load(bundle/'INFERENCE_PINS.json')
    verify_pins(bundle,pins['artifacts'])
    manifest=load(bundle/'inference_inputs/CONTROL_MANIFEST.json')
    config=load(bundle/'FROZEN_RUN_CONFIG.json')
    require(config['restarts_per_main_control']==18 and config['steps_per_restart']==100000, 'This wrapper requires the fixed original budget')
    controls=manifest['controls']
    requested=[c['id'] for c in controls] if args.controls==['all'] else args.controls
    require(len(requested)==len(set(requested)) and set(requested)<=set(c['id'] for c in controls), 'Unknown or duplicated control ID')
    chosen=[c for c in controls if c['id'] in requested]
    require(sha(MODULE/'generic_solver.cpp')==CPP_SHA256, 'Generic solver source changed')
    output.mkdir(parents=True)
    solver=output/('generic_solver.exe' if sys.platform=='win32' else 'generic_solver')
    compile_start=now()
    proc=subprocess.run([args.compiler,'-O3','-std=c++17',str(MODULE/'generic_solver.cpp'),'-o',str(solver)],capture_output=True,text=True,timeout=60)
    save(output/'COMPILE_RECEIPT.json', {'started_utc':compile_start,'completed_utc':now(),'exit_code':proc.returncode,'compiler':args.compiler,'source_sha256':CPP_SHA256,'stderr':proc.stderr})
    require(proc.returncode==0, 'Compile failed; see new COMPILE_RECEIPT.json')
    model=safe_path(bundle,manifest['model_path'])
    # The unchanged C++ core reads native floats; swap only the runtime copy if needed.
    if pins['byte_order']!=sys.byteorder:
        floats=array.array('f');floats.frombytes(model.read_bytes());floats.byteswap()
        model=output/'runtime_native_model.bin';model.write_bytes(floats.tobytes())
    freq=[int(v) for v in safe_path(bundle,manifest['frequency_path']).read_text().split()]
    receipts=[]
    for control in chosen:
        cid=control['id'];cipher_path=safe_path(bundle,control['cipher_path'])
        cipher=[int(v) for v in cipher_path.read_text().split()]
        require(len(cipher)==control['length'] and all(0<=v<26 for v in cipher), 'Wrong synthetic input profile')
        order=sorted(range(26),key=lambda c:(-collections.Counter(cipher)[c],c));key=[0]*26
        for c,plain in zip(order,freq):key[c]=plain
        save(output/(cid+'.frequency_baseline.json'),{'plain':''.join(chr(key[c]+97) for c in cipher),'key':key,'uses_training_frequency_only':True})
        start=now();tick=time.monotonic()
        proc=subprocess.run([str(solver),str(model),str(cipher_path),str(safe_path(bundle,manifest['frequency_path'])),str(control['seed']),'18','100000',str(output/(cid+'.sa.json'))],capture_output=True,text=True,timeout=180)
        receipts.append({'id':cid,'started_utc':start,'completed_utc':now(),'seconds':time.monotonic()-tick,'exit_code':proc.returncode,'seed':control['seed'],'restarts':18,'steps':100000})
        save(output/'RUN_RECEIPTS.json',{'record_type':'new public replay','controls':receipts,'gold_loaded_by_runner':False})
        require(proc.returncode==0, 'Inference failed: '+cid)
    save(output/'INFERENCE_COMPLETION.json',{'record_type':'new public replay, distinct from original frozen run','at_utc':now(),'completed_ids':[c['id'] for c in chosen],'all_selected_completed':True,'all_nine_completed':len(chosen)==9,'gold_loaded_by_runner':False})
    save(output/'RESULT_PINS.json',{'artifacts':[row_pin(output/(c['id']+suffix),output) for c in chosen for suffix in ['.sa.json','.frequency_baseline.json']]})
    print('PASS: new compilation and '+str(len(chosen))+' fixed-budget synthetic replay(s); no grading performed')

if __name__=='__main__':main()
