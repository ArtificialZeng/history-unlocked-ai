"""Verify this code derivative and replay seven existing cipher cases offline."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from check_public_boundary import check

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = {
    "hc615": [["scripts/verify_solution.py"]],
    "hc696": [["scripts/verify_solution_v1.py"], ["scripts/test_release_integrity_v1.py"]],
    "hc849": [["scripts/check_hc849_release_v1.py", "--integrity-tests"]],
    "hc851": [["scripts/check_hc851_v1.py", "--integrity-tests"]],
    "hc852": [["scripts/check_hc852_release_v1.py", "--integrity-tests"]],
    "hc1615": [["verify.py", "--root", ".", "--donor-key",
                "data/key/DONOR_FIXED_OBSERVED_KEY_v2.json", "--tamper"]],
    "hc1619": [["checker.py", "--output-dir", "{fresh_output}"]],
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_files():
    manifest = json.loads((ROOT / "CODE_CORE_MANIFEST.json").read_text())
    expected = set()
    for row in manifest["files"]:
        path = (ROOT / row["path"]).resolve()
        path.relative_to(ROOT.resolve())
        if not path.is_file():
            raise ValueError("Missing file: " + row["path"])
        raw = path.read_bytes()
        if len(raw) != row["bytes"] or sha(raw) != row["sha256"]:
            raise ValueError("Payload changed: " + row["path"])
        if row["path"] in expected:
            raise ValueError("Duplicate manifest entry")
        expected.add(row["path"])
    actual = {str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file()
              and ".git" not in p.relative_to(ROOT).parts
              and "__pycache__" not in p.relative_to(ROOT).parts and p.suffix != ".pyc"}
    if actual != expected | {"CODE_CORE_MANIFEST.json"}:
        raise ValueError("Unlisted or absent payload: " + str(sorted(actual ^ (expected | {"CODE_CORE_MANIFEST.json"}))))
    frozen = json.loads((ROOT / "docs/CORE_PROVENANCE.json").read_text())
    for row in frozen["files"]:
        raw = (ROOT / row["path"]).read_bytes()
        if len(raw) != row["bytes"] or sha(raw) != row["sha256"]:
            raise ValueError("Original scientific payload modified: " + row["path"])
    return {"payload_files_verified": len(expected),
            "unchanged_scientific_payloads_verified": len(frozen["files"])}


def replay():
    rows = []
    with tempfile.TemporaryDirectory(prefix="history_unlocked_replay_") as temp:
        for case, commands in COMMANDS.items():
            for command in commands:
                argv = [str(Path(temp) / "hc1619_output") if a == "{fresh_output}" else a
                        for a in command]
                result = subprocess.run([sys.executable, "-B"] + argv, cwd=ROOT / "cases" / case,
                                        capture_output=True, text=True, timeout=180)
                if result.returncode:
                    raise RuntimeError(case + ": " + " ".join(command) + "\n" + result.stdout + result.stderr)
                rows.append({"case": case, "command": command, "exit_code": 0,
                             "stdout_sha256": sha(result.stdout.encode()),
                             "stderr_sha256": sha(result.stderr.encode())})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", action="store_true", help="Run the eight case verification commands")
    args = parser.parse_args()
    result = {"status": "PASS", "boundary": check(), **verify_files(),
              "frozen_replays": replay() if args.replay else [],
              "new_cipher_attacks": 0, "mailbox_access": False,
              "network_calls_required": False}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
