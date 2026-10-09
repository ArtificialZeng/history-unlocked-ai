"""Read root codec only after verifying the frozen independent precomparison seal."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/independent_method_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    sealpath=OUT/'INDEPENDENT_CODEC_PRECOMPARISON_SEAL_v1.json'
    seal=json.loads(sealpath.read_text())
    assert seal['root_codec_read_or_imported'] is False
    for r in seal['files']:assert sha(ROOT/r['path'])==r['sha256']
    began=datetime.datetime.now(datetime.timezone.utc).isoformat()
    rootpath=ROOT/'scripts/grille_v1.py'
    spec=importlib.util.spec_from_file_location('postseal_root_grille_v1',rootpath)
    rootmod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=rootmod;spec.loader.exec_module(rootmod)
    fixtures=json.loads((OUT/'INDEPENDENT_SYNTHETIC_FIXTURES_v1.json').read_text())
    checks=[];rejected=[]
    def reject(label,callback):
        try:callback()
        except ValueError as exc:rejected.append({'label':label,'reason':str(exc)})
        else:raise AssertionError('root accepted invalid core case: '+label)
    for f in fixtures:
        n=f['side'];holes=tuple(divmod(h-1,n) for h in f['holes_1indexed']);g=rootmod.Grille(n,holes);plain=f['plaintext']
        for c in f['controls']:
            start=c['start_turn'];direction=c['direction'];route=g.permutation(start,direction)
            assert [p+1 for p in route]==c['permutation_1indexed']
            cipher=g.encrypt(plain,start,direction)
            assert hashlib.sha256(cipher.encode()).hexdigest()==c['ciphertext_sha256']
            assert g.decrypt(cipher,start,direction)==plain
            checks.append({'side':n,'holes_1indexed':f['holes_1indexed'],'start_turn':start,'direction':direction,'permutation_matches_sealed_vector':True,'cipher_hash_matches_sealed_vector':True,'decode_matches_sealed_plaintext':True})
        reject(f'{n}_{holes}_duplicate',lambda n=n,holes=holes:rootmod.Grille(n,(*holes,holes[0])))
        reject(f'{n}_{holes}_lower_bound',lambda n=n,holes=holes:rootmod.Grille(n,((-1,0),*holes[1:])))
        reject(f'{n}_{holes}_upper_bound',lambda n=n,holes=holes:rootmod.Grille(n,((n,0),*holes[1:])))
        reject(f'{n}_{holes}_missing_hole',lambda n=n,holes=holes:rootmod.Grille(n,holes[:-1]))
        reject(f'{n}_{holes}_partial_encrypt',lambda g=g,plain=plain:g.encrypt(plain[:-1]))
        cipher0=g.encrypt(plain)
        reject(f'{n}_{holes}_partial_decrypt',lambda g=g,cipher0=cipher0:g.decrypt(cipher0[:-1]))
        if n>2:
            r,c=holes[0];collided=(holes[0],(c,n-1-r),*holes[2:])
            assert len(set(collided))==len(holes)
            reject(f'{n}_{holes}_same_orbit',lambda n=n,collided=collided:rootmod.Grille(n,collided))
    primary=rootmod.Grille(4,((0,0),(1,3),(2,1),(2,3)))
    assert primary.encrypt('THETURNINGGRILLE')=='TILUNRGHGELTENIR'
    assert primary.decrypt('TILUNRGHGELTENIR')=='THETURNINGGRILLE'
    assert len(checks)==800 and len(rejected)==696
    for r in seal['files']:assert sha(ROOT/r['path'])==r['sha256']
    baseline=json.loads((ROOT/'reports/GRILLE_SYNTHETIC_CONTROLS_v1.json').read_text())
    result={'status':'PASS','started_at_utc':began,'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'chronology':'Root implementation was read/imported only after the independent-code/result/fixture precomparison seal. Comparisons use its sealed fixture permutations and ciphertext hashes.','precomparison_seal_sha256':sha(sealpath),'precomparison_files_unchanged_before_and_after':True,'root_codec_path':str(rootpath.relative_to(ROOT)),'root_codec_sha256':sha(rootpath),'root_codec_matches_provided_baseline_hash':sha(rootpath)==baseline['source_code_sha256'],'independent_code_sha256':sha(ROOT/'scripts/independent_grille_v1.py'),'primary_worked_vector_crosscheck':True,'distinct_grilles':100,'orientation_direction_crosschecks':len(checks),'root_core_rejection_controls':len(rejected),'crosschecks':checks,'root_rejected_cases':rejected,'target_inputs':0,'parameter_contract_note':'Canonical starts 0,1,2,3 and directions ±1 were compared. Root uses modulo-four starts; the independent public interface rejects noncanonical starts explicitly. Strict invalid-type controls belong to the independent implementation and are not claimed as identical root API behavior.','limits':'Method and synthetic-software agreement only; no target key, source transcription or reading was assessed.'}
    p=OUT/'POSTSEAL_ROOT_CROSSCHECK_v1.json';p.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','orientation_direction_crosschecks','root_core_rejection_controls','root_codec_sha256','root_codec_matches_provided_baseline_hash','precomparison_files_unchanged_before_and_after','target_inputs']}))
if __name__=='__main__':main()
