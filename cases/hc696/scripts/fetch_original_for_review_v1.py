"""Optional public-source fetch; invoked explicitly, never by the offline checker."""
from pathlib import Path
import hashlib,json,urllib.request
ROOT=Path(__file__).resolve().parents[1]
URL='https://api.hcportal.eu/media/2001/32451685221415.jpg'
EXPECTED='2dc894dd0aaa745eb5c7ba6155b653038cc6625817ef66ec0502125dd93f0ae4'
def main():
    path=ROOT/'sources/raw/HC696_original.jpg'
    if path.exists():
        assert hashlib.sha256(path.read_bytes()).hexdigest()==EXPECTED
        print('PASS existing original matches registered hash');return
    req=urllib.request.Request(URL,headers={'User-Agent':'HC696-reproducible-research/1.0'})
    with urllib.request.urlopen(req,timeout=30)as response:
        data=response.read(32*1024*1024+1)
    assert len(data)<=32*1024*1024,'unexpected oversized source'
    assert hashlib.sha256(data).hexdigest()==EXPECTED,'source changed; refuse adopting bytes'
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    print('PASS fetched original; native-pixel review available, no relabelling performed')
if __name__=='__main__':main()
