"""Read-only exact verification of the registered final visible cryptogram."""
from pathlib import Path
import csv,hashlib,json
from portax_v1 import decrypt,encrypt,packing_pairs,effective_key
ROOT=Path(__file__).resolve().parents[1]
def load(path):return json.loads((ROOT/path).read_text())
def digest(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def verify():
    registration=load('config/TARGET_SOURCE_REGISTRATION_v1.json')
    assert digest('reports/independent_source_review_v1/source_ledger_v1.json')==registration['source_ledger_sha256']
    assert digest('reports/independent_source_review_v1/freeze_manifest_v1.json')==registration['source_manifest_sha256']
    ledger=load('reports/independent_source_review_v1/source_ledger_v1.json')
    occurrences=ledger['occurrences']
    assert len(occurrences)==180
    assert [x['global_position']for x in occurrences]==list(range(1,181))
    ct=''.join(x['visible_final_uppercase']for x in occurrences)
    assert ct==registration['ciphertext']
    candidate=load('experiments/target_first_v1/CANDIDATE_v1.json')
    assert digest('experiments/target_first_v1/SEARCH_RESULTS_v1.tsv')==candidate['first_results_sha256']
    key=candidate['effective_slides'];plain=candidate['best']['plaintext']
    assert key==[7,0,8,5,2,8]
    assert effective_key(candidate['best']['effective_key_representative'])==tuple(key)
    assert len(plain)==len(ct)==180
    assert decrypt(ct,key)==plain
    assert encrypt(plain,key)==ct
    cert=load('reports/root_forward_certificate_v1/CERTIFICATE_v1.json')
    assert len(cert)==180
    mapping={}
    for top,bottom,col in packing_pairs(180,len(key)):
        mapping[top]=(bottom,col,'top');mapping[bottom]=(top,col,'bottom')
    assert set(mapping)==set(range(180))
    for i,(source,row)in enumerate(zip(occurrences,cert)):
        for k,v in source.items():assert row[k]==v,(i,k)
        partner,col,role=mapping[i]
        assert row['decoded_letter']==plain[i]
        assert row['forward_cipher_letter']==ct[i] and row['forward_match'] is True
        assert row['paired_source_index']==partner+1
        assert row['key_column']==col+1 and row['slide']==key[col]
        assert row['pair_role']==role
    assert [i+1for i,x in enumerate(plain)if x=='X']==[95,180]
    assert registration['typed_underlayer_held_positions']==[23,66,80,132,172]
    return {'status':'PASS_EXACT_FINAL_VISIBLE_LAYER_ONLY','observed_positions':180,'rows':6,'groups':36,'period':6,'effective_slides':key,'exact_forward':True,'cipher_edits':0,'nulls':0,'position_specific_exceptions':0,'original_typed_underlayer_positions_held':5,'key_spelling_unique':False,'outside_expert_confirmation':False}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
