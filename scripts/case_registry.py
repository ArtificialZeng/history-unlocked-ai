#!/usr/bin/env python3
"""Offline, conservative case registry. Evidence meanings are human-reviewed.

All registered IDs block NEW discovery. Shared resource/hash matches require
review; they do not prove that two ciphers are identical. Locks coordinate only
writers using this one current registry, never disconnected offline copies.
"""
import argparse
from contextlib import contextmanager
import datetime as dt
import hashlib
import ipaddress
import json
import ntpath
import os
from pathlib import Path
import re
import tempfile
import time
from urllib.parse import urlsplit, urlunsplit

FLAGS = {"attempted", "source_checked", "catalog_solved", "prior_reading", "reserved", "local_release"}
OUTCOMES = {"attempted": {"attempted"}, "source_checked": {"source_checked"},
            "source_hold": {"source_checked"}, "method_failed": {"attempted"},
            "deferred": {"attempted"}, "partial": {"attempted"},
            "catalog_solved": {"catalog_solved", "source_checked"},
            "prior_reading": {"prior_reading", "source_checked"},
            "local_release": {"local_release", "attempted"}}
HEX = re.compile(r"^[0-9a-fA-F]{64}$")
SECRET = re.compile(r"(?i)(?:authorization|bearer|password|secret|api[_-]?key|token)\s*[=: ]")
MAX_AGE = dt.timedelta(hours=24)


def utc(): return dt.datetime.now(dt.timezone.utc)
def stamp(): return utc().isoformat().replace("+00:00", "Z")
def sha(data): return hashlib.sha256(data).hexdigest()
def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""): h.update(block)
    return h.hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def require(value, message):
    if not value: raise ValueError(message)
def text(value, maximum=512):
    require(isinstance(value, str) and 0 < len(value.strip()) <= maximum and not any(ord(x)<32 for x in value), "invalid metadata string")
    return value.strip()
def date(value):
    value = text(value, 80)
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None and parsed.utcoffset() == dt.timedelta(0), "UTC timestamp required")
    return parsed
def public_url(value):
    value=text(value,2048);p=urlsplit(value)
    require(p.scheme in ("http", "https") and p.hostname and not p.username and not p.password, "public URL without credentials required")
    host=p.hostname.rstrip(".").lower()
    try:
        address=ipaddress.ip_address(host)
    except ValueError:
        require("." in host and host not in {"localhost", "local", "internal"}
                and not any(host.endswith(suffix) for suffix in
                            (".localhost", ".local", ".internal", ".localdomain")),
                "public host required; local/internal/single-label hosts rejected")
    else:
        require(address.is_global, "public host required; nonglobal literal IP rejected")
    return value


def history_locator(value):
    """A portable local pointer is provenance only, never fresh web evidence."""
    value=text(value,2048)
    if not value.startswith("local:"):return public_url(value)
    path=value[6:]
    require(bool(path) and not path.startswith(("/","~","\\")) and ":" not in path
            and ".." not in path.replace("\\","/").split("/")
            and not SECRET.search(path) and "?" not in path and "#" not in path,
            "local history pointer must be safe relative path without credentials/traversal")
    return value


def canonical(value):
    value=text(value)
    m=re.fullmatch(r"(?i)(?:hcportal:|HC[_ -]?)(\d+)",value)
    if m: return "hcportal:"+str(int(m[1]))
    p=urlsplit(value)
    if p.scheme in ("http","https") and p.hostname in {"api.hcportal.eu","crypto.hcportal.eu","hcportal.eu","www.hcportal.eu"}:
        m=re.fullmatch(r"/(?:api/cryptograms|dashboard/cryptograms|cryptograms)/(\d+)/?",p.path)
        if m: return "hcportal:"+str(int(m[1]))
    m=re.fullmatch(r"([a-z][a-z0-9_-]*):([A-Za-z0-9_.-]+)",value)
    if m:return m[1]+":"+m[2]
    return None


def alias(value):
    value=text(value)
    c=canonical(value)
    if c:return c
    p=urlsplit(value)
    if p.scheme in ("http","https"):
        return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip("/"),p.query,p.fragment))
    return value


def validate_record(record):
    require(isinstance(record,dict),"record object required")
    c=canonical(record.get("case_id"));require(c and ":" in c,"canonical case_id required")
    result={"case_id":c,"aliases":[],"flags":[],"disposition":"skip","source_fingerprints":[],"sources":[]}
    require(record.get("disposition")=="skip","known records must have skip disposition")
    require(isinstance(record.get("aliases"),list),"aliases list required")
    result["aliases"]=sorted(set(text(x) for x in record["aliases"]))
    require(isinstance(record.get("flags"),list) and set(record["flags"])<=FLAGS,"invalid flags")
    result["flags"]=sorted(set(record["flags"]))
    require(isinstance(record.get("source_fingerprints"),list),"fingerprints list required")
    for fp in record["source_fingerprints"]:
        require(isinstance(fp,dict),"fingerprint object required")
        require(fp.get("kind")=="sha256_file" and HEX.fullmatch(fp.get("sha256","")),"invalid file SHA256")
        require(re.fullmatch(r"[a-z][a-z0-9_]{0,79}",fp.get("scope","")),"fingerprint scope required")
        item={"kind":"sha256_file","sha256":fp["sha256"].lower(),"scope":fp["scope"]}
        if fp.get("url"):item["url"]=public_url(fp["url"])
        result["source_fingerprints"].append(item)
    require(isinstance(record.get("sources"),list),"sources list required")
    for source in record["sources"]:
        require(isinstance(source,dict),"source receipt object required")
        item={"url":history_locator(source["url"]),"evidence_type":text(source["evidence_type"],512)}
        if item["url"].startswith("local:"):item["locator_type"]="LOCAL_RELATIVE_POINTER_NOT_WEB_PROOF"
        # Historical provenance can lack an access time. Never manufacture one.
        # This does not relax gate()'s fresh primary/prior-review timestamps.
        if source.get("checked_utc") is not None:
            date(source["checked_utc"]);item["checked_utc"]=source["checked_utc"]
        result["sources"].append(item)
    if record.get("project_label"):
        label=text(record["project_label"],200)
        require(not label.startswith(("/","~","\\")) and not re.match(r"^[A-Za-z]:",label) and ".." not in label.replace("\\","/").split("/"),"project_label must be relative")
        result["project_label"]=label
    if record.get("local_status"):result["local_status"]=text(record["local_status"],160)
    for field in ("outcomes","reservation"):
        if field in record:result[field]=record[field]
    return result


def union(left,right):
    seen={json.dumps(x,sort_keys=True,ensure_ascii=False):x for x in left+right}
    return [seen[k] for k in sorted(seen)]
def combine(left,right):
    result=dict(left)
    for key in ("aliases","flags"):result[key]=sorted(set(left[key])|set(right[key]))
    for key in ("sources","source_fingerprints","outcomes"):result[key]=union(left.get(key,[]),right.get(key,[]))
    for key in ("project_label","local_status","reservation"):
        if key not in result and key in right:result[key]=right[key]
    result["disposition"]="skip"
    return result


def seed_records(path):
    value=read(path);require(value.get("schema_version")==1,"unsupported seed schema")
    date(value["generated_utc"]);require(isinstance(value.get("records"),list) and value["records"],"nonempty seed required; empty-registry discovery forbidden")
    records={}
    for r in value["records"]:
        item=validate_record(r);c=item["case_id"]
        records[c]=combine(records[c],item) if c in records else item
    return records


@contextmanager
def locked(state, timeout=5):
    state.mkdir(parents=True,exist_ok=True);path=state/".registry.lock";deadline=time.monotonic()+timeout
    while True:
        try:fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);break
        except FileExistsError:
            if time.monotonic()>=deadline:raise ValueError("registry locked; use one shared current registry/single writer; inspect stale lock manually")
            time.sleep(.05)
    try:
        with os.fdopen(fd,"w") as f:f.write(json.dumps({"pid":os.getpid(),"created_utc":stamp()}));f.flush();os.fsync(f.fileno())
        yield
    finally:path.unlink(missing_ok=True)


def load(state):
    path=state/"registry.json";require(path.exists(),"registry not initialized; bootstrap a nonempty known-case seed before discovery")
    value=read(path);require(value.get("schema_version")==1 and value.get("records"),"invalid or empty registry")
    records=[validate_record(r) for r in value["records"]]
    require(len(records)==len({r["case_id"] for r in records}),"duplicate stored case IDs")
    value["records"]=records
    return value


def save(state,value):
    path=state/"registry.json"
    if path.exists():
        old=path.read_bytes();folder=state/"snapshots";folder.mkdir(exist_ok=True);snapshot=folder/(sha(old)+".json")
        if not snapshot.exists():
            with snapshot.open("xb") as f:f.write(old);f.flush();os.fsync(f.fileno())
    value["updated_utc"]=stamp();data=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    fd,tmp=tempfile.mkstemp(prefix=".registry-",dir=state)
    try:
        with os.fdopen(fd,"wb") as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
        try:
            fd=os.open(state,os.O_RDONLY|getattr(os,"O_DIRECTORY",0));os.fsync(fd);os.close(fd)
        except OSError:pass
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def merge_seed(state,path):
    incoming=seed_records(path)
    with locked(state):
        value=load(state) if (state/"registry.json").exists() else {"schema_version":1,"records":[],"seed_imports":[]}
        records={r["case_id"]:r for r in value["records"]}
        for c,r in incoming.items():records[c]=combine(records[c],r) if c in records else r
        value["records"]=[records[c] for c in sorted(records)]
        value["seed_imports"]=union(value.get("seed_imports",[]),[{"sha256":file_sha(path)}]);save(state,value)
    return {"status":"MERGED","records":len(records),"seed_sha256":file_sha(path),"existing_attempt_flags_retained":True}


def check(value,case_id,aliases=(),hashes=()):
    c=canonical(case_id);require(c,"canonical candidate ID required")
    names={alias(x) for x in [case_id,*aliases]}
    identities={c}|{v for x in aliases if (v:=canonical(x)) and v.startswith("hcportal:")}
    hashes={h.lower() for h in hashes};require(all(HEX.fullmatch(h) for h in hashes),"invalid queried SHA256")
    identity_hits=set();resource_hits=set();hash_hits=set()
    for r in value["records"]:
        known_ids={r["case_id"]}|{v for x in r["aliases"] if (v:=canonical(x)) and v.startswith("hcportal:")}
        if identities & known_ids:identity_hits.add(r["case_id"])
        resources=r["aliases"]+[s["url"] for s in r["sources"]]+[f["url"] for f in r["source_fingerprints"] if f.get("url")]
        if names & {alias(x) for x in resources}:resource_hits.add(r["case_id"])
        if hashes & {x["sha256"] for x in r["source_fingerprints"]}:hash_hits.add(r["case_id"])
    if identity_hits:status="REJECT";reason="KNOWN_CASE_ID_OR_IDENTITY_ALIAS"
    elif resource_hits or hash_hits:status="REVIEW";reason="SHARED_RESOURCE_ALIAS_OR_FILE_HASH; same page/image need not mean same cipher"
    else:status="CLEAR";reason="No match in this current registry; no worldwide novelty proof"
    return {"status":status,"case_id":c,"reason":reason,"identity_matches":sorted(identity_hits),"resource_alias_matches":sorted(resource_hits),"source_hash_matches":sorted(hash_hits),"worldwide_novelty_proven":False}


def gate(evidence,case_id):
    c=canonical(case_id);require(evidence.get("schema_version")==1 and canonical(evidence.get("case_id"))==c,"gate case/schema mismatch")
    p=evidence["primary_status"];r=evidence["prior_review"]
    require(canonical(p["case_id"])==canonical(r["case_id"])==c,"case-bound evidence required")
    public_url(p["url"]);require(HEX.fullmatch(p.get("receipt_sha256","")),"primary receipt SHA256 required")
    if c.startswith("hcportal:"):require(canonical(p["url"])==c,"primary HC case URL required")
    require(r.get("bounded") is True and type(r.get("query_budget")) is int and r["query_budget"]>0,"bounded query budget required")
    terms=r["identity_terms"];require(isinstance(terms,list) and terms and all(text(t) for t in terms),"case-bound original identity terms required")
    queries=r["queries"];require(isinstance(queries,list) and 0<len(queries)<=r["query_budget"],"actual finite exact-item queries required")
    for q in queries:
        query=text(q["query"],2048);public_url(q["capture_url"]);require(HEX.fullmatch(q.get("capture_sha256","")),"query capture SHA256 required")
        require(any(t.casefold() in query.casefold() for t in terms),"query must use an explicit original filename/archive/item/ID identity term")
    sources=r["reviewed_sources"];require(isinstance(sources,list),"reviewed sources list required")
    uncertain=False;credible=False
    for item in sources:
        public_url(item["url"]);date(item["checked_utc"]);require(HEX.fullmatch(item.get("receipt_sha256","")),"reviewed-source receipt SHA256 required")
        require(canonical(item["case_id"])==c,"review source must be case-bound")
        match=item["identity_match"];finding=item["finding"]
        require(match in {"exact","uncertain","unrelated"} and finding in {"no_credible_prior_reading_found","credible_prior_reading","unknown","unrelated"},"invalid prior-review enum")
        credible |= match=="exact" and finding=="credible_prior_reading"
        uncertain |= match=="uncertain" or (match!="unrelated" and finding=="unknown")
    conclusion=r["conclusion"];require(conclusion in {"bounded_negative","credible_prior_reading","unknown"},"invalid prior conclusion")
    if credible or conclusion=="credible_prior_reading":return "REJECT","CREDIBLE_CASE_BOUND_PRIOR_READING"
    if p["status"]=="Solved":return "REJECT","CATALOGUE_SOLVED"
    now=utc();times=[date(p["checked_utc"]),date(r["checked_utc"])]+[date(x["checked_utc"]) for x in sources if x["identity_match"]!="unrelated"]
    if any(now-t>MAX_AGE or t-now>dt.timedelta(minutes=5) for t in times):return "HOLD","STALE_OR_FUTURE_PRIMARY_OR_PRIOR_REVIEW"
    if p["status"]!="Not solved" or conclusion!="bounded_negative" or uncertain:return "HOLD","UNKNOWN_STATUS_OR_PRIOR_IDENTITY"
    require(evidence.get("coordination",{}).get("shared_current_registry_or_single_writer") is True,"shared-current-registry/single-writer acknowledgement required")
    return "CLEAR","FRESH_PRIMARY_AND_BOUNDED_NEGATIVE_REVIEW; not worldwide proof"


def new_record(c,aliases,hashes):
    return {"case_id":c,"aliases":sorted(set(aliases)),"flags":[],"disposition":"skip","source_fingerprints":[{"kind":"sha256_file","sha256":h,"scope":"whole_source_image"} for h in sorted(set(hashes))],"sources":[]}
def reserve(state,case_id,aliases,hashes,evidence_path):
    evidence=read(evidence_path)
    with locked(state):
        value=load(state);checked=check(value,case_id,aliases,hashes)
        if checked["status"]!="CLEAR":return checked
        decision,reason=gate(evidence,checked["case_id"])
        if decision!="CLEAR":return {**checked,"status":decision,"reason":reason}
        # Validated case identity in evidence is mandatory input, even if the
        # caller omitted --alias. Shared publication/capture URLs are not IDs.
        evidence_aliases=aliases+[evidence["primary_status"]["url"]]+evidence["prior_review"]["identity_terms"]
        checked=check(value,checked["case_id"],evidence_aliases,hashes)
        if checked["status"]!="CLEAR":return checked
        record=new_record(checked["case_id"],evidence_aliases,hashes)
        record["flags"]=["reserved","source_checked"]
        record["reservation"]={"utc":stamp(),"evidence_sha256":file_sha(evidence_path),"coordination":"shared_current_registry_or_single_writer_acknowledged"}
        record["sources"]=[{"url":evidence["primary_status"]["url"],"checked_utc":evidence["primary_status"]["checked_utc"],"evidence_type":"fresh_primary_Not_solved"}]
        record["outcomes"]=[{"utc":stamp(),"outcome":"reserved"}];value["records"].append(record);value["records"].sort(key=lambda x:x["case_id"]);save(state,value)
        return {"status":"RESERVED","case_id":record["case_id"],"evidence_sha256":file_sha(evidence_path),"worldwide_novelty_proven":False}


def record_outcome(state,case_id,outcome,aliases=(),hashes=()):
    c=canonical(case_id);require(c and outcome in OUTCOMES,"valid outcome/case required")
    with locked(state):
        value=load(state);records={r["case_id"]:r for r in value["records"]};incoming=new_record(c,aliases,hashes)
        incoming["flags"]=sorted(OUTCOMES[outcome]);incoming["outcomes"]=[{"utc":stamp(),"outcome":outcome}];incoming["local_status"]=outcome
        records[c]=combine(records[c],incoming) if c in records else incoming
        records[c]["local_status"]=outcome;value["records"]=[records[x] for x in sorted(records)];save(state,value)
    return {"status":"RECORDED","case_id":c,"flags":records[c]["flags"],"outcome":outcome}


def portable_string(value):
    p=urlsplit(value)
    if p.scheme in ("http","https"):
        if not p.hostname:return None
        cleaned=urlunsplit((p.scheme,p.hostname+(":"+str(p.port) if p.port else ""),p.path,"",""))
        return None if SECRET.search(cleaned) or re.search(r"/(?:Users|home)/[^/]+/",cleaned) else cleaned
    if SECRET.search(value):return None
    if value.startswith(("/","~","\\")) or re.match(r"^[A-Za-z]:",value):return ntpath.basename(value.replace("\\","/")) or None
    if re.search(r"/(?:Users|home)/[^/]+/|[A-Za-z]:\\Users\\",value):return None
    return value
def portable_export(value):
    records=[]
    for raw in value["records"]:
        r=validate_record(raw)
        # Export the agreed seed fields only: no freeform runtime dictionaries.
        r={k:v for k,v in r.items() if k not in {"outcomes","reservation"}}
        r["aliases"]=sorted({x for a in r["aliases"] if (x:=portable_string(a))})
        r["sources"]=[{**s,"url":u,"evidence_type":t} for s in r["sources"] if (u:=portable_string(s["url"])) and (t:=portable_string(s["evidence_type"]))]
        for f in r["source_fingerprints"]:
            if "url" in f:f["url"]=portable_string(f["url"])
        if "local_status" in r:
            s=portable_string(r["local_status"])
            if s:r["local_status"]=s
            else:del r["local_status"]
        if "project_label" in r and not portable_string(r["project_label"]):del r["project_label"]
        records.append(r)
    return {"schema_version":1,"generated_utc":stamp(),"records":records,"limitations":["All registered IDs block new discovery; source hash/resource matches require review.","Offline copies do not coordinate. Use one shared current registry or a single writer.","Evidence receipts and human classifications are not a worldwide novelty proof."]}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--state-dir",type=Path,required=True);sub=p.add_subparsers(dest="command",required=True)
    for name in ("init","merge"):
        q=sub.add_parser(name);q.add_argument("--seed",type=Path,required=True)
    for name in ("check","reserve","record"):
        q=sub.add_parser(name);q.add_argument("--case-id",required=True);q.add_argument("--alias",action="append",default=[]);q.add_argument("--url",action="append",default=[]);q.add_argument("--sha256",action="append",default=[]);q.add_argument("--file",type=Path,action="append",default=[])
        if name=="reserve":q.add_argument("--evidence",type=Path,required=True)
        if name=="record":q.add_argument("--outcome",choices=sorted(OUTCOMES),required=True)
    q=sub.add_parser("export");q.add_argument("--output",type=Path,required=True);sub.add_parser("list")
    args=p.parse_args();state=args.state_dir.resolve()
    try:
        if args.command in ("init","merge"):
            if args.command=="merge":load(state)
            answer=merge_seed(state,args.seed)
        elif args.command=="export":
            answer=portable_export(load(state))
            with args.output.open("x",encoding="utf-8") as f:json.dump(answer,f,ensure_ascii=False,indent=2);f.write("\n")
            answer={"status":"EXPORTED","records":len(answer["records"]),"contains_raw_gate_queries":False}
        elif args.command=="list":
            value=load(state);answer={"status":"SUMMARY","records":len(value["records"]),"flag_counts":{flag:sum(flag in r["flags"] for r in value["records"]) for flag in sorted(FLAGS)},"case_ids":[r["case_id"] for r in value["records"]]}
        else:
            aliases=args.alias+args.url;hashes=args.sha256+[file_sha(f) for f in args.file]
            if args.command=="check":answer=check(load(state),args.case_id,aliases,hashes)
            elif args.command=="reserve":answer=reserve(state,args.case_id,aliases,hashes,args.evidence)
            else:answer=record_outcome(state,args.case_id,args.outcome,aliases,hashes)
        print(json.dumps(answer,ensure_ascii=False,sort_keys=True,indent=2))
        return 0 if answer["status"] in {"CLEAR","RESERVED","MERGED","RECORDED","EXPORTED","SUMMARY"} else 2
    except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as error:
        print(json.dumps({"status":"HOLD","reason":type(error).__name__+": "+str(error),"worldwide_novelty_proven":False}));return 2


if __name__=="__main__":raise SystemExit(main())
