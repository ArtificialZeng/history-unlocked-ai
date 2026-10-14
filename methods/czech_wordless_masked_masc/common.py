"""Portable helpers. No corpus, plaintext or grading data is loaded here."""
import hashlib
import json
from pathlib import Path

MODULE = Path(__file__).resolve().parent
FROZEN = MODULE / 'frozen'

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def require(value, message):
    if not value:
        raise RuntimeError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def safe_path(root, relative):
    root = Path(root).resolve()
    require(not Path(relative).is_absolute(), 'Absolute artifact path rejected')
    path = (root / relative).resolve()
    require(path.is_relative_to(root), 'Artifact escapes bundle')
    return path

def verify_pins(root, rows):
    for row in rows:
        path = safe_path(root, row['path'])
        require(path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], 'Artifact pin mismatch: '+row['path'])

def row_pin(path, root):
    path = Path(path)
    return {'path':str(path.relative_to(root)), 'bytes':path.stat().st_size, 'sha256':sha(path)}
