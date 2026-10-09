"""Source-free controls. Does not read any target image, ledger, key or text."""
from pathlib import Path
import hashlib,json,random,datetime
from grille_even_v1 import rotate,route,encrypt,decrypt

def main():
    rng=random.Random(84920261006)
    known={'side':4,'holes':[(0,0),(1,3),(2,1),(2,3)]}
    assert encrypt('THETURNINGGRILLE',**known)=='TILUNRGHGELTENIR'
    assert decrypt('TILUNRGHGELTENIR',**known)=='THETURNINGGRILLE'
    fixtures=[]
    for side,count in [(2,4),(4,24),(6,24),(8,24),(10,24)]:
        unseen=set((r,c) for r in range(side) for c in range(side));orbits=[]
        while unseen:
            cell=min(unseen);orb=tuple(sorted({rotate(cell,side,k) for k in range(4)}))
            assert len(orb)==4;orbits.append(orb);unseen.difference_update(orb)
        distinct=set()
        while len(distinct)<count:
            distinct.add(tuple(sorted(rng.choice(orb) for orb in orbits)))
        for cuts in sorted(distinct):
            for start in range(4):
                for direction in [-1,1]:
                    for scan in ['row-major','column-major']:
                        for order in ['row-major','column-major']:
                            plain=''.join(chr(0x1000+i) for i in range(side*side*3))
                            cfg=dict(side=side,holes=cuts,start=start,direction=direction,hole_scan=scan,cipher_order=order)
                            out=encrypt(plain,**cfg);assert decrypt(out,**cfg)==plain
                            assert len(set(route(side,cuts,start,direction,scan)))==side*side
                            fixtures.append({'config':cfg,'plaintext':plain,'ciphertext':out})
    rejects=0
    for cfg in [{'side':3,'holes':[(0,0)]},{'side':4,'holes':[(0,0)]*4},{'side':4,'holes':[(0,0),(0,1),(3,3),(3,2)]},{'side':4,'holes':[(0,0),(1,3),(2,1),(4,3)]}]:
        try:route(**cfg)
        except ValueError:rejects+=1
        else:raise AssertionError('invalid key accepted')
    for bad in ['', 'short']:
        for fn in [encrypt,decrypt]:
            try:fn(bad,**known)
            except ValueError:rejects+=1
            else:raise AssertionError('invalid length accepted')
    p=Path(__file__).resolve().parents[1]/'reports/root_method_v1';p.mkdir(parents=True,exist_ok=True)
    result={'status':'PASS','seed':84920261006,'distinct_keys':100,'settings_per_key':32,'fixtures':len(fixtures),'blocks_per_fixture':3,'known_vector_checks':2,'invalid_model_or_length_rejections':rejects,'target_data_read':False,'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (p/'SYNTHETIC_FIXTURES_v1.json').write_text(json.dumps(fixtures,ensure_ascii=False,indent=2)+'\n')
    (p/'GENERIC_CONTROL_RESULT_v1.json').write_text(json.dumps(result,indent=2)+'\n')
    root=p.parents[1];files=[root/'scripts/grille_even_v1.py',root/'scripts/root_generic_controls_v1.py',p/'SYNTHETIC_FIXTURES_v1.json',p/'GENERIC_CONTROL_RESULT_v1.json']
    (p/'PRETARGET_METHOD_SEAL_v1.json').write_text(json.dumps({'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'target_data_read':False,'artifacts':[{'path':str(f.relative_to(root)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]},indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
