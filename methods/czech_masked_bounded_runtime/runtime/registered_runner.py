#!/usr/bin/env python3
"""Frozen numeric-only direct runtime. Does not admit a historical experiment."""
import argparse, array, collections, concurrent.futures, datetime, hashlib, json, math, os, pathlib, random, re, shutil, signal, subprocess, sys, threading, time
sys.dont_write_bytecode=True
BASE=pathlib.Path(__file__).resolve().parent
PINS={'generic_solver.cpp':'651b888047c939dd0ce6e0d84805b8a4beba45eb6b0d8ebfe3ab43eb60681276','quadgram_model.bin':'64f3e69c72e7e74f5c7fd3e41c90c42321ac46879d91f3b52d6f0182c4db8a64','training_frequency_order.txt':'156c666c1f2c72247c67b6607a05a08b5c63e56908b4ba724e3183c3844122be','FIXED_CONFIG.json':'53aea196171de16e01a5dc7037f0fe8c6f8b26bbb32825e09bfba1861d389432'}
P05_HASH='ecab97eb59c4d79427f7d40eece61faa8c86d15529c2fc50585c648d7e8b6e95'
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p,x): pathlib.Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def require(v,s):
 if not v: raise RuntimeError(s)
def pin(p,h): require(re.fullmatch('[0-9a-f]{64}',h or '') is not None and sha(p)==h,'pin mismatch: '+pathlib.Path(p).name)
def read_numeric(p):
 text=pathlib.Path(p).read_text(encoding='ascii'); toks=text.split(); require(len(toks)>=4,'short numeric input')
 require(all(re.fullmatch(r'(?:0|[1-9][0-9]*)',x) for x in toks),'malformed numeric token')
 out=[int(x) for x in toks]; require(all(0<=x<=26 for x in out),'numeric value outside 0..26'); return out
def strict_key(k):
 require(isinstance(k,list) and len(k)==26 and all(type(x) is int for x in k) and sorted(k)==list(range(26)),'key is not strict 26-bijection'); return k
def render(code,k): return ''.join(' ' if x==26 else chr(97+k[x]) for x in code)
def shuffle_known(code,seed):
 ix=[i for i,x in enumerate(code) if x!=26]; vals=[code[i] for i in ix]; random.Random(seed).shuffle(vals); out=code.copy()
 for i,x in zip(ix,vals): out[i]=x
 require(collections.Counter(x for x in out if x!=26)==collections.Counter(x for x in code if x!=26),'shuffle histogram changed')
 require([i for i,x in enumerate(out) if x==26]==[i for i,x in enumerate(code) if x==26],'shuffle gaps changed'); return out
class Scorer:
 def __init__(self,p):
  require(sys.byteorder=='little','unchanged core/model runtime requires little endian native float32'); self.model=array.array('f'); self.model.frombytes(pathlib.Path(p).read_bytes()); require(self.model.itemsize==4 and len(self.model)==27**4,'model representation')
  self.floor=self.model[-1]; n=0
  for a in range(27):
   for b in range(27):
    for c in range(27):
     for d in range(27):
      if 26 in (a,b,c,d): require(self.model[((a*27+b)*27+c)*27+d]==self.floor,'nonconstant sentinel penalty'); n+=1
  self.sentinel_cells_checked=n
 def score(self,code,k):
  total=known=0.; obs=0
  for i in range(len(code)-3):
   w=code[i:i+4]; a=[26 if x==26 else k[x] for x in w]; v=self.model[((a[0]*27+a[1])*27+a[2])*27+a[3]]; total+=v
   if 26 not in w: known+=v; obs+=1
  alln=len(code)-3; return {'score':total,'all_quadgram_windows':alln,'fully_observed_quadgram_windows':obs,'sentinel_containing_quadgram_windows':alln-obs,'constant_sentinel_score':(alln-obs)*self.floor,'fully_observed_score':known,'all_window_average':total/alln,'fully_observed_average':known/obs if obs else None}
def baseline(code,frequency,scorer):
 strict_key(frequency); hist=collections.Counter(x for x in code if x!=26); order=sorted(range(26),key=lambda x:(-hist[x],x)); key=[0]*26
 for i,c in enumerate(order): key[c]=frequency[i]
 return {'key':key,'plain':render(code,key),'known_character_count':sum(x!=26 for x in code),'sentinel_excluded_from_frequency_order':True,**scorer.score(code,key)}
def validate_result(result,code,seed,scorer):
 require(result['seed']==seed and result['restarts']==18 and result['steps']==100000,'returned config differs'); ts=result['trials']; require(len(ts)==18,'not all 18 restarts retained'); known=sum(c!=26 for c in code); checks=0
 for r,t in enumerate(ts):
  require(t['restart']==r,'restart index'); k=strict_key(t['key']); require(t['plain']==render(code,k),'trial render differs'); s=scorer.score(code,k); require(math.isfinite(t['score']) and abs(s['score']-t['score'])<1e-6,'trial score differs'); inv=[k.index(x) for x in range(26)]; require(sum(inv[ord(t['plain'][i])-97]==c for i,c in enumerate(code) if c!=26)==known,'trial inverse differs'); checks+=1
 winner=max(range(18),key=lambda i:ts[i]['score']); require(result['key']==ts[winner]['key'] and result['plain']==ts[winner]['plain'] and result['score']==ts[winner]['score'],'original max/first tie selection differs'); strict_key(result['key']); require(result['plain']==render(code,result['key']),'overall render differs'); require(all(result['plain'][i]==' ' for i,c in enumerate(code) if c==26),'unknown gaps lost')
 return {**scorer.score(code,result['key']),'known_character_count':known,'candidate_key_output_inverse_correct':known,'candidate_key_output_inverse_total':known,'restarts_checked':checks,'winner_restart':winner,'gold_recovery_not_tested':True}
def validate_registration(reg,authorization=None):
 require(reg.get('schema')=='DIRECT_MASKED_TRIAL_v1','registration schema'); mode=reg.get('mode'); require(mode in ('HISTORICAL','SYNTHETIC_QA'),'mode'); require(reg.get('authored_by')==('ROOT_CENTRAL' if mode=='HISTORICAL' else 'RESOURCE_WORKER_QA'),'registration author role'); allowed={'schema','authored_by','mode','input_path','input_sha256','output_path','stop_utc','fixed_config_sha256','core_sha256','model_sha256','frequency_sha256','runner_sha256','budget','solver_seed','max_negatives','historical_admission_authorized','admission_authority','central_authorization_sha256','resource_validation_authorized','resource_validation_token','resource_lease_sha256'}; require(set(reg)<=allowed,'registration contains fields outside opaque interface'); required=('input_path','input_sha256','output_path','stop_utc','fixed_config_sha256','core_sha256','model_sha256','frequency_sha256','runner_sha256','budget','solver_seed','max_negatives')
 require(all(x in reg for x in required),'missing registration/pins/budget'); require(set(reg['budget'])=={'max_parallel_core_processes','per_core_timeout_seconds','max_aggregate_core_wall_seconds','whole_trial_seconds'},'missing/unknown budget field')
 require(reg['budget']=={'max_parallel_core_processes':2,'per_core_timeout_seconds':60,'max_aggregate_core_wall_seconds':6000,'whole_trial_seconds':2400},'fixed budget changed')
 require(reg['fixed_config_sha256']==PINS['FIXED_CONFIG.json'] and reg['core_sha256']==PINS['generic_solver.cpp'] and reg['model_sha256']==PINS['quadgram_model.bin'] and reg['frequency_sha256']==PINS['training_frequency_order.txt'],'registration immutable pin changed')
 require(re.fullmatch('[0-9a-f]{64}',reg['runner_sha256'] or '') is not None,'runner pin absent')
 if mode=='HISTORICAL':
  require(reg.get('historical_admission_authorized') is True and reg.get('admission_authority')=='ROOT_CENTRAL','historical admission absent'); require(authorization and reg.get('central_authorization_sha256')==authorization and re.fullmatch('[0-9a-f]{64}',authorization),'central authorization digest required'); require(reg['solver_seed']==2026101457 and reg['max_negatives']==99,'historical fixed seed/null plan')
 else: require(reg.get('resource_validation_token')=='P05_ONLY_RESOURCE_20261014' and reg.get('resource_lease_sha256')=='7767215f0984f59235c0e847689df4c391c8adb69f7a6931c20c67f665709a7c','sealed resource QA token/lease'); require(reg.get('resource_validation_authorized') is True and reg['input_sha256']==P05_HASH and reg['solver_seed']==2026101425 and reg['max_negatives']==0,'only sealed public P05 RESOURCE QA permitted')
 stop=datetime.datetime.fromisoformat(reg['stop_utc']); require(stop.tzinfo is not None,'STOP requires timezone'); return stop
class Budget:
 def __init__(self,root,start,stop): self.root=root; self.start=start; self.deadline=min(start+2400,time.monotonic()+max(0,(stop-datetime.datetime.now(datetime.timezone.utc)).total_seconds())); self.lock=threading.RLock(); self.stop=threading.Event(); self.active={}; self.total=0.; self.started=0; self.completed=0; self.records=[]
 def kill_groups(self):
  with self.lock: processes=list(self.active.values())
  for p in processes:
   if p.poll() is None:
    try: os.killpg(p.pid,signal.SIGTERM)
    except ProcessLookupError: pass
  for p in processes:
   try: p.wait(timeout=.15)
   except subprocess.TimeoutExpired:
    try: os.killpg(p.pid,signal.SIGKILL)
    except ProcessLookupError: pass
 def run(self,label,binary,inp,seed,verify,scorer):
  verify(); code=read_numeric(inp); out=self.root/(label+'.sa.json'); tick=time.monotonic(); begin=now(); argv=[str(binary),str(BASE/'quadgram_model.bin'),str(inp),str(BASE/'training_frequency_order.txt'),str(seed),'18','100000',str(out)]
  with self.lock:
   require(not self.stop.is_set() and tick<self.deadline,'STOP/whole wall reached before call'); require(len(self.active)<2,'parallel cap'); require(self.total+60*(len(self.active)+1)<=6000,'aggregate wall reservation exhausted before call'); self.started+=1
   so=open(self.root/(label+'.stdout.txt'),'wb'); se=open(self.root/(label+'.stderr.txt'),'wb'); p=subprocess.Popen(argv,stdout=so,stderr=se,start_new_session=True); self.active[label]=p
  limit=min(tick+59.8,self.deadline-.2); reason=None
  while p.poll() is None:
   if self.stop.is_set() or time.monotonic()>=limit:
    reason='STOP_OR_WHOLE_WALL' if self.stop.is_set() or limit<tick+59.8 else 'PER_CORE_TIMEOUT'; self.stop.set() if reason=='STOP_OR_WHOLE_WALL' else None
    try: os.killpg(p.pid,signal.SIGTERM)
    except ProcessLookupError: pass
    try: p.wait(timeout=.15)
    except subprocess.TimeoutExpired:
     try: os.killpg(p.pid,signal.SIGKILL)
     except ProcessLookupError: pass
     p.wait()
    if reason=='STOP_OR_WHOLE_WALL': self.kill_groups()
    break
   time.sleep(.02)
  elapsed=time.monotonic()-tick; so.close(); se.close(); rc=p.returncode
  with self.lock: del self.active[label]; self.total+=elapsed
  receipt={'label':label,'argv':argv,'pid':p.pid,'process_group_id':p.pid,'started_utc':begin,'completed_utc':now(),'core_wall_seconds':elapsed,'exit_code':rc,'termination_reason':reason,'per_core_wall_within_60':elapsed<=60,'input_sha256':sha(inp),'core_sha256':sha(BASE/'generic_solver.cpp'),'model_sha256':sha(BASE/'quadgram_model.bin'),'frequency_sha256':sha(BASE/'training_frequency_order.txt'),'fixed_config_sha256':sha(BASE/'FIXED_CONFIG.json'),'binary_sha256':sha(binary),'output_sha256':sha(out) if out.exists() else None,'seed':seed,'restarts':18,'steps':100000}
  if rc==0 and reason is None:
   receipt['checks']=validate_result(json.loads(out.read_text()),code,seed,scorer)
   with self.lock: self.completed+=1
  save(self.root/(label+'.receipt.json'),receipt)
  with self.lock: self.records.append(receipt)
  return receipt

def compile_core(private,start,deadline,budget):
 require(time.monotonic()<deadline,'STOP before compilation'); compiler=shutil.which('c++'); require(compiler,'existing C++ compiler absent'); binary=private/'generic_solver'; records=[]
 for label,argv in [('version',[compiler,'--version']),('compile',[compiler,'-O3','-std=c++17',str(BASE/'generic_solver.cpp'),'-o',str(binary)])]:
  tick=time.monotonic(); begin=now(); p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True);
  with budget.lock: budget.active['compiler_'+label]=p
  timeout=min(60,max(.01,deadline-tick)); reason=None
  try: stdout,stderr=p.communicate(timeout=timeout)
  except subprocess.TimeoutExpired:
   reason='COMPILER_TIMEOUT_OR_STOP'; os.killpg(p.pid,signal.SIGTERM)
   try: stdout,stderr=p.communicate(timeout=.15)
   except subprocess.TimeoutExpired: os.killpg(p.pid,signal.SIGKILL); stdout,stderr=p.communicate()
  with budget.lock: del budget.active['compiler_'+label]
  (private/(label+'.stdout.txt')).write_bytes(stdout); (private/(label+'.stderr.txt')).write_bytes(stderr); records.append({'label':label,'argv':argv,'pid':p.pid,'started_utc':begin,'completed_utc':now(),'wall_seconds':time.monotonic()-tick,'exit_code':p.returncode,'termination_reason':reason,'source_sha256':sha(BASE/'generic_solver.cpp')}); save(private/'COMPILE_RECEIPT.json',{'calls':records,'binary_sha256':sha(binary) if binary.exists() else None}); require(p.returncode==0 and reason is None,'compiler/version command failed')
 return binary

def lock_private(private):
 rows=[]
 for p in sorted(private.rglob('*')):
  if p.is_file(): rows.append({'path':str(p.relative_to(private)),'bytes':p.stat().st_size,'sha256':sha(p)})
 lock={'at_utc':now(),'artifacts':rows,'scope':'All private inference artifacts locked before any future source mapping or QA gold read','os_scope':'owner-only file permissions and immutable receipt hashes; not an OS-enforced agent blindness barrier'}; save(private/'OUTPUT_LOCK.json',lock)
 for p in private.rglob('*'):
  if p.is_file(): p.chmod(0o400)
 private.chmod(0o500); return sha(private/'OUTPUT_LOCK.json')
def main():
 start=time.monotonic(); parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--registration',required=True,type=pathlib.Path); parser.add_argument('--expected-registration-sha256',required=True); parser.add_argument('--authorization-sha256'); args=parser.parse_args(); pin(args.registration,args.expected_registration_sha256); reg=json.loads(args.registration.read_text()); stop=validate_registration(reg,args.authorization_sha256)
 for n,h in PINS.items(): pin(BASE/n,h)
 pin(__file__,reg['runner_sha256']); inp=pathlib.Path(reg['input_path']).resolve(); pin(inp,reg['input_sha256']); code=read_numeric(inp); out=pathlib.Path(reg['output_path']).resolve(); require(not out.exists(),'new output directory required'); require(not out.is_relative_to(BASE) and not inp.is_relative_to(out),'output/input separation'); out.mkdir(parents=True); private=out/'private'; private.mkdir(mode=0o700); fixed=private/'positive.cipher.txt'; shutil.copyfile(inp,fixed); fixed.chmod(0o400); budget=Budget(private,start,stop); binary=None; fatal=None; safe={}
 def stop_handler(signum,frame): budget.stop.set(); budget.kill_groups()
 signal.signal(signal.SIGTERM,stop_handler); signal.signal(signal.SIGINT,stop_handler)
 try:
  binary=compile_core(private,start,budget.deadline,budget); bh=sha(binary); scorer=Scorer(BASE/'quadgram_model.bin'); freq=read_numeric(BASE/'training_frequency_order.txt'); strict_key(freq); base=baseline(code,freq,scorer); save(private/'frequency_baseline.json',base)
  def verify():
   pin(args.registration,args.expected_registration_sha256); pin(__file__,reg['runner_sha256']); pin(fixed,reg['input_sha256']); pin(binary,bh)
   for n,h in PINS.items(): pin(BASE/n,h)
  pos=budget.run('positive',binary,fixed,reg['solver_seed'],verify,scorer); checks=pos.get('checks'); safe={'positive_complete':bool(checks),'positive_calls':1,'negative_calls_started':0,'negative_calls_completed':0,'matched_null_p':None,'matched_null_rank_available':False,'score_role':'heuristic, not probability','null_role':'conditional shuffle comparison, not historical truth probability','known_character_count':sum(x!=26 for x in code),'all_quadgram_windows':len(code)-3,'model_sentinel_cells_checked':scorer.sentinel_cells_checked}
  if checks: safe.update(checks)
  require(checks is not None,'positive call incomplete; timeout is not unsolvability')
  gate=checks['fully_observed_average'] is not None and checks['fully_observed_average']>=-4.70; safe['prescreen_gate_passed']=gate; safe['prescreen_threshold']=-4.70; safe['prescreen_role']='prospective heuristic from frozen modern controls; not calibrated probability'; safe['negative_status']='RESOURCE_QA_ZERO_NEGATIVES' if reg['mode']=='SYNTHETIC_QA' else ('GATE_ABSTENTION_ZERO_NEGATIVES' if not gate else 'PENDING')
  if reg['mode']=='HISTORICAL' and gate:
   inputs=[]
   for seed in range(2026101501,2026101600):
    v=shuffle_known(code,seed); p=private/('shuffle_'+str(seed)+'.cipher.txt'); p.write_text(' '.join(map(str,v))+'\n'); p.chmod(0o400); inputs.append((seed,p,sha(p)))
   save(private/'SHUFFLE_INPUT_PINS.json',{'shuffle_algorithm':'Python random.Random(seed).shuffle on known positions only','python_version':sys.version,'inputs':[{'seed':s,'path':p.name,'sha256':h,'histogram_preserved':True,'gap_indices_preserved':True} for s,p,h in inputs]})
   negatives=[]
   def run_negative(item):
    seed,p,h=item; pin(p,h); return budget.run('shuffle_'+str(seed),binary,p,2026101457,verify,scorer)
   with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    it=iter(inputs); pending={}
    for _ in range(2):
     item=next(it,None)
     if item: pending[pool.submit(run_negative,item)]=item
    while pending:
     ready,_=concurrent.futures.wait(pending,return_when=concurrent.futures.FIRST_COMPLETED)
     for f in ready:
      del pending[f]
      try: negatives.append(f.result())
      except Exception as e: save(private/'NEGATIVE_STOP.json',{'at_utc':now(),'reason':str(e)}); budget.stop.set(); budget.kill_groups()
      if not budget.stop.is_set():
       item=next(it,None)
       if item: pending[pool.submit(run_negative,item)]=item
   complete=[x for x in negatives if x.get('checks')]; safe['negative_calls_started']=budget.started-1; safe['negative_calls_completed']=len(complete); safe['negative_status']='COMPLETE_99' if len(complete)==99 else 'PARTIAL_NO_99_WIDE_P'
   if len(complete)==99:
    ge=sum(x['checks']['score']>=checks['score'] for x in complete); safe.update(matched_null_rank_available=True,matched_null_ge_positive=ge,matched_null_p=(1+ge)/100,matched_null_resolution=.01,matched_null_denominator=100)
   save(private/'NEGATIVE_SUMMARY.json',{'calls':negatives,'completed_count':len(complete),'qualified_conditional_null_rank':safe})
 except Exception as e: fatal=str(e); budget.stop.set(); budget.kill_groups()
 finally:
  save(private/'CALL_SUMMARY.json',{'calls':budget.records,'started':budget.started,'completed':budget.completed,'aggregate_core_wall_seconds':budget.total,'historical_target_calls':budget.started if reg['mode']=='HISTORICAL' else 0,'resource_qa_calls':budget.started if reg['mode']=='SYNTHETIC_QA' else 0,'fatal':fatal,'whole_trial_elapsed_seconds':time.monotonic()-start}); lockhash=lock_private(private); safe.update(schema='ROOT_SAFE_RUNTIME_SUMMARY_v1',status='COMPLETE' if fatal is None else 'INCOMPLETE_OR_REFUSED_AFTER_START',fatal=fatal,mode=reg['mode'],output_lock_sha256=lockhash,registration_sha256=args.expected_registration_sha256,input_sha256=reg['input_sha256'],core_sha256=PINS['generic_solver.cpp'],model_sha256=PINS['quadgram_model.bin'],frequency_sha256=PINS['training_frequency_order.txt'],fixed_config_sha256=PINS['FIXED_CONFIG.json'],runner_sha256=sha(__file__),binary_sha256=sha(binary) if binary and binary.exists() else None,core_calls_started=budget.started,core_calls_completed=budget.completed,aggregate_core_wall_seconds=budget.total,whole_trial_elapsed_seconds=time.monotonic()-start,whole_trial_within_2400_seconds=time.monotonic()-start<=2400,aggregate_within_6000_seconds=budget.total<=6000,all_core_calls_within_60_seconds=all(x['core_wall_seconds']<=60 for x in budget.records),historical_admission_by_this_worker=False,historical_truth_claim=False,completed_utc=now()); save(out/'ROOT_SAFE_RUNTIME_SUMMARY.json',safe); print(json.dumps(safe,sort_keys=True));
 if fatal: return 2
 return 0
if __name__=='__main__':
 try: sys.exit(main())
 except Exception as e: print(json.dumps({'status':'REFUSED_BEFORE_CORE','error':str(e),'historical_calls':0})); sys.exit(2)
