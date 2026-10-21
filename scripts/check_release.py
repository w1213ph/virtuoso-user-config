#!/usr/bin/env python3
"""Check distributable files for common private data and unwanted artifacts."""
import argparse
import ipaddress
import json
from pathlib import Path
import re
import sys

PATTERNS = {
    "private key": r"-----BEGIN (?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----",
    "personal Unix home": r"/home/[A-Za-z0-9_.-]+",
    "personal Windows home": r"[A-Za-z]:[\\/]Users[\\/][^\s/\\]+",
    "SSH account/host": r"\b[A-Za-z0-9_.-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z0-9-]+\b",
    "credential assignment": r"(?i)(?:password|passwd|access_token|api_key)\s*[:=]\s*['\"][^'\"]+['\"]",
}
BLOCKED_SUFFIXES = {".oa", ".sdb", ".psf", ".pdf", ".png", ".jpg", ".jpeg", ".zip", ".gz", ".tar", ".pyc", ".log", ".scs", ".lib", ".pem", ".key"}
SKIP_DIRS = {".git", "__pycache__"}


def scan(root):
    findings, count = [], 0
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if path.is_symlink():
            findings.append([relative.as_posix(), "symlink"])
            continue
        if not path.is_file():
            continue
        count += 1
        if path.suffix.lower() in BLOCKED_SUFFIXES or path.name.startswith((".install", "id_")):
            findings.append([relative.as_posix(), "non-source or local artifact"])
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            findings.append([relative.as_posix(), "non-UTF-8 file"])
            continue
        for label, pattern in PATTERNS.items():
            if re.search(pattern, text):
                findings.append([relative.as_posix(), label])
        for candidate in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text):
            try:
                address = ipaddress.ip_address(candidate)
                if address.is_private or address.is_loopback or address.is_link_local:
                    findings.append([relative.as_posix(), "private/local IP"])
            except ValueError:
                pass
    return {"files_checked": count, "findings": findings, "passed": not findings}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    result = scan(Path(args.root))
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)
