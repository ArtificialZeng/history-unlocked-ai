#!/usr/bin/env python3
import datetime,hashlib,json,re,shutil,subprocess,tempfile
from pathlib import Path
CASE=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
STAGE=CASE/'release/staging/hc1615-new-year-cipher-reading'
PYTHON='/Users/zeng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((STAGE/'RELEASE_MANIFEST_v1.json').read_text());entries=manifest['files']
listed={e['path'] for e in entries};actual={str(p.relative_to(STAGE)) for p in STAGE.rglob('*') if p.is_file()}-{'RELEASE_MANIFEST_v1.json','SHA256SUMS'}
assert actual==listed and len(entries)==manifest['file_count']==113
for e in entries:
 p=STAGE/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],e['path']
sums={}
for line in (STAGE/'SHA256SUMS').read_text().splitlines():
 h,f=line.split('  ',1);assert f not in sums;sums[f]=h;assert sha(STAGE/f)==h,f
assert set(sums)==actual|{'RELEASE_MANIFEST_v1.json'}
images=[p for p in actual if Path(p).suffix.lower() in {'.png','.jpg','.jpeg','.gif','.webp'}];assert not images
assert not any(x in p.split('/') for p in actual for x in ['.git','__pycache__','.DS_Store'])
assert sha(STAGE/'verify.py')=='f9b8ace394ea1393758810ba7ce6d765d24563610bbee90c71298a2769233479'
leaks=[];absolute_mentions=[]
pattern=re.compile(r'gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|(?i:password|api_key|access_token)\s*[:=]\s*[\"\'][^\"\']{8,}[\"\']')
for rel in sorted(actual):
 p=STAGE/rel
 if p.suffix.lower() in {'.json','.md','.py','.txt','.cff'}:
  text=p.read_text(errors='replace')
  if pattern.search(text):leaks.append(rel)
  if '/Users/' in text:absolute_mentions.append(rel)
assert not leaks
key=STAGE/'data/key/DONOR_FIXED_OBSERVED_KEY_v2.json';assert sha(key)=='267fac542b3cc9b3fbb5d788b8d867a0c37de0fa1f4ffefe16776256e1835273'
assert [p for p in actual if p.startswith('data/') and not p.startswith(('data/source_v1/','data/fixed_projection_v1/','data/mark_carry_projection_v1/','data/key/'))]==[]
for rel in ['README.md','README.zh-CN.md','README.cs.md','README.ja.md','LICENSE_CODE.txt','NOTICE.md','assets/fonts/LICENSE_DEJAVU.txt','assets/fonts/FONT_PROVENANCE_v1.json']:assert rel in actual
commands=[]
def run(name,args,cwd):
 proc=subprocess.run([PYTHON,'-B']+args,cwd=cwd,capture_output=True,text=True,timeout=60)
 for suffix,value in [('stdout',proc.stdout),('stderr',proc.stderr)]:
  with (OUT/f'{name}.{suffix}.txt').open('x') as f:f.write(value)
 commands.append({'command_id':name,'arguments':args,'cwd_role':'fresh_clean_release_root' if cwd.name=='clean_release' else 'temporary_external_cwd','exit_code':proc.returncode,'stdout_sha256':sha(OUT/f'{name}.stdout.txt'),'stderr_sha256':sha(OUT/f'{name}.stderr.txt')})
 assert proc.returncode==0,name+' failed: '+proc.stderr
 return proc.stdout
with tempfile.TemporaryDirectory(prefix='clean_assembly_',dir=OUT) as td:
 scratch=Path(td);clean=scratch/'clean_release';shutil.copytree(STAGE,clean)
 assert not any(p.suffix.lower() in {'.jpg','.jpeg','.png'} for p in clean.rglob('*') if p.is_file())
 raw=run('01_default_offline_verify',['verify.py','--root','.','--donor-key','data/key/DONOR_FIXED_OBSERVED_KEY_v2.json','--tamper'],clean)
 proof=json.loads(raw);assert proof['arithmetic_PASS'] and proof['greedy_text_encryption_PASS'] and proof['tamper_count']==48 and len(proof['synthetic_rule_mechanics'])==11 and proof['native_file_hashes_verified']==0
 run('02_baseline_reproduction',['scripts/reproduce_baseline.py','--root','.','--authorization','config/FIXED_PROJECTION_LOCK_v1.json','--donor-key','data/key/DONOR_FIXED_OBSERVED_KEY_v2.json','--output','regenerated_baseline'],clean)
 run('03_model_reproduction',['scripts/reproduce_mark_projection.py','--root','.','--authorization','config/MARK_CARRY_MODEL_v1.json','--donor-key','data/key/DONOR_FIXED_OBSERVED_KEY_v2.json','--output','regenerated_model'],clean)
 matches={}
 for regenerated,archived,names in [('regenerated_baseline','data/fixed_projection_v1',['CONDITIONAL_CANDIDATE_v1.json','LITERAL_ROWS_v1.txt']),('regenerated_model','data/mark_carry_projection_v1',['MARK_CARRY_CANDIDATE_v1.json','LITERAL_ROWS_v1.txt'])]:
  for name in names:
   assert (clean/regenerated/name).read_bytes()==(clean/archived/name).read_bytes(),name
   matches[regenerated+'/'+name]={'byte_equal':True,'sha256':sha(clean/regenerated/name)}
 # Outside the release CWD, every file argument is relative to the temporary CWD.
 external=scratch/'external_cwd';external.mkdir()
 run('04_external_cwd_verify',['../clean_release/verify.py','--root','../clean_release','--donor-key','../clean_release/data/key/DONOR_FIXED_OBSERVED_KEY_v2.json'],external)
 for name,script,auth,output,filename,archived in [('05_external_baseline','reproduce_baseline.py','FIXED_PROJECTION_LOCK_v1.json','outside_baseline','CONDITIONAL_CANDIDATE_v1.json','data/fixed_projection_v1'),('06_external_model','reproduce_mark_projection.py','MARK_CARRY_MODEL_v1.json','outside_model','MARK_CARRY_CANDIDATE_v1.json','data/mark_carry_projection_v1')]:
  run(name,['../clean_release/scripts/'+script,'--root','../clean_release','--authorization','../clean_release/config/'+auth,'--donor-key','../clean_release/data/key/DONOR_FIXED_OBSERVED_KEY_v2.json','--output',output],external)
  assert (external/output/filename).read_bytes()==(clean/archived/filename).read_bytes()
 # No GET: both already retained originals are explicitly supplied to the temp copy.
 replay=json.loads(run('07_native_rgb_replay',['scripts/fetch_and_replay_source.py','--root','.','--picture-from',str(CASE/'sources/raw/HC1615_picture_original.jpg'),'--address-from',str(CASE/'sources/raw/HC1615_address_original.jpg')],clean))
 assert len(replay['row_RGB_replays'])==7 and all(x['RGB_match'] for x in replay['row_RGB_replays'])
 pngall=all(x['PNG_encoding_byte_match'] for x in replay['row_RGB_replays'])
 if pngall:
  native=json.loads(run('08_optional_native_verify',['verify.py','--root','.','--donor-key','data/key/DONOR_FIXED_OBSERVED_KEY_v2.json','--verify-native'],clean));assert native['native_file_hashes_verified']==7
 from pypdf import PdfReader
 pdf=clean/'output/pdf/HC1615_New_Year_Cipher_Proposed_Reading_v1.pdf';pages=len(PdfReader(pdf).pages);assert pages==4
# Temporary images/outputs have been deleted. Staging was never mutated.
for e in entries:assert sha(STAGE/e['path'])==e['sha256'],e['path']
receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'clean staging assembly/portablecommand/runtime reproduction audit','PASS':True,'source_stage':str(STAGE),'release_manifest_sha256':sha(STAGE/'RELEASE_MANIFEST_v1.json'),'sha256sums_sha256':sha(STAGE/'SHA256SUMS'),'payload_files':113,'checksum_entries':len(sums),'payload_total_bytes':sum(e['bytes'] for e in entries),'initial_originals_crops_images':0,'symbolic_units':proof['units'],'covered_units':proof['covered_units'],'NFC_letter_characters':proof['expanded_NFC_letter_characters'],'trace_tokens':proof['greedy_token_count'],'tamper_cases':48,'synthetic_rule_checks':11,'default_native_reads':0,'candidate_and_literal_byte_matches':matches,'external_cwd_commands_PASS':True,'explicit_supplied_originals_only':True,'network_GETs':0,'native_replay':replay,'native_PNG_all_byte_equal':pngall,'pdf_pages':pages,'pdf_sha256':sha(STAGE/'output/pdf/HC1615_New_Year_Cipher_Proposed_Reading_v1.pdf'),'full_old_case_C_P_models_payload':False,'authorized_prior_key_artifact_only':True,'prior_key_metadata_short_previous_spellings_retained':json.loads(key.read_text()).get('literal_encoded_spelling_retained',[]),'credentials_patterns_found':leaks,'archival_absolute_path_mentions':absolute_mentions,'absolute_path_runtime_dependency':False,'staging_original_case_mutated':False,'temporary_copy_removed':True,'commands':commands,'audit_script_sha256':sha(Path(__file__)),'source_or_historical_uniqueness_not_a_package_claim':True}
with (OUT/'CLEAN_ASSEMBLY_QA_RESULT_v1.json').open('x') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ['commands','archival_absolute_path_mentions','candidate_and_literal_byte_matches','native_replay','prior_key_metadata_short_previous_spellings_retained']},ensure_ascii=False,indent=2))
