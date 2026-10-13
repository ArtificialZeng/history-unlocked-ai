"""Refresh release hashes after deliberate edits; never changes scientific payloads."""
import datetime
import hashlib
import json
from pathlib import Path

from check_public_boundary import check

ROOT = Path(__file__).resolve().parents[1]


def main():
    check()
    scientific = json.loads((ROOT/'docs/CORE_PROVENANCE.json').read_text())
    for row in scientific['files']:
        raw = (ROOT/row['path']).read_bytes()
        if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('Frozen scientific payload changed: '+row['path'])
    files = []
    for p in sorted(ROOT.rglob('*')):
        rel = p.relative_to(ROOT)
        if not p.is_file() or '.git' in rel.parts or '__pycache__' in rel.parts or p.suffix == '.pyc':
            continue
        if rel == Path('CODE_CORE_MANIFEST.json'):
            continue
        raw = p.read_bytes()
        files.append({'path':str(rel),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    result = {'version':'code-core-v4',
              'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'scope':'Reproducible code, necessary evidence data, methods and brief promotion; no private correspondence or media submissions.',
              'manifest_self_excluded':True,'files':files}
    (ROOT/'CODE_CORE_MANIFEST.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'payload_files':len(files),'unchanged_scientific_files':len(scientific['files'])}))


if __name__ == '__main__':
    main()
