#!/usr/bin/env python3
"""Source-only independent transcription, entered from original pixels.

No OCR, cipher method, language scoring or primary observer data is used.
Coordinates refer to the unchanged 3024 x 4032 JPEG; boxes are generous
provenance windows, not an inferred exact segmentation of individual ink.
"""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent.parent
SOURCE = ROOT / 'sources/raw/HC696_original.jpg'
ROWS = [
    ['CIUSW', 'INBAX', 'ERHPB', 'WPXOQ', 'YKPVA', 'GUSRB'],
    ['KWXKJ', 'UKILR', 'WBCJW', 'MTYLZ', 'WUSUF', 'CBKDA'],
    ['UGTKS', 'NKJFS', 'JLZGM', 'MWZWB', 'EKKMN', 'LNAJT'],
    ['SQMZL', 'JCIMS', 'WIFNE', 'NEQPN', 'SWQRC', 'CPNLM'],
    ['MQNSD', 'MLWMK', 'ZHKHL', 'ENXJI', 'VKPMW', 'ASSHI'],
    ['NKDJR', 'ZCWJT', 'BFPNG', 'BQZGP', 'HWZYO', 'EKNCL'],
]
# Manual centers initially located in the displayed source at 1368 x 1824;
# conversion to original pixels is explicit and reversible.
XS = [
    [87,121,157,195,229,299,335,372,404,440,509,546,580,618,655,720,758,793,829,864,932,966,1002,1037,1072,1145,1179,1217,1251,1288],
    [92,125,160,198,236,302,337,372,411,445,511,547,583,616,653,722,758,793,829,865,936,970,1023,1057,1092,1162,1197,1232,1266,1322],
    [97,134,167,205,242,309,346,381,417,452,519,556,591,628,663,730,768,803,837,864,936,970,1024,1059,1095,1170,1206,1242,1275,1310],
    [106,140,177,213,247,313,347,382,420,454,521,556,592,627,662,728,762,796,831,865,940,975,1009,1043,1078,1147,1183,1218,1251,1288],
    [106,140,177,211,246,316,352,386,423,458,523,556,591,627,662,729,762,797,830,865,940,976,1010,1045,1081,1147,1182,1218,1254,1289],
    [112,149,183,218,251,322,358,392,428,463,530,567,601,636,670,730,765,800,835,869,944,979,1014,1048,1082,1148,1181,1217,1251,1287],
]
Y_MODEL = [(367.1,-.02415),(468.3,-.024),(569.2,-.024),(667.2,-.021),(768,-.0225),(868.7,-.027)]
SCALE = 3024/1368

def pos(row, group, site):
    return f'R{row:02d}G{group:02d}P{site:02d}'

def bbox(row, n):
    x = XS[row-1][n]
    a,b = Y_MODEL[row-1]
    x,y = round(x*SCALE),round((a+b*x)*SCALE)
    return [x-38,y-44,x+38,y+44]

OVERSTRIKES = [
    {'id':'D01','position':pos(1,5,3),'final_visible':'P','bbox':[2190,716,2254,809],
     'evidence':'Dark left stem and single upper rounded bowl, with no lower bowl; violet remnants at top/left are partly covered.','crop':'crops/r1g5_2x.png'},
    {'id':'D02','position':pos(3,2,1),'final_visible':'N','bbox':[654,1199,707,1278],
     'evidence':'Dark two vertical strokes joined by descending diagonal; violet residual ink is visible above the right vertical.','crop':'crops/r3g2_2x.png'},
    {'id':'D03','position':pos(3,4,5),'final_visible':'B','bbox':[1870,1172,1941,1247],
     'evidence':'Dark left stem and two stacked rounded lobes; violet remnants occur inside lower lobe and near upper-right serif.','crop':'crops/r3g4_2x.png'},
    {'id':'D04','position':pos(5,3,2),'final_visible':'H','bbox':[1208,1632,1271,1711],
     'evidence':'Dark two upright stems joined by horizontal midbar; violet ink survives near upper left/interior.','crop':'crops/r5g3_2x.png'},
    {'id':'D05','position':pos(6,5,2),'final_visible':'W','bbox':[2114,1810,2181,1888],
     'evidence':'Dark zigzag has two low troughs and three high endpoints, with right rising stroke longer than violet type; violet top serifs survive.','crop':'crops/r6g5_2x.png'},
]
for e in OVERSTRIKES:
    e.update({'final_confidence':'high','underlying_visible_letter':None,
              'underlying_alternatives':[],
              'underlying_status':'unresolved: no restricted letter set is defensible from the exposed residual pixels',
              'operation_status':'handwritten letter superposed; replacement versus reinforcement of the same letter cannot be established',
              'hold':True})

UNDERLINES = [
    {'id':'U01','bbox':[479,802,700,850],'positions':[pos(1,1,5),pos(1,2,1)],
     'evidence':'Dark upward-right line begins under W and crosses the inter-block gap to the lower area of I.','crop':'crops/r1underline1_2x.png'},
    {'id':'U02','bbox':[1098,792,1249,824],'positions':[pos(1,3,1),pos(1,3,2)],
     'evidence':'Dark almost horizontal line under E/R; lower portions of these typed letters remain legible.','crop':'crops/r1underline2_2x.png'},
    {'id':'U03','bbox':[1150,1464,1248,1510],'positions':[pos(4,3,1),pos(4,3,2)],
     'evidence':'Two or more dark short horizontal strokes beneath W/I, thickening the underline at I.','crop':'crops/r4underline1_2x.png'},
    {'id':'U04','bbox':[1665,1446,1784,1480],'positions':[pos(4,4,2),pos(4,4,3)],
     'evidence':'Dark upward-right stroke beneath E/Q. Q has a visible lower-right tail above/near the mark.','crop':'crops/r4underline2_2x.png'},
]
OTHER_MARKS = [
    {'id':'M01','bbox':[104,423,1230,608],'kind':'header and rules',
     'preferred_visible_text':'Anglický text čís. 7',
     'literal_diacritic_hold':'Small mark over header i after č is not resolved into acute versus dot with high confidence; preferred text is a visual transcription, not a cipher observation.',
     'evidence':'Violet type, violet dashed line below, and red rising diagonal crossing the header.','crop':'crops/header_2x.png'},
    {'id':'M02','bbox':[2145,480,2256,606],'kind':'dark check-like handwritten mark',
     'evidence':'Two joined dark strokes above cipher block; no cipher position.'},
    {'id':'M03','bbox':[2490,118,2714,353],'kind':'magenta numeral',
     'visible':'4','evidence':'Large magenta handwritten/stamped numeral at upper right; no cipher position.'},
    {'id':'M04','bbox':[0,726,75,884],'kind':'red left-margin stroke',
     'evidence':'Red slanting stroke partly clipped by image edge, left of row 1.'},
    {'id':'M05','bbox':[2804,1600,2880,1760],'position':pos(5,6,5),'kind':'lower-right ink and gray extension at typed I',
     'evidence':'Typed I is readable from top/bottom serifs and upright. A violet-blue concentration at its lower-right and gray vertical extension below it are retained as an unclassified source mark, not an alternate letter.','crop':'crops/row5_lastblock_2x.png'},
    {'id':'M06','bbox':[387,2044,430,2247],'kind':'thin vertical noncipher stroke',
     'evidence':'Thin dark/violet line below row 6 under first block; no letter or word reading assigned.'},
]

sites=[]
for row,groups in enumerate(ROWS,1):
    for group,s in enumerate(groups,1):
        for site,c in enumerate(s,1):
            name=pos(row,group,site)
            events=[e['id'] for e in OVERSTRIKES if e['position']==name]
            events += [e['id'] for e in UNDERLINES if name in e['positions']]
            events += [e['id'] for e in OTHER_MARKS if e.get('position')==name]
            sites.append({'index_1based':len(sites)+1,'position':name,'row':row,'group':group,'site':site,
                          'final_visible':c,'final_confidence':'high','source':'sources/raw/HC696_original.jpg',
                          'bbox_original_px':bbox(row,(group-1)*5+site-1),'events':events,
                          'reading_layer':'dark handwritten final' if any(e['position']==name for e in OVERSTRIKES) else 'violet typewritten'})

compact=''.join(''.join(r) for r in ROWS)
assert len(compact)==len(sites)==180
assert all(len(r)==6 and all(len(g)==5 for g in r) for r in ROWS)
record={
    'record_id':'HC696_independent_own_source_freeze_v1',
    'stage':'source-only; frozen before primary observer comparison',
    'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'source_dimensions_px':[3024,4032],
    'bbox_convention':'[left,top,right,bottom], original JPEG pixels; generous manual windows; not exact ink segmentation',
    'source_geometry':{'rows':6,'blocks_per_row':6,'sites_per_block':5,'visible_alphabetic_sites':180,
                       'extra_intrablock_spacing':[{'row':2,'group':5,'visual':'WU SUF','after_site':2},
                                                 {'row':2,'group':6,'visual':'CBKD A','after_site':4}],
                       'spacing_note':'Six five-site blocks are retained from recurring layout. Additional visible gaps in row 2 are explicitly preserved and not interpreted as content.'},
    'rows':ROWS,'compact_visible_final':compact,
    'compact_utf8_sha256':hashlib.sha256(compact.encode()).hexdigest(),
    'sites':sites,'dark_letter_events':OVERSTRIKES,'underline_events':UNDERLINES,'other_marks':OTHER_MARKS,
    'source_holds':{'final_layer_letter_holds':[],
                    'earlier_layer_holds':[e['id'] for e in OVERSTRIKES],
                    'mark_holds':['M01','M05'],
                    'requirement':'Neither an original violet character nor correction history may be inferred from a readable final dark letter.'},
    'exposures':{'read':['AGENTS.md','sources/SOURCE_ONLY_SCOPE_v1.md','sources/SOURCE_ADOPTION_RECEIPT_v1.json',
                         'sources/raw/HC696_detail_current.json','sources/raw/HC696_original.jpg','own crops only'],
                 'known_from_scope':['catalogue cipher category/name PORTAX','catalogue language English','catalogue state Not solved','catalogue date circa 1952'],
                 'not_read':['primary observer ledger','method or key files','experiments','plaintext or candidates','root README/protocol/state','other-puzzle contents'],
                 'network_calls':0,'root_state_changes':False,'git_actions':False},
}
def dump(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
dump(BASE/'OWN_SOURCE_FREEZE_v1.json',record)
(BASE/'OWN_COMPACT_VISIBLE_FINAL_v1.txt').write_text(compact+'\n',encoding='utf-8')
(BASE/'OWN_GROUPED_VISIBLE_FINAL_v1.txt').write_text('\n'.join(' '.join(r) for r in ROWS)+'\n',encoding='utf-8')
dump(BASE/'OWN_HOLDS_v1.json',record['source_holds'])
files=['OWN_SOURCE_FREEZE_v1.json','OWN_COMPACT_VISIBLE_FINAL_v1.txt','OWN_GROUPED_VISIBLE_FINAL_v1.txt','OWN_HOLDS_v1.json','build_own_source_freeze.py']
manifest={name:hashlib.sha256((BASE/name).read_bytes()).hexdigest() for name in files}
dump(BASE/'OWN_FREEZE_MANIFEST_v1.json',manifest)
(BASE/'OWN_SOURCE_SEAL_v1.md').write_text(
    '# Independent own source seal v1\n\n'
    'Original-pixel-only transcription frozen before primary source observer comparison.\n\n'
    f'Compact 180-letter UTF-8 string SHA-256 (no newline): `{record["compact_utf8_sha256"]}`.\n\n'
    'Six rows, six five-site blocks per row; final-layer letter holds: none. '
    'Five earlier violet-layer identities remain unresolved under readable dark final P/N/B/H/W. '
    'Four underline events and source-layout gaps are retained.\n\n'
    'File hashes are in `OWN_FREEZE_MANIFEST_v1.json`. Primary observer exposure: none at seal.\n',encoding='utf-8')
print(json.dumps({'letters':len(compact),'compact_sha256':record['compact_utf8_sha256'],'manifest':manifest},indent=2))
