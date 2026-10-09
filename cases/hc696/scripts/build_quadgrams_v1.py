from pathlib import Path
import collections,struct,math,json,hashlib,re
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/"sources/language/training_doyle1892.txt"
text=src.read_text(encoding="utf-8-sig")
start=text.index("*** START");start=text.index("\n",start)+1
end=text.index("*** END",start)
letters=re.sub("[^A-Z]","",text[start:end].upper())
cts=collections.Counter(letters[i:i+4] for i in range(len(letters)-3))
total=sum(cts.values());den=total+0.01*26**4
vals=[]
for i in range(26**4):
 n=i;s=""
 for j in range(4):s=chr(65+n%26)+s;n//=26
 vals.append(math.log((cts[s]+0.01)/den))
out=ROOT/"config/quadgrams_v1.bin"
if out.exists():raise SystemExit("refuse overwrite model")
out.write_bytes(struct.pack("<"+str(len(vals))+"f",*vals))
(ROOT/"config/MODEL_RECEIPT_v1.json").write_text(json.dumps({"training_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"source_alpha_letters":len(letters),"quadgram_windows":total,"unique_quadgrams":len(cts),"alpha":0.01,"format":"26^4 littleendian float32,naturallogs","sha256":hashlib.sha256(out.read_bytes()).hexdigest()},indent=2)+"\n")
print(len(letters),len(cts))
