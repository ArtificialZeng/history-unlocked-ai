"""Read-only offline HC851 mechanical/source-certificate replay (stdlib only).

Original images are separately accessed via their official URLs. This checker
replays frozen transcription/provenance records; it does not perform new visual
reading or establish historical priority. No LLM or language score is used.
"""
import argparse, copy, csv, hashlib, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
from independent_grille_v1 import encrypt, decrypt, permutation, GrilleError
from grille_v1 import Grille
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text())
def require(condition,message):
    if not condition:raise ValueError(message)
def digest(text):return hashlib.sha256(text.encode()).hexdigest()
def inputs():
    c=(ROOT/'data/cold_source_v1/PRIMARY_TYPED_ACTIVE_STREAM_v1.txt').read_text().strip()
    s=load('reports/independent_candidate_audit_v1/FINAL_CANDIDATE_AUDIT_SUMMARY_v1.json')
    g=load('data/cold_source_v1/PHYSICAL_PUBLIC_GRILLE_GEOMETRY_v1.json')
    r=load('data/cold_source_v1/PRIMARY_TYPED_ALL_PLACEMENTS_v1.json')['records']
    a=load('reports/independent_candidate_audit_v1/ALL_144_ACTIVE_SOURCE_FORWARD_CERTIFICATE_v1.json')
    return c,s['literal_plaintext_unchanged'],g,r,a
def validate(c,p,g,r,a):
    require(len(c)==len(p)==144,'active extent is not144')
    require(len(r)==145 and len(a)==144,'source/certificate extents differ')
    holes=tuple(sorted(row*6+col+1 for row,col in g['holes_row_column_0based']))
    require(g['cut_cells_count']==9 and g['coarse_cut_lattice']['rows']==6 and g['coarse_cut_lattice']['columns']==6,'wrong geometry')
    require(decrypt(c,6,holes)==p and encrypt(p,6,holes)==c,'independent target forward/decode mismatch')
    other=Grille(6,tuple(tuple(x) for x in g['holes_row_column_0based']))
    require(other.encrypt(p)==c and other.decrypt(c)==p,'root target forward/decode mismatch')
    active=sorted([x for x in r if x['active_index_1based'] is not None],key=lambda x:x['active_index_1based'])
    require([x['active_index_1based'] for x in active]==list(range(1,145)),'source active index coverage')
    require(''.join(x['ASCII_final_visible'] for x in active)==c,'source letters differ from frozen active stream')
    require([x['raw_placement_index_1based'] for x in r]==list(range(1,146)),'raw position coverage')
    cancel=r[138];require(cancel['active_index_1based'] is None and cancel['ASCII_final_visible'] is None and cancel['underlay_ASCII'] is None,'cancelled raw139 must remain explicit unknown')
    require(active[27]['ASCII_final_visible']=='F' and active[27]['underlay_ASCII'] is None,'F28 unknown old layer lost')
    route=permutation(6,holes)
    require(len(set(route))==36,'not complete grille coverage')
    require({x['active_cipher_position_1indexed'] for x in a}==set(range(1,145)),'certificate cipher coverage')
    require({x['plaintext_position_1indexed'] for x in a}==set(range(1,145)),'certificate payload coverage')
    ledger={x['active_index_1based']:x for x in active}
    for x in a:
        i=x['active_cipher_position_1indexed'];j=x['plaintext_position_1indexed'];k=ledger[i]
        require(c[i-1]==p[j-1]==x['source_character']==x['literal_payload_character'],'certificate literal mismatch')
        require(i==(j-1)//36*36+route[(j-1)%36]+1,'certificate route mismatch')
        require(k['raw_placement_index_1based']==x['primary_raw_position_1indexed'],'certificate raw mapping mismatch')
        require(k['native_box_xyxy']==x['primary_source']['native_box_xyxy'],'source coordinate mismatch')
        require(k['source_sha256']==x['primary_source']['source_sha256'],'source hash mismatch')
        require(x['public_key_physical_hole']['source_sha256']==g['source_sha256'],'key source hash mismatch')
        require(x['physical_source_provenance']=='FROZEN_PRIMARY_AND_PUBLIC_KEY_VERIFIED','physical source certificate not complete')
    return holes
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--integrity-tests',action='store_true');args=parser.parse_args()
    c,p,g,r,a=inputs();holes=validate(c,p,g,r,a)
    eight=load('reports/independent_candidate_audit_v1/ALL_EIGHT_INDEPENDENT_DECODES_v1.json')['results']
    require(len(eight)==8,'eight-choice coverage')
    for row in eight:
        start=row['start_turn'];direction=row['direction']
        plain=decrypt(c,6,holes,start_turn=start,direction=direction)
        require(plain==row['literal_plaintext'] and encrypt(plain,6,holes,start_turn=start,direction=direction)==c,'registered decode mismatch')
    neighbors=load('reports/independent_candidate_audit_v1/FIXED_LITERAL_27_SINGLE_ORBIT_NEIGHBORS_v1.json')['cases']
    require(len(neighbors)==27,'neighbor budget mismatch')
    for row in neighbors:
        forward=encrypt(p,6,row['changed_holes_1indexed'])
        require(forward==row['forward_ciphertext'] and forward!=c,'neighbor falsification mismatch')
    fixture_rows=load('reports/independent_method_v1/INDEPENDENT_SYNTHETIC_FIXTURES_v1.json');count=0
    require(len({(x['side'],tuple(x['holes_1indexed'])) for x in fixture_rows})==100,'100 distinct software grilles required')
    for f in fixture_rows:
        n=f['side'];h=f['holes_1indexed'];plain=f['plaintext'];other=Grille(n,tuple(divmod(x-1,n) for x in h))
        for row in f['controls']:
            start=row['start_turn'];direction=row['direction'];cipher=encrypt(plain,n,h,start_turn=start,direction=direction)
            require(digest(cipher)==row['ciphertext_sha256'],'synthetic control hash mismatch')
            require(decrypt(cipher,n,h,start_turn=start,direction=direction)==plain,'synthetic roundtrip mismatch')
            require(other.encrypt(plain,start,direction)==cipher,'two software implementations differ')
            count+=1
    require(count==800,'software budget mismatch')
    require(encrypt('THETURNINGGRILLE',4,[1,8,10,12])=='TILUNRGHGELTENIR','ACA primary worked vector')
    tested=[]
    if args.integrity_tests:
        cases=[]
        q=list(p);q[0]='A' if p[0]!='A' else 'B';cases.append(('changed_plaintext',(c,''.join(q),g,r,a)))
        q=list(c);q[0]='A' if c[0]!='A' else 'B';cases.append(('changed_ciphertext',(''.join(q),p,g,r,a)))
        z=copy.deepcopy(a);z[0]['primary_source']['native_box_xyxy'][0]+=1;cases.append(('changed_coordinate',(c,p,g,r,z)))
        z=copy.deepcopy(r);z[138]['underlay_ASCII']='A';cases.append(('invented_cancelled_layer',(c,p,g,z,a)))
        z=copy.deepcopy(g);z['holes_row_column_0based'][0]=[0,1];cases.append(('changed_key_hole',(c,p,z,r,a)))
        for label,values in cases:
            try:validate(*values)
            except (ValueError,GrilleError):tested.append({'case':label,'rejected':True})
            else:raise ValueError('tampered evidence accepted: '+label)
    print(json.dumps({'status':'PASS','current_active_letters':144,'raw_placements_preserved':145,'certified_source_positions':144,'source_key_public':True,'independent_forward_exact':True,'root_forward_exact':True,'registered_decodes_checked':8,'limited_neighbors_checked':27,'synthetic_controls_replayed':count,'integrity_tests':tested,'historical_priority_or_global_uniqueness_established':False},indent=2))
if __name__=='__main__':main()
