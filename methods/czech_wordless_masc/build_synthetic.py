#!/usr/bin/env python3
"""Build only the pinned synthetic Czech controls; standard library, no legacy imports."""
import argparse
import array
import collections
import datetime
import hashlib
import json
import math
from pathlib import Path
import random
import shutil
import unicodedata

ROOT = Path(__file__).resolve().parent

def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def digest(path):
    return {'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def normalized(form):
    return ''.join(c for c in unicodedata.normalize('NFKD', form).lower()
                   if 'a' <= c <= 'z')

def parse(path):
    docs = collections.OrderedDict()
    counters = collections.Counter()
    doc = None
    sid = None
    forms = []
    token_ids = []
    def flush():
        nonlocal forms, token_ids, sid
        if forms:
            if doc is None or sid is None:
                raise RuntimeError('Missing explicit document or sentence identity')
            text = ''.join(normalized(f) for f in forms)
            docs.setdefault(doc, []).append({'sent_id': sid, 'plain': text,
                                             'token_ids': token_ids})
            counters['sentences'] += 1
            counters['normalized_characters'] += len(text)
        forms, token_ids, sid = [], [], None
    with path.open(encoding='utf-8') as stream:
        for lineno, line in enumerate(stream, 1):
            line = line.rstrip('\n')
            if not line:
                flush()
                continue
            if line.startswith('# newdoc id = '):
                flush()
                doc = line.split(' = ', 1)[1]
                if doc in docs:
                    raise RuntimeError('Repeated explicit document id')
                counters['newdoc_markers'] += 1
            elif line.startswith('# sent_id = '):
                sid = line.split(' = ', 1)[1]
            elif line.startswith('#'):
                continue
            else:
                cols = line.split('\t')
                if len(cols) != 10:
                    raise RuntimeError(f'Bad CoNLL-U row at {lineno}')
                if not cols[0].isdigit():
                    counters['range_or_empty_node_rows_excluded'] += 1
                    continue
                forms.append(cols[1])
                token_ids.append(cols[0])
                counters['integer_FORM_rows'] += 1
                if not normalized(cols[1]):
                    counters['FORM_rows_yielding_no_letters'] += 1
    flush()
    counters['documents'] = len(docs)
    return docs, dict(counters)

def main():
    started = stamp()
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus-dir', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    module = Path(__file__).resolve().parent
    ROOT = args.output.resolve()
    if ROOT.exists():
        raise RuntimeError('Output must be a new directory; frozen data will not be overwritten')
    for item in json.loads((module/'sources.json').read_text())['files']:
        if not item['filename'].endswith('.conllu'):
            continue
        resource = args.corpus_dir/item['filename']
        if resource.stat().st_size != item['bytes'] or hashlib.sha256(resource.read_bytes()).hexdigest() != item['sha256']:
            raise RuntimeError('Pinned corpus content changed: '+item['filename'])
    ROOT.mkdir(parents=True)
    profile = json.loads((module/'frozen/PROFILE_PREREGISTRATION.json').read_text())
    train_path = args.corpus_dir/'cs_pdtc-ud-train-la.conllu'
    dev_path = args.corpus_dir/'cs_pdtc-ud-dev.conllu'
    train, train_stats = parse(train_path)
    dev, dev_stats = parse(dev_path)
    train_ids, dev_ids = set(train), set(dev)
    intersection = sorted(train_ids & dev_ids)
    train_sentence_set = {s['plain'] for doc in train.values() for s in doc}
    train_document_strings = [''.join(s['plain'] for s in doc) for doc in train.values()]
    inference = ROOT/'inference_inputs'
    grading = ROOT/'grading_gold'
    inference.mkdir(exist_ok=True)
    grading.mkdir(exist_ok=True)
    model_counts = collections.Counter()
    letters = collections.Counter()
    for text in train_document_strings:
        letters.update(text)
        nums = [ord(c)-97 for c in text]
        for i in range(len(nums)-3):
            a,b,c,d = nums[i:i+4]
            model_counts[((a*27+b)*27+c)*27+d] += 1
    total = sum(model_counts.values())
    smoothing = 0.01
    denominator = total + smoothing*(26**4)
    floor = math.log10(smoothing/denominator)
    model = array.array('f', [floor])*(27**4)
    for idx, count in model_counts.items():
        model[idx] = math.log10((count+smoothing)/denominator)
    if model.itemsize != 4:
        raise RuntimeError('Native float array is not 4 bytes')
    with (inference/'quadgram_model.bin').open('wb') as out:
        model.tofile(out)
    freq = sorted(range(26), key=lambda i: (-letters[chr(i+97)], i))
    (inference/'training_frequency_order.txt').write_text(' '.join(map(str,freq))+'\n')
    controls = []
    gold = []
    used_docs = set()
    selected_plaintexts = []
    rejections = collections.Counter()
    for number, (length, seed) in enumerate(zip(profile['lengths'], profile['seeds']), 1):
        rng = random.Random(seed)
        ids = sorted(dev)
        rng.shuffle(ids)
        selected = None
        for doc_id in ids:
            if doc_id in train_ids:
                rejections['document_id_in_train'] += 1
                continue
            if doc_id in used_docs:
                rejections['document_already_selected'] += 1
                continue
            sentences = dev[doc_id]
            starts = list(range(len(sentences)))
            rng.shuffle(starts)
            for start in starts:
                spans = []
                text = ''
                for sent in sentences[start:]:
                    if not sent['plain'] or sent['plain'] in train_sentence_set:
                        rejections['empty_or_full_sentence_train_overlap'] += 1
                        break
                    spans.append(sent)
                    text += sent['plain']
                    if len(text) >= length:
                        excerpt = text[:length]
                        if any(excerpt in t for t in train_document_strings):
                            rejections['entire_excerpt_train_substring_overlap'] += 1
                            break
                        if excerpt in selected_plaintexts:
                            rejections['duplicate_selected_excerpt'] += 1
                            break
                        selected = (doc_id, start, spans, excerpt)
                        break
                if selected:
                    break
            if selected:
                break
        if selected is None:
            raise RuntimeError(f'No independent excerpt for control {number}')
        doc_id, start, spans, plain = selected
        used_docs.add(doc_id)
        selected_plaintexts.append(plain)
        enc = list(range(26))
        random.Random(seed ^ 0x534E54484B4559).shuffle(enc)
        dec = [0]*26
        for p,c in enumerate(enc):
            dec[c] = p
        cipher = [enc[ord(c)-97] for c in plain]
        cid = f'P{number:02d}'
        cipher_path = inference/f'{cid}.cipher.txt'
        cipher_path.write_text(' '.join(map(str,cipher))+'\n')
        controls.append({'id':cid,'kind':'positive','length':length,'seed':seed,
                         'cipher_path':str(cipher_path.relative_to(ROOT)),'cipher_sha256':digest(cipher_path)['sha256']})
        gold.append({'id':cid,'plain':plain,'enc_plain_to_cipher':enc,'dec_cipher_to_plain':dec,
                     'document_id':doc_id,'dev_start_sentence_index':start,
                     'source_path':dev_path.name,'source_sha256':hashlib.sha256(dev_path.read_bytes()).hexdigest(),
                     'sentences':[{'sent_id':s['sent_id'],'full_normalized_sentence_sha256':
                                   hashlib.sha256(s['plain'].encode()).hexdigest(),
                                   'full_normalized_sentence_length':len(s['plain']),
                                   'token_ids':s['token_ids']} for s in spans],
                     'excerpt_starts_at_sentence_start':True,
                     'excerpt_ends_at_character':length,
                     'full_sentences_exactly_absent_from_train':True,
                     'entire_excerpt_absent_as_train_document_substring':True})
    for num, positive_index in enumerate([0,2,4], 1):
        positive = controls[positive_index]
        cipher = [int(x) for x in (ROOT/positive['cipher_path']).read_text().split()]
        neg_seed = positive['seed'] + 900
        random.Random(neg_seed).shuffle(cipher)
        cid = f'N{num:02d}'
        path = inference/f'{cid}.cipher.txt'
        path.write_text(' '.join(map(str,cipher))+'\n')
        controls.append({'id':cid,'kind':'matched_frequency_shuffle','length':len(cipher),
                         'seed':neg_seed,'matched_positive':positive['id'],
                         'cipher_path':str(path.relative_to(ROOT)),'cipher_sha256':digest(path)['sha256'],
                         'histogram_exactly_preserved':True})
    write_json(grading/'gold.json', {'created_utc':stamp(),'controls':gold,
                                   'gold_may_be_read_only_after_inference_completion':True})
    metadata = {'started_utc':started,'completed_utc':stamp(),
                'normalization':'CoNLL-U integer-ID FORM only; NFKD then lowercase, retain ASCII a-z only; no boundaries; range/empty node rows excluded; document concatenation for training',
                'train_stats':train_stats,'dev_stats':dev_stats,
                'train_dev_document_id_intersection_count':len(intersection),
                'selected_document_count':len(used_docs),'selected_documents_distinct':len(used_docs)==6,
                'selected_documents_not_in_train':not (used_docs & train_ids),
                'rejection_counts':dict(rejections),'all_selected_full_sentences_absent_from_train':True,
                'all_selected_excerpts_absent_as_train_document_substring':True,
                'train_4gram_occurrences':total,'train_4gram_types':len(model_counts),
                'model':'log10 add-0.01 smoothed train-only wordless 4grams, 27^4 native float layout, symbol 26 unused',
                'model_native_float_byte_order':__import__('sys').byteorder,
                'training_letter_counts':dict(letters),
                'resource_independence_limit':'Exact document IDs, normalized full sentences and whole excerpt substrings were checked against declared train only; shared genre, source collection, author or near-duplicate paraphrases were not ruled out.'}
    write_json(ROOT/'BUILD_METADATA.json', metadata)
    write_json(inference/'CONTROL_MANIFEST.json', {'created_utc':stamp(),'controls':controls,
                'model_path':str((inference/'quadgram_model.bin').relative_to(ROOT)),
                'frequency_path':str((inference/'training_frequency_order.txt').relative_to(ROOT)),
                'no_plaintext_or_key_values':True})
    frozen = [digest(p) for p in sorted(inference.iterdir()) if p.is_file()]
    write_json(ROOT/'INPUT_FREEZE.json', {'created_utc':stamp(),'inference_inputs':frozen,
                                        'gold_hashes':[digest(grading/'gold.json')],
                                        'answer_recovery_threshold_exact':5,'positive_count_required':6,
                                        'selection_not_conditioned_on_solver_output':True})
    shutil.copyfile(module/'generic_solver.cpp', ROOT/'generic_solver.cpp')
    shutil.copyfile(module/'frozen/FROZEN_RUN_CONFIG.json', ROOT/'FROZEN_RUN_CONFIG.json')
    # This new bundle is construction replay; no solver result is silently copied.
    write_json(ROOT/'INFERENCE_PINS.json', {'artifacts':[digest(p) for p in sorted(inference.iterdir()) if p.is_file()], 'byte_order':__import__('sys').byteorder})
    print(json.dumps({'positive_count':6,'negative_count':3,'train_stats':train_stats,
                      'dev_stats':dev_stats,'train_dev_doc_intersections':len(intersection),
                      'selected_documents_distinct':True,'model_4grams':total,'completed_utc':stamp()}))

if __name__ == '__main__':
    main()
