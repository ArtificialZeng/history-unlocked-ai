"""Reproduce the target-free control packet; default is read-only checking."""
from pathlib import Path
import hashlib,json,random,re,argparse
ROOT=Path(__file__).resolve().parents[1]
def pair(a,b,t):
    x=a if a<13 else (a-13-t)%13
    y=(b//2-t)%13
    if x==y:return ((x+t)%13+13 if a<13 else x,b^1)
    return (y if a<13 else 13+b//2,2*((x+t)%13)+b%2)
def transform(text,key):
    assert len(text)%2==0
    out=list(text);p=len(key)
    for base in range(0,len(text),2*p):
        h=min(2*p,len(text)-base)//2
        for i in range(h):
            a,b=pair(ord(text[base+i])-65,ord(text[base+h+i])-65,key[i])
            out[base+i]=chr(a+65);out[base+h+i]=chr(b+65)
    return ''.join(out)
def build():
    src=ROOT/'sources/language/validation_shelley1818.txt'
    text=src.read_text(encoding='utf-8-sig')
    s=text.index('*** START');s=text.index('\n',s)+1;e=text.index('*** END',s)
    letters=re.sub('[^A-Z]','',text[s:e].upper())
    assert transform('THEEARLYBIRDGETSTHEWORMX',[2,0,9,12])=='NIJAMPBGQCWKHQJEUIKYMPAT'
    gen=random.Random(6961952);answers=[];cases=[]
    for period in range(1,11):
        start=gen.randrange(5000,len(letters)-5000);plain=letters[start:start+180]
        key=[gen.randrange(13)for _ in range(period)]
        cid='SYNTHETIC_P%02d'%period;ct=transform(plain,key)
        assert transform(ct,key)==plain
        cases.append(cid+'\t'+ct)
        answers.append({'id':cid,'period':period,'excerpt_start':start,'plaintext':plain,'effective_slides':key,'ciphertext':ct})
    return '\n'.join(cases)+'\n',json.dumps(answers,indent=2)+'\n'
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir');args=ap.parse_args()
    cases,answers=build()
    if args.output_dir:
        d=Path(args.output_dir);d.mkdir(parents=True,exist_ok=True)
        for name,content in [('CASES_v1.tsv',cases),('SEALED_ANSWERS_v1.json',answers)]:
            p=d/name
            if p.exists():raise SystemExit('refuse overwrite '+str(p))
            p.write_text(content)
    else:
        d=ROOT/'experiments/pretarget_synthetic_v1'
        assert (d/'CASES_v1.tsv').read_text()==cases
        assert (d/'SEALED_ANSWERS_v1.json').read_text()==answers
        print('PASS exact pretarget control packet reproduction; no target read')
