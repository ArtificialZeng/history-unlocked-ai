"""Check the code repository's file boundary without reading any mailbox."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PARTS = {
    "press", "editorial", "publication", "manuscript", "private_qa",
    "email", "emails", "correspondence", "outreach", "private",
}
FORBIDDEN_SUFFIXES = {
    ".pdf", ".docx", ".doc", ".eml", ".msg", ".zip", ".7z", ".tar",
    ".gz", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ttf",
}
PRIVATE_MARKERS = [
    r"(?im)^\s*(?:USER:|ASSISTANT:|用户[：:]|助手[：:])",
    r"<send_user_message|<in-app-browser",
    r"(?im)^(?:From:|To:|Subject:|收件人[：:]|发件人[：:])",
    r"(?im)^Dear\s+(?:Dr[.]?|Professor)\s+",
    r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}",
]


def check(root=ROOT):
    bad = []
    scanned = 0
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if ".git" in rel.parts or "__pycache__" in rel.parts:
            continue
        if path.is_symlink():
            bad.append({"path": str(rel), "reason": "symlink"})
            continue
        if not path.is_file():
            continue
        scanned += 1
        if (any(p.lower() in FORBIDDEN_PARTS or p.lower().startswith("private_")
                for p in rel.parts) or path.suffix.lower() in FORBIDDEN_SUFFIXES):
            bad.append({"path": str(rel), "reason": "outside code/data/documentation scope"})
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # Frozen scoring caches are separately pinned by SHA-256.
        # The checker necessarily defines its own patterns. Do not scan its source
        # as correspondence; integrity verification pins this utility separately.
        if rel == Path("scripts/check_public_boundary.py"):
            continue
        if any(re.search(pattern, content, re.I) for pattern in PRIVATE_MARKERS):
            bad.append({"path": str(rel), "reason": "private correspondence/conversation or credential marker"})
    if bad:
        raise ValueError(json.dumps({"status": "FAIL", "findings": bad}, indent=2))
    return {"status": "PASS", "files_scanned": scanned,
            "news_submission_files": 0, "private_correspondence_markers": 0,
            "archive_containers": 0,
            "scope": "File/content checks for this code repository; not a guarantee about external copies."}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
