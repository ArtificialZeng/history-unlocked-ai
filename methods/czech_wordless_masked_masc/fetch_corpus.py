#!/usr/bin/env python3
"""Fetch the pinned public Czech corpus; retained raw data has CC BY-NC-SA 4.0 terms."""
import argparse
import datetime
from pathlib import Path
import sys
import urllib.request
sys.dont_write_bytecode = True
from common import MODULE, load, require, row_pin, save, sha

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args()
    target=args.output.resolve()
    require(not target.exists(), 'Output must be a new directory')
    require(not target.is_relative_to(MODULE.resolve()), 'Download corpus outside the module checkout')
    target.mkdir(parents=True)
    receipts=[]
    for item in load(MODULE/'sources.json')['files']:
        output=target/item['filename']
        with urllib.request.urlopen(item['url'], timeout=60) as response:
            content=response.read()
        output.write_bytes(content)
        require(len(content)==item['bytes'] and sha(output)==item['sha256'], 'Upstream pin changed: '+item['filename'])
        receipts.append({'url':item['url'], 'access_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(), **row_pin(output,target)})
    save(target/'FETCH_RECEIPTS.json', {'files':receipts, 'license':'CC-BY-NC-SA-4.0'})
    print('PASS: four pinned upstream files fetched; raw corpus is not part of this release')

if __name__=='__main__':main()
