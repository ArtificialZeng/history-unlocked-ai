#!/usr/bin/env python3
"""Optional public-source retrieval and exact native RGB replay; needs Pillow."""
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--picture-from', type=Path)
    ap.add_argument('--address-from', type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    # Originals are not included in the source ZIP; this is an explicit fetch action.
    roles = [('picture', args.picture_from), ('address', args.address_from)]
    got = {}
    for role, supplied in roles:
        receipt = json.loads((root/f'sources/provenance/HC1615_{role}.receipt.json').read_text())
        dest = root/f'sources/raw/HC1615_{role}_original.jpg'
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            assert digest(dest) == receipt['sha256'], 'Existing source has different bytes'
        else:
            if supplied is not None:
                body = supplied.read_bytes()
            else:
                request = urllib.request.Request(receipt['url'], headers={'User-Agent':'HC1615ResearchSourceReplay/1.0'})
                with urllib.request.urlopen(request, timeout=45) as response:
                    assert response.status == 200
                    body = response.read()
            assert hashlib.sha256(body).hexdigest() == receipt['sha256'], 'Public original changed; preserve the pinned edition'
            with dest.open('xb') as f:
                f.write(body)
        got[role] = dest
    from PIL import Image, __version__ as pillow_version
    raw = Image.open(got['picture']).convert('RGB')
    upright = raw.transpose(Image.Transpose.ROTATE_90)
    rows = json.loads((root/'data/source_v1/SOURCE_ROWS_v1.json').read_text())['rows']
    checks = []
    for row in rows:
        crop = upright.crop(tuple(row['integer90CCW_bbox']))
        rgb = hashlib.sha256(crop.tobytes()).hexdigest()
        assert rgb == row['RGB_SHA256'], row['row_id']+' RGB differs'
        dest = root/row['path']
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            crop.save(dest)
        encoded_match = digest(dest) == row['PNG_SHA256']
        checks.append({'row_id':row['row_id'],'RGB_match':True,'PNG_encoding_byte_match':encoded_match})
    print(json.dumps({'Pillow':pillow_version,'row_RGB_replays':checks,'scope':'Native whole-row pixels, not exclusive glyph masks or proof of source identity. PNG encoding can differ across library versions even when RGB matches.'},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
