"""Emit the manual cold pixel reading; no OCR, cipher method, or language scoring.

The literal observations and coordinates were recorded from original/native crops.
Running this writes only this report directory. Use verify_source_freeze.py to
check the frozen artifacts without writing anything.
"""
from pathlib import Path
import csv, hashlib, json

BASE = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = "sources/raw/HC696_original.jpg"
SOURCE_HASH = "2dc894dd0aaa745eb5c7ba6155b653038cc6625817ef66ec0502125dd93f0ae4"

# Six independently counted rows, six observed groups per row, five sites each.
GROUPS = [
    ["CIUSW", "INBAX", "ERHPB", "WPXOQ", "YKPVA", "GUSRB"],
    ["KWXKJ", "UKILR", "WBCJW", "MTYLZ", "WUSUF", "CBKDA"],
    ["UGTKS", "NKJFS", "JLZGM", "MWZWB", "EKKMN", "LNAJT"],
    ["SQMZL", "JCIMS", "WIFNE", "NEQPN", "SWQRC", "CPNLM"],
    ["MQNSD", "MLWMK", "ZHKHL", "ENXJI", "VKPMW", "ASSHI"],
    ["NKDJR", "ZCWJT", "BFPNG", "BQZGP", "HWZYO", "EKNCL"],
]

# Manually observed horizontal occurrence centers. Cell bboxes are provenance
# windows, not segmented ink masks. Y ranges are complete native row crops.
CENTERS = [
    [[195,268,348,426,502],[658,736,811,888,970],[1130,1204,1283,1356,1436],[1598,1670,1750,1828,1903],[2054,2134,2217,2295,2366],[2530,2602,2688,2766,2849]],
    [[206,284,361,435,513],[668,747,822,899,978],[1135,1210,1290,1370,1446],[1596,1679,1751,1828,1908],[2071,2146,2260,2334,2412],[2557,2634,2708,2790,2920]],
    [[224,303,381,458,534],[688,768,841,920,995],[1157,1229,1306,1384,1459],[1603,1683,1757,1837,1910],[2069,2147,2261,2343,2418],[2565,2644,2723,2845,2925]],
    [[229,305,384,459,534],[699,771,848,924,1004],[1150,1232,1307,1383,1461],[1614,1683,1761,1837,1911],[2069,2148,2227,2304,2379],[2535,2610,2688,2764,2843]],
    [[238,316,395,473,550],[704,777,855,933,1008],[1157,1235,1313,1390,1466],[1615,1695,1769,1845,1925],[2074,2154,2230,2309,2386],[2532,2612,2689,2767,2845]],
    [[247,325,403,484,561],[719,797,873,949,1030],[1170,1248,1326,1407,1483],[1620,1696,1773,1850,1929],[2078,2155,2231,2309,2390],[2539,2616,2694,2770,2848]],
]
ROW_Y = [[680,875],[905,1110],[1135,1340],[1370,1560],[1590,1780],[1800,2000]]
OVERWRITES = {23: "E01", 66: "E02", 80: "E04", 132: "E05", 172: "E06"}
LINKS = {23:["E01"],66:["E02"],77:["E03"],80:["E04"],132:["E05"],172:["E06"],
         5:["E07"],6:["E07"],11:["E08"],12:["E08"],101:["E09"],102:["E09"],107:["E10"],108:["E10"],
         1:["E11"],153:["E12"],150:["E18"]}

def dump(path, obj):
    (OUT/path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")

def occ(n): return f"C{n:03d}"

def main():
    assert hashlib.sha256((BASE/SOURCE).read_bytes()).hexdigest()==SOURCE_HASH
    rows=[]
    group_rows=[]
    n=0
    for line,(groups,centers,ys) in enumerate(zip(GROUPS,CENTERS,ROW_Y),1):
        assert len(groups)==6
        for group,(text,xs) in enumerate(zip(groups,centers),1):
            assert len(text)==len(xs)==5
            start=n+1
            for position,(char,x) in enumerate(zip(text,xs),1):
                n+=1
                is_overlay=n in OVERWRITES
                rows.append({"occurrence_id":occ(n),"global_position":n,"line":line,"group":group,
                    "position_in_group":position,"position_in_line":(group-1)*5+position,
                    "visible_final_uppercase":char,"visible_identity_status":"fixed_from_pixels",
                    "visible_layer":"thick_dark_overlay" if is_overlay else "violet_typewritten",
                    "typed_underlayer_identity":None if is_overlay else char,
                    "typed_underlayer_status":"held_unidentified_occluded" if is_overlay else "legible",
                    "source_supported_alternative_letters":[],
                    "alternative_note":"No underlying alphabetic candidate is asserted: incomplete/occluded residue does not identify a letter." if is_overlay else None,
                    "event_ids":LINKS.get(n,[]),"source":SOURCE,"source_sha256":SOURCE_HASH,
                    "bbox_original_xyxy":[x-38,ys[0],x+38,ys[1]],
                    "bbox_kind":"manual occurrence-centered cell window; includes entire row height; not a tight ink segmentation",
                    "native_crop_id":f"line_{line:02d}",
                    "pixel_evidence":"Dominant final uppercase outline directly legible in the original and native row crop; no linguistic inference."})
            group_rows.append({"line":line,"group":group,"first_position":start,"last_position":n,"site_count":5,
                "visible_final":text,"occurrence_ids":[occ(i) for i in range(start,n+1)],
                "bbox_original_xyxy":[min(xs)-38,ys[0],max(xs)+38,ys[1]],
                "layout_note":"Additional internal spacing is visible; retained by individual x coordinates." if (line==2 and group in (5,6)) or (line==3 and group in (5,6)) else None})
    assert n==180
    ledger={"schema":"HC696_source_ledger_v1","target":"HC696","layer_policy":"Visible final uppercase layer is fixed. Five dark overlays occupy existing sites; the occluded violet typed underlayer is held unidentified at those sites.",
        "source":SOURCE,"source_sha256":SOURCE_HASH,"original_size":[3024,4032],
        "bbox_convention":"zero-based original image pixels [left,top,right,bottom)",
        "counts":{"rows":6,"groups":36,"sites":180,"groups_per_row":[6]*6,"sites_per_group":[5]*36,
                  "fixed_visible_final_identities":180,"held_typed_underlayer_identities":5},
        "occurrences":rows,"groups":group_rows}
    dump("source_ledger_v1.json",ledger)
    with (OUT/"letter_position_ledger_v1.tsv").open("w",newline="") as f:
        fields=["occurrence_id","global_position","line","group","position_in_group","visible_final_uppercase","visible_layer","typed_underlayer_identity","typed_underlayer_status","event_ids","bbox_original_xyxy","source","source_sha256"]
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t")
        w.writeheader()
        for row in rows:
            r={k:row[k] for k in fields}
            r["event_ids"]=";".join(r["event_ids"])
            r["bbox_original_xyxy"]=json.dumps(r["bbox_original_xyxy"])
            w.writerow(r)
    visible_lines=[" ".join(g) for g in GROUPS]
    (OUT/"visible_final_grouped_v1.txt").write_text("\n".join(visible_lines)+"\n")
    (OUT/"visible_final_stream_v1.txt").write_text("".join("".join(g) for g in GROUPS)+"\n")
    typed="".join(r["typed_underlayer_identity"] or "?" for r in rows)
    (OUT/"typed_underlayer_held_v1.txt").write_text(typed+"\n")

    events=[
        ("E01","dark_uppercase_overlay",[23],"E01_P_overwrite","Final P has one upper bowl and a descending left stem; black/dark strokes occlude the earlier violet site. It may be correction or reinforcement; chronology/earlier identity is not recoverable.",[]),
        ("E02","dark_uppercase_overlay",[66],"E02_N_overwrite","Final N has two upright strokes connected by a descending diagonal; earlier typed identity is occluded and held.",[]),
        ("E03","ambiguous_crossing_or_print_irregularity",[77],"E03_W_crossing","Violet W remains readable. A small darker diagonal/top crossing may be extraneous pencil, ink irregularity, or part of the printed impression; no second alphabetic identity is supported.",[]),
        ("E04","dark_uppercase_overlay",[80],"E04_B_overwrite","Final B has a left stem and two right bowls. Violet fragments remain within/beside it but do not uniquely identify the earlier typed letter.",[]),
        ("E05","dark_uppercase_overlay",[132],"E05_H_overwrite","Final H has two upright strokes and one crossbar. Violet residue is insufficient to recover the earlier typed identity.",[]),
        ("E06","dark_uppercase_overlay",[172],"E06_W_overwrite","Final W has two lower vertices and three upper endpoints. Earlier typed identity remains occluded and held.",[]),
        ("E07","dark_underline",[5,6],"E07_line1_W_I_underline","One rising dark underline spans W at the end of group 1, the intergroup blank, and I at the start of group 2; both visible identities stay fixed.",[]),
        ("E08","dark_underline",[11,12],"E08_line1_E_R_underline","Dark underline below E and R, with short downward excess at the E side; no letter replacement.",[]),
        ("E09","dark_underline",[101,102],"E09_line4_W_I_underline","Broad multi-stroke dark underline beneath W and I; overlaps their lower vicinity without obscuring identity.",[]),
        ("E10","dark_underline",[107,108],"E10_line4_E_Q_underline","Dark underline beneath E and Q; Q tail remains visible. Underline is not a letter.",[]),
        ("E11","red_margin_stroke",[1],"E11_left_red_stroke","Red rising stroke near left margin, plus a faint branch toward the edge; only spatially adjacent to C001. No semantic link or replacement asserted.",["S002"]),
        ("E12","blue_vertical_margin_stroke",[153],"E12_below_cipher_blue_stroke","Isolated narrow blue vertical stroke below the cipher, spatially below C153's column. No semantic connection or extra cipher site asserted.",["S003"]),
        ("E13","noncipher_header_text",[],"E13_header_text","Ordinary mixed-case typewritten header, visually transcribed as Anglický text čís. 7. Diacritic styling is less clear than the cipher; see header record.",[f"H{i:03d}" for i in range(1,18)]),
        ("E14","violet_dashed_header_rule",[],"E14_header_dashed_rule","Series of small violet horizontal impressions below the heading. A rule, not cipher letters; exact dash count is not used.",["R001"]),
        ("E15","red_heading_stroke",[],"E15_header_red_stroke","Long red stroke rises from left below the heading and crosses the right-hand heading/7 region. It is separate from violet text and dashed rule.",[f"H{i:03d}" for i in range(1,18)]+["S001","R001"]),
        ("E16","magenta_header_digit",[],"E16_header_magenta_4","Large handwritten magenta 4 near upper right; separate from cipher and typewritten heading.",["M001"]),
        ("E17","dark_check_like_mark",[],"E17_header_check_mark","Dark check/V-like two-segment handwritten mark to the right of the heading; identity recorded as shape, not a cipher V.",["M002"]),
        ("E18","terminal_I_ink_extension",[150],"E18_line5_terminal_I_ink","Visible I has extra violet ink extending below/beside its lower serif. I remains directly legible; no extra character site.",[]),
    ]
    manifest=json.loads((OUT/"crop_manifest_v1.json").read_text())
    crop_index={c["crop_id"]:c for c in manifest["crops"]}
    event_rows=[]
    for eid,kind,positions,crop,note,other in events:
        event_rows.append({"event_id":eid,"kind":kind,"cipher_occurrence_ids":[occ(i) for i in positions],
            "noncipher_occurrence_ids":other,"crop_id":crop,"bbox_original_xyxy":crop_index[crop]["bbox_original_xyxy"],
            "observation":note,"earlier_letter_candidates":[],"role_or_temporal_order_status":"not_inferred",
            "source":SOURCE,"source_sha256":SOURCE_HASH})
    dump("marks_and_layer_events_v1.json",{"events":event_rows,"policy":"Events refer to occurrences or explicit noncipher marks. Spatial links for E11/E12 do not imply semantic relations. Incidental paper fibers and stains are not inventoried as deliberate annotation."})
    header=list("Anglickýtextčís.7")
    hx=[160,201,242,282,321,363,403,444,530,573,615,655,730,772,814,856,922]
    noncipher=[]
    for i,(char,x) in enumerate(zip(header,hx),1):
        noncipher.append({"occurrence_id":f"H{i:03d}","visible_value":char,"bbox_original_xyxy":[x-24,440,x+24,560],
            "event_ids":["E13","E15"],"identity_status":"base character fixed; diacritic spelling tentative" if i in (8,13,14) else "legible",
            "source":SOURCE,"source_sha256":SOURCE_HASH})
    for oid,value,box,eids in [
        ("R001","violet dashed rule",[120,553,960,610],["E14","E15"]),
        ("S001","red rising heading stroke",[75,395,1240,610],["E15"]),
        ("M001","4",[2490,95,2710,360],["E16"]),
        ("M002","check/V-like shape",[2120,470,2250,600],["E17"]),
        ("S002","red left-margin stroke",[0,710,110,910],["E11"]),
        ("S003","narrow blue vertical stroke",[350,2000,460,2240],["E12"]),
    ]:
        noncipher.append({"occurrence_id":oid,"visible_value":value,"bbox_original_xyxy":box,"event_ids":eids,
                          "identity_status":"shape observation; function not inferred","source":SOURCE,"source_sha256":SOURCE_HASH})
    dump("noncipher_ledger_v1.json",{"header_diplomatic":"Anglický text čís. 7","header_caution":"Mixed-case base characters and numeral are readable. The y/c/i diacritic spellings above are tentative shape transcription, not linguistic evidence; no header word is used as a crib.","occurrences":noncipher})

if __name__=="__main__": main()
