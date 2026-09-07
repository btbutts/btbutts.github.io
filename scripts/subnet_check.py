#!/usr/bin/env python3
# scripts/subnet_check.py
"""Script to validate aws global subnets for changes and modify if needed"""

import hashlib
import sys
import urllib.request
from pathlib import Path

AWS_SUBNET_URL = "https://ip-ranges.amazonaws.com/ip-ranges.json"
SCRIPT_DIR = Path(__file__).resolve().parent
AWS_SUBNET_PATH = (
    SCRIPT_DIR.parent
    / "resources"
    / "aws_subnets"
    / "global_aws_subnets.json"
)

def get_file_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main():
    # 1. Fetch remote content
    print("Retrieving latest AWS IP ranges...")
    req = urllib.request.Request(AWS_SUBNET_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        remote_data = response.read()

    remote_hash = get_file_sha256(remote_data)
    print(f"Latest subnet json SHA256: {remote_hash}")

    # 2. Read local file hash
    local_hash = None
    if AWS_SUBNET_PATH.is_file():
        local_data = AWS_SUBNET_PATH.read_bytes()
        local_hash = get_file_sha256(local_data)
    print(f"Local subnet json SHA256:  {local_hash}")

    # 3. Compare and overwrite
    if remote_hash == local_hash:
        print("Hashes match. Nothing to do.")
        sys.exit(0)

    print(f"Hashes differ. Overwriting {AWS_SUBNET_PATH}...")
    AWS_SUBNET_PATH.parent.mkdir(parents=True, exist_ok=True)
    AWS_SUBNET_PATH.write_bytes(remote_data)
    print("File updated successfully.")

if __name__ == "__main__":
    main()

