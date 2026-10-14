"""Pure masked-control helpers; imports never load corpus or grading data."""
import array
import collections
import random
import sys
from common import require

CPP_SHA256 = '651b888047c939dd0ce6e0d84805b8a4beba45eb6b0d8ebfe3ab43eb60681276'
MODEL_SHA256 = '64f3e69c72e7e74f5c7fd3e41c90c42321ac46879d91f3b52d6f0182c4db8a64'

def read_cipher(path):
    code = [int(v) for v in path.read_text(encoding='utf-8').split()]
    require(all(0 <= v <= 26 for v in code), 'Invalid masked cipher symbol')
    return code

def render(code, key):
    require(sorted(key) == list(range(26)), 'Invalid substitution permutation')
    return ''.join(' ' if c == 26 else chr(key[c] + 97) for c in code)

def read_model(path, byte_order='little'):
    model = array.array('f')
    model.frombytes(path.read_bytes())
    require(model.itemsize == 4 and len(model) == 27**4, 'Wrong float32 model layout')
    if sys.byteorder != byte_order:
        model.byteswap()
    return model

def score(text, model):
    require(all(c == ' ' or 'a' <= c <= 'z' for c in text), 'Invalid solver rendering')
    nums = [26 if c == ' ' else ord(c) - 97 for c in text]
    return sum(model[((nums[i]*27+nums[i+1])*27+nums[i+2])*27+nums[i+3]]
               for i in range(len(nums)-3))

def baseline(code, frequency):
    require(sorted(frequency) == list(range(26)), 'Invalid frequency permutation')
    histogram = collections.Counter(c for c in code if c != 26)
    order = sorted(range(26), key=lambda c: (-histogram[c], c))
    key = [0]*26
    for cipher_symbol, letter in zip(order, frequency):
        key[cipher_symbol] = letter
    return {'plain':render(code, key), 'key':key,
            'uses_training_frequency_only':True, 'sentinel_ignored_in_histogram':True}

def permutation(seed):
    enc = list(range(26))
    random.Random(seed ^ 0x534E54484B4559).shuffle(enc)
    dec = [0]*26
    for p, c in enumerate(enc):
        dec[c] = p
    return enc, dec

def make_masks(length, seed):
    rng = random.Random(seed)
    occupied = set()
    runs = []
    for _ in range(13):
        run_length = rng.randint(2, 5)
        starts = list(range(length-run_length+1))
        rng.shuffle(starts)
        for start in starts:
            neighborhood = set(range(max(0, start-1), min(length, start+run_length+1)))
            if not neighborhood & occupied:
                runs.append({'start':start, 'length':run_length, 'kind':'unknown_run'})
                occupied.update(range(start, start+run_length))
                break
        else:
            raise RuntimeError('Mask packing failure')
    candidates = [i for i in range(length) if i not in occupied]
    rng.shuffle(candidates)
    singles = sorted(candidates[:17])
    require(len(singles) == 17, 'Singleton mask count differs')
    return sorted(runs + [{'start':i, 'length':1, 'kind':'single_erasure'} for i in singles],
                  key=lambda x:x['start'])

def apply_masks(plain, enc, masks):
    by_start = {x['start']:x for x in masks}
    code, origins = [], []
    i = 0
    while i < len(plain):
        if i in by_start:
            code.append(26)
            origins.append(None)
            i += by_start[i]['length']
        else:
            code.append(enc[ord(plain[i])-97])
            origins.append(i)
            i += 1
    return code, origins

def gap_windows(code):
    all_windows = max(0, len(code)-3)
    gap_count = sum(26 in code[i:i+4] for i in range(all_windows))
    return {'all_quadgram_windows':all_windows, 'sentinel_containing_windows':gap_count,
            'fully_observed_windows':all_windows-gap_count}
