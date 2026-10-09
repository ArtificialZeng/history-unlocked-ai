"""Read-only verification of the source-only freeze. No inference or writes."""
from pathlib import Path
import hashlib, json

OUT = Path(__file__).resolve().parent
BASE = OUT.parents[1]

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    manifest_path=OUT/"freeze_manifest_v1.json"
    expected=(OUT/"freeze_manifest_v1.sha256").read_text().split()[0]
    assert sha(manifest_path)==expected, "seal manifest changed"
    m=json.loads(manifest_path.read_text())
    for record in m["files"]:
        path=BASE/record["path"]
        assert path.resolve().is_relative_to(BASE.resolve()), "outside-scope path"
        assert path.stat().st_size==record["bytes"], record["path"]
        assert sha(path)==record["sha256"], record["path"]
    ledger=json.loads((OUT/"source_ledger_v1.json").read_text())
    rows=ledger["occurrences"]
    assert len(rows)==180
    assert [r["global_position"] for r in rows]==list(range(1,181))
    assert len({r["occurrence_id"] for r in rows})==180
    assert all(r["visible_identity_status"]=="fixed_from_pixels" for r in rows)
    assert all(len(r["visible_final_uppercase"])==1 and "A"<=r["visible_final_uppercase"]<="Z" for r in rows)
    held=[r["global_position"] for r in rows if r["typed_underlayer_identity"] is None]
    assert held==[23,66,80,132,172]
    final="".join(r["visible_final_uppercase"] for r in rows)
    typed="".join(r["typed_underlayer_identity"] or "?" for r in rows)
    assert (OUT/"visible_final_stream_v1.txt").read_text().strip()==final
    assert (OUT/"typed_underlayer_held_v1.txt").read_text().strip()==typed
    grouped=(OUT/"visible_final_grouped_v1.txt").read_text().splitlines()
    assert len(grouped)==6
    for line,text in enumerate(grouped,1):
        groups=text.split()
        assert len(groups)==6 and all(len(g)==5 for g in groups)
        for group,t in enumerate(groups,1):
            sites=[r for r in rows if r["line"]==line and r["group"]==group]
            assert len(sites)==5
            assert [r["position_in_group"] for r in sites]==[1,2,3,4,5]
            assert "".join(r["visible_final_uppercase"] for r in sites)==t
    other=json.loads((OUT/"noncipher_ledger_v1.json").read_text())["occurrences"]
    all_occ={r["occurrence_id"] for r in rows+other}
    events=json.loads((OUT/"marks_and_layer_events_v1.json").read_text())["events"]
    all_events={e["event_id"] for e in events}
    assert len(all_events)==18
    for e in events:
        links=e["cipher_occurrence_ids"]+e["noncipher_occurrence_ids"]
        assert links and all(o in all_occ for o in links), e["event_id"]
    for r in rows+other:
        assert all(e in all_events for e in r["event_ids"])
        x0,y0,x1,y1=r["bbox_original_xyxy"]
        assert 0<=x0<x1<=3024 and 0<=y0<y1<=4032
        for eid in r["event_ids"]:
            e=next(e for e in events if e["event_id"]==eid)
            assert r["occurrence_id"] in e["cipher_occurrence_ids"]+e["noncipher_occurrence_ids"]
    crop_manifest=json.loads((OUT/"crop_manifest_v1.json").read_text())
    assert crop_manifest["source_sha256"]==ledger["source_sha256"]
    crop_ids=set()
    for crop in crop_manifest["crops"]:
        crop_ids.add(crop["crop_id"])
        assert sha(BASE/crop["path"])==crop["sha256"]
        x0,y0,x1,y1=crop["bbox_original_xyxy"]
        factor=3 if crop["crop_id"].endswith("_nearest3x") else 1
        assert crop["output_size"]==[(x1-x0)*factor,(y1-y0)*factor]
    assert all(e["crop_id"] in crop_ids for e in events)
    print(json.dumps({"status":"PASS","read_only":True,"sites":180,"groups":36,"rows":6,
        "fixed_final_identities":180,"held_typed_positions":held,"linked_events":18,"crop_files":len(crop_ids),
        "manifest_sha256":expected},indent=2))

if __name__=="__main__": main()
