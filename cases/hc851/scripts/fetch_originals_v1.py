"""Optional public-source download, one request/file, exact hash checks.

No login, cookies, access-control bypass, retries or automatic alternative sources.
Default release checks do not require this step. Source rights stay with archive.
"""
import hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    meta=json.loads((ROOT/'sources/SOURCE_URLS_AND_RIGHTS_v1.json').read_text())
    result=[]
    for row in meta['originals']:
        path=ROOT/row['local_path']
        if path.exists():raw=path.read_bytes();status='existing'
        else:
            req=urllib.request.Request(row['url'],headers={'User-Agent':'HC851-research-reproducibility/1.0'})
            with urllib.request.urlopen(req,timeout=45) as response:raw=response.read()
            status='downloaded'
        if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
            raise ValueError('Official source bytes changed or mismatch; no substitution accepted: '+row['url'])
        if not path.exists():path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        result.append({'path':row['local_path'],'status':status,'sha256_exact':True})
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
