"""Only frozen-source/grid and eight registered choices, no plaintext hints."""
import pathlib,json,hashlib,datetime
from grille_v1 import Grille
P=pathlib.Path(__file__).resolve().parents[1];src=json.loads((P/'data/root_source_v1/ROOT_SOURCE_FREEZE_v1.json').read_text());cipher=(P/'data/root_source_v1/preferred_supplied_hand_cipher_v1.txt').read_text().strip();k=src['physical_key'];g=Grille(k['side'],tuple(tuple(x)for x in k['holes_zeroindexed']));r=[]
for start in range(4):
 for direction in [1,-1]:
  plain=g.decrypt(cipher,start,direction);forward=g.encrypt(plain,start,direction);assert forward==cipher
  r.append({'start':start,'direction':direction,'plaintext_literal':plain,'forward_ciphertext':forward,'matches_active_letters':sum(x==y for x,y in zip(cipher,forward)),'length':len(cipher),'matches_raw_cancelled_slot':None,'source_assisted':True,'claim_scope':'Mechanicaldecode ofcurrent144activelettersunderprovidedkey; nofulloriginal145orhistoricalpriorityclaim'})
out=P/'reports/target_decode_v1';out.mkdir(exist_ok=True);(out/'ALL_EIGHT_REGISTERED_DECODES_v1.json').write_text(json.dumps({'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cipher_sha256':hashlib.sha256(cipher.encode()).hexdigest(),'provided_source_key':k,'results':r},indent=2)+'\n')
for x in r:print(x['start'],x['direction'],x['plaintext_literal'])
