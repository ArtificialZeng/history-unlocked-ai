#!/usr/bin/env python3
"""Deterministically rebuild the pinned masked fixtures and train-only model."""
import argparse
import array
import collections
import datetime
import hashlib
import math
from pathlib import Path
import random
import shutil
import sys
import unicodedata
sys.dont_write_bytecode = True
from common import MODULE, FROZEN, load, require, row_pin, save, sha
from masked_profile import apply_masks, make_masks, permutation

def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def normalized(form):
    return ''.join(c for c in unicodedata.normalize('NFKD', form).lower() if 'a' <= c <= 'z')

def parse(path):
    docs = collections.OrderedDict()
    counters = collections.Counter()
    doc, sid = None, None
    forms, token_ids = [], []
    def flush():
        nonlocal forms, token_ids, sid
        if forms:
            require(doc is not None and sid is not None, 'Missing explicit document or sentence identity')
            text = ''.join(normalized(f) for f in forms)
            docs.setdefault(doc, []).append({'sent_id':sid, 'plain':text, 'token_ids':token_ids})
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
                require(doc not in docs, 'Repeated explicit document ID')
                counters['newdoc_markers'] += 1
            elif line.startswith('# sent_id = '):
                sid = line.split(' = ', 1)[1]
            elif line.startswith('#'):
                continue
            else:
                cols = line.split('\t')
                require(len(cols) == 10, 'Bad CoNLL-U row at '+str(lineno))
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus-dir', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output, corpus = args.output.resolve(), args.corpus_dir.resolve()
    require(not output.exists(), 'Output must be a new directory')
    require(not output.is_relative_to(MODULE.resolve()) and not output.is_relative_to(corpus),
            'Rebuild outside the module and raw corpus directories')
    for item in load(MODULE/'sources.json')['files']:
        if item['filename'].endswith('.conllu'):
            path = corpus/item['filename']
            require(path.stat().st_size == item['bytes'] and sha(path) == item['sha256'],
                    'Pinned corpus bytes changed: '+item['filename'])
    profile = load(FROZEN/'PROFILE_PREREGISTRATION.json')
    require(profile['lengths'] == [400,400,500,500,600,600], 'Fixed masked profile changed')
    old_ids = load(MODULE/'REBUILD_EXCLUSIONS.json')['document_ids']
    require(len(old_ids) == len(set(old_ids)) == 6, 'Old-six document exclusion count changed')
    train_path, dev_path = corpus/'cs_pdtc-ud-train-la.conllu', corpus/'cs_pdtc-ud-dev.conllu'
    train, train_stats = parse(train_path)
    dev, dev_stats = parse(dev_path)
    train_ids = set(train)
    train_sentences = {s['plain'] for d in train.values() for s in d}
    train_documents = [''.join(s['plain'] for s in d) for d in train.values()]
    grams, letters = collections.Counter(), collections.Counter()
    for text in train_documents:
        letters.update(text)
        nums = [ord(c)-97 for c in text]
        for i in range(len(nums)-3):
            a,b,c,d = nums[i:i+4]
            grams[((a*27+b)*27+c)*27+d] += 1
    total = sum(grams.values())
    denominator = total + .01*(26**4)
    model = array.array('f', [math.log10(.01/denominator)])*(27**4)
    require(model.itemsize == 4, 'Native float is not 32 bits')
    for index, count in grams.items():
        model[index] = math.log10((count+.01)/denominator)
    output.mkdir(parents=True)
    inference, grading = output/'inference_inputs', output/'grading_gold'
    inference.mkdir()
    grading.mkdir()
    # Freeze original little-endian bytes, even on a big-endian rebuild host.
    if sys.byteorder != 'little':
        model.byteswap()
    (inference/'quadgram_model.bin').write_bytes(model.tobytes())
    frequency = sorted(range(26), key=lambda i: (-letters[chr(i+97)], i))
    (inference/'training_frequency_order.txt').write_text(' '.join(map(str,frequency))+'\n', encoding='utf-8')
    controls, gold, selected_text = [], [], []
    used, rejections = set(), collections.Counter()
    for number, (length, seed, mask_seed) in enumerate(zip(profile['lengths'],profile['permutation_seeds'],profile['mask_seeds']),1):
        chosen = None
        for doc_id, sentences in dev.items():
            if doc_id in train_ids or doc_id in used or doc_id in old_ids:
                rejections['ineligible_document'] += 1
                continue
            text, spans = '', []
            for sentence in sentences:
                if not sentence['plain'] or sentence['plain'] in train_sentences:
                    rejections['empty_or_training_sentence'] += 1
                    break
                spans.append(sentence)
                text += sentence['plain']
                if len(text) >= length:
                    excerpt = text[:length]
                    if any(excerpt in t for t in train_documents):
                        rejections['training_document_excerpt_match'] += 1
                        break
                    if excerpt in selected_text:
                        rejections['duplicate_excerpt'] += 1
                        break
                    chosen = doc_id, spans, excerpt
                    break
            if chosen:
                break
        require(chosen is not None, 'No eligible new excerpt')
        doc_id, spans, plain = chosen
        used.add(doc_id)
        selected_text.append(plain)
        enc, dec = permutation(seed)
        masks = make_masks(length, mask_seed)
        masked = set()
        for mask in masks:
            positions = set(range(mask['start'],mask['start']+mask['length']))
            require(not masked & positions, 'Overlapping masks')
            masked |= positions
        cipher, origins = apply_masks(plain, enc, masks)
        require(cipher.count(26) == len(masks) == 30, 'Mask count differs')
        cid = 'P'+str(number).zfill(2)
        path = inference/(cid+'.cipher.txt')
        path.write_text(' '.join(map(str,cipher))+'\n', encoding='utf-8')
        controls.append({'id':cid, 'kind':'positive', 'solver_seed':seed,
            'cipher_path':str(path.relative_to(output)), 'cipher_sha256':sha(path),
            'tokens':len(cipher), 'gap_marker_count':30})
        gold.append({'id':cid, 'plain':plain, 'enc_plain_to_cipher':enc, 'dec_cipher_to_plain':dec,
            'document_id':doc_id, 'source_sha256':sha(dev_path),
            'sentences':[{'sent_id':s['sent_id'], 'normalized_sentence_sha256':hashlib.sha256(s['plain'].encode()).hexdigest(),
                'normalized_sentence_length':len(s['plain']), 'token_ids':s['token_ids']} for s in spans],
            'original_length':length, 'permutation_seed':seed, 'mask_seed':mask_seed, 'masks':masks,
            'known_original_positions':[j for j in range(length) if j not in masked],
            'cipher_token_to_original_position':origins, 'unknown_original_character_count':len(masked),
            'unknown_runs':13, 'single_erasures':17})
    for number, positive in enumerate(controls[:3],1):
        cipher = [int(v) for v in (output/positive['cipher_path']).read_text().split()]
        observed = [c for c in cipher if c != 26]
        seed = positive['solver_seed'] + 200000
        random.Random(seed).shuffle(observed)
        it = iter(observed)
        shuffled = [26 if c == 26 else next(it) for c in cipher]
        require(collections.Counter(cipher) == collections.Counter(shuffled), 'Negative histogram differs')
        cid = 'N'+str(number).zfill(2)
        path = inference/(cid+'.cipher.txt')
        path.write_text(' '.join(map(str,shuffled))+'\n', encoding='utf-8')
        controls.append({'id':cid, 'kind':'frequency_preserving_observed_symbol_shuffle', 'solver_seed':seed,
            'matched_positive':positive['id'], 'cipher_path':str(path.relative_to(output)),
            'cipher_sha256':sha(path), 'tokens':len(shuffled), 'gap_marker_count':30,
            'histogram_exactly_preserved':True, 'gap_locations_exactly_preserved':True})
    save(grading/'gold.json', {'created_utc':stamp(), 'controls':gold, 'inference_must_not_read_this_file':True})
    save(inference/'RUN_CONFIG.json', {'created_utc':stamp(), 'restarts':18, 'steps_per_restart':100000,
        'model_path':'inference_inputs/quadgram_model.bin', 'frequency_path':'inference_inputs/training_frequency_order.txt',
        'controls':controls, 'unknown_sentinel':26,
        'sentinel_semantics':'UNKNOWN gap marker, not a wordspace; variable-length original gaps are not certified cipher units',
        'historical_inputs':0})
    metadata = {'started_utc':started, 'completed_utc':stamp(),
        'normalization':'Pinned public builder parse: integer FORM rows; NFKD lowercase ASCII26; no word boundaries; train documents concatenated',
        'train_stats':train_stats, 'dev_stats':dev_stats,
        'train_dev_document_id_intersection_count':len(train_ids & set(dev)),
        'model_4gram_occurrences':total, 'model_4gram_types':len(grams), 'model_smoothing':.01, 'model_byte_order':'little',
        'model_sentinel_grams':'All quadgrams containing26 receive the same floor value; model trains on no gap markers',
        'selected_document_count':len(used), 'selected_documents_distinct':len(used) == 6,
        'selected_documents_not_in_train':not bool(used & train_ids), 'selected_documents_exclude_previous_six':not bool(used & set(old_ids)),
        'selected_document_id_sha256':[hashlib.sha256(g['document_id'].encode()).hexdigest() for g in gold],
        'old_document_ids_only_extracted':True, 'old_document_id_sha256':[hashlib.sha256(i.encode()).hexdigest() for i in old_ids],
        'all_selected_full_normalized_sentences_absent_from_train':True, 'all_selected_whole_excerpts_absent_from_train_documents':True,
        'rejections':dict(rejections), 'limits':[
            'Explicit document ID/full-sentence/whole-excerpt separation only; near duplicates, author and genre independence not established',
            'Modern text has no evidence of historical domain or source error pattern equivalence']}
    save(output/'BUILD_METADATA.json', metadata)
    shutil.copyfile(FROZEN/'PROFILE_PREREGISTRATION.json', output/'PROFILE_PREREGISTRATION.json')
    save(output/'INFERENCE_PINS.json', {'artifacts':[row_pin(p,output) for p in sorted(inference.iterdir()) if p.is_file()],
        'byte_order':'little', 'scope':'New deterministic construction; no inference outputs copied'})
    print(__import__('json').dumps({'status':'BUILT_NEW_SYNTHETIC_INPUTS', 'positives':6, 'negatives':3,
        'model_sha256':sha(inference/'quadgram_model.bin'), 'selected_documents_distinct':len(used) == 6,
        'selected_documents_exclude_previous_six':not bool(used & set(old_ids)), 'historical_targets_solved':0}))

if __name__ == '__main__':
    main()
