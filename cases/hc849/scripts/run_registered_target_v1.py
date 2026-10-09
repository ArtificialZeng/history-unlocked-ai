"""Run the already registered finite target projections without source edits."""
from pathlib import Path
import json,hashlib,datetime
from grille_even_v1 import decrypt,encrypt,route,rotate

ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    regpath=ROOT/'config/TARGET_METHOD_REGISTRATION_v1.json'
    reg=json.loads(regpath.read_text())
    assert reg['target_full_or_partial_decode_runs_before_registration']==0
    assert reg['settings_cap']==len(reg['settings'])==32
    assert digest(ROOT/'reports/cold_source_v1/SOURCE_FREEZE_MANIFEST_v1.json')==reg['frozen_source_manifest_sha256']
    typed=json.loads((ROOT/reg['ciphertext_file']).read_text())
    key=json.loads((ROOT/reg['physical_key_file']).read_text())
    cipher=typed['stream_ascii']
    assert len(cipher)==typed['current_count']==64
    assert ''.join(p['current'] for p in typed['positions'])==cipher
    holes=[(c['row']-1,c['column']-1) for c in key['cells'] if c['cut']]
    assert len(holes)==16 and key['coarse_rows']==key['coarse_columns']==8
    records=[];all_cert=[];started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    for settings in reg['settings']:
        kwargs=dict(side=8,holes=holes,**settings)
        plaintext=decrypt(cipher,**kwargs)
        regenerated=encrypt(plaintext,**kwargs)
        assert regenerated==cipher
        visits=route(8,holes,settings['start'],settings['direction'],settings['hole_scan'])
        cid='a%s_d%s_h%s_c%s'%(settings['start'],settings['direction'],settings['hole_scan'],settings['cipher_order'])
        rec={'id':cid,'settings':settings,'plaintext_literal':plaintext,'reencrypted_literal':regenerated,'exact_source_positions':64,'is_registered_preferred':settings==reg['preferred_before_outputs']}
        records.append(rec);cert=[]
        for i,(r,c) in enumerate(visits):
            source_i=r*8+c if settings['cipher_order']=='row-major' else c*8+r
            source=typed['positions'][source_i]
            turn=i//16
            initial=rotate((r,c),8,-settings['start']-settings['direction']*turn)
            hole=next(x for x in key['cells'] if x['row']-1==initial[0] and x['column']-1==initial[1])
            assert hole['cut'] and plaintext[i]==cipher[source_i]
            cert.append({'plaintext_position':i+1,'plaintext_letter':plaintext[i],'source_position':source_i+1,'current_source_letter':cipher[source_i],'matrix_row':r+1,'matrix_column':c+1,'turn_index':turn,'initial_physical_cell_id':hole['cell_id'],'typed_source_record':source,'physical_cut_record':hole})
        assert len({a['source_position'] for a in cert})==64
        all_cert.append({'id':cid,'settings':settings,'certificate':cert})
    out=ROOT/'reports/registered_target_v1';out.mkdir(exist_ok=False)
    result={'started_utc':started,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'registered_settings':32,'all_forward_exact':True,'source_letters_or_key_changes':0,'candidate_selection_using_language':False,'whole_previous_source_layer_claim':False,'unknown_key_recovery':False,'registered_config_sha256':digest(regpath),'records':records}
    (out/'ALL_32_REGISTERED_PROJECTIONS_v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (out/'ALL_32_SOURCE_POSITION_CERTIFICATES_v1.json').write_text(json.dumps(all_cert,ensure_ascii=False,indent=2)+'\n')
    preferred=[x for x in records if x['is_registered_preferred']];assert len(preferred)==1
    (out/'PREFERRED_CURRENT_LAYER_LITERAL_v1.json').write_text(json.dumps(preferred[0],indent=2)+'\n')
    files=list(out.glob('*.json'))+[Path(__file__).resolve()]
    (out/'TARGET_RESULT_SEAL_v1.json').write_text(json.dumps({'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'artifact_hashes':[{'path':str(f.relative_to(ROOT)),'bytes':f.stat().st_size,'sha256':digest(f)} for f in files]},indent=2)+'\n')
    print(json.dumps({'target_runs':32,'preferred':preferred[0],'all_forward_exact_64':True}))

if __name__=='__main__':main()
