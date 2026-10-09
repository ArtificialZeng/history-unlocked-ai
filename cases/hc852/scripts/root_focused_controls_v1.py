#!/usr/bin/env python3
from pathlib import Path
import random,itertools,json,hashlib,datetime,sys
sys.dont_write_bytecode=True
from grille_even_v1 import encrypt,decrypt,rotate
R=Path(__file__).resolve().parents[1];O=R/'reports/root_method_v1';O.mkdir(exist_ok=True)
reg=json.loads((R/'config/ROOT_FOCUSED_GENERIC_CONTROLS_v1.json').read_text())
assert hashlib.sha256((R/'scripts/grille_even_v1.py').read_bytes()).hexdigest()==reg['code_sha256']
k=[(0,0),(1,3),(2,1),(2,3)];P='THETURNINGGRILLE';C='TILUNRGHGELTENIR';assert encrypt(P,side=4,holes=k)==C and decrypt(C,side=4,holes=k)==P
rng=random.Random(reg['seed']);orbits=[];left={(r,c)for r in range(8)for c in range(8)}
while left:
 a=min(left);orbit=sorted({rotate(a,8,z)for z in range(4)});assert len(orbit)==4;orbits.append(orbit);left.difference_update(orbit)
keys=set()
while len(keys)<5:keys.add(tuple(sorted(rng.choice(o)for o in orbits)))
fixtures=[]
for keyidx,key in enumerate(sorted(keys)):
 for start,direction,scan,order in itertools.product(range(4),[-1,1],['row-major','column-major'],['row-major','column-major']):
  for blocks in [1,2]:
   p=''.join(rng.choice('abcdefghijklmnopqrstuvwxyz0123456789XYZ')for _ in range(64*blocks));kw=dict(side=8,holes=key,start=start,direction=direction,hole_scan=scan,cipher_order=order);c=encrypt(p,**kw);assert decrypt(c,**kw)==p
   fixtures.append({'generic_key_index':keyidx,'holes':[list(x)for x in key],'start':start,'direction':direction,'hole_scan':scan,'cipher_order':order,'blocks':blocks,'plaintext':p,'ciphertext':c})
assert len(fixtures)==320
bad=[dict(side=3,holes=[]),dict(side=0,holes=[]),dict(side=4,holes=[(0,0)]),dict(side=4,holes=[(0,0)]*4),dict(side=4,holes=[(0,0),(1,3),(2,1),(4,3)]),dict(side=4,holes=k,start=4),dict(side=4,holes=k,hole_scan='spiral'),dict(side=4,holes=k,cipher_order='spiral')]
for kw in bad:
 try:encrypt(P,**kw)
 except ValueError:pass
 else:raise AssertionError(kw)
(O/'FOCUSED_SYNTHETIC_FIXTURES_v1.json').write_text(json.dumps(fixtures,indent=2)+'\n')
(O/'CONTROL_RESULTS_v1.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_REUSED_GENERIC_CORE_FOCUSED_CONTROLS','synthetic_trials':320,'distinct_keys':5,'settings':32,'block_counts':[1,2],'ACA_known_vectors':1,'invalid_case_rejections':8,'target_file_reads':0,'root_fully_blind':False,'fresh_code_implementation':False},indent=2)+'\n')
items=[R/'scripts/grille_even_v1.py',Path(__file__),R/'config/ROOT_FOCUSED_GENERIC_CONTROLS_v1.json',*sorted(O.iterdir())]
(O/'PRETARGET_METHOD_SEAL_v1.json').write_text(json.dumps({'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'artifacts':[{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in items],'no_target_inputs':True},indent=2)+'\n')
print('Root reused core: focused320 synthetic +ACA1 +8rejections PASS; targetinputs0')
