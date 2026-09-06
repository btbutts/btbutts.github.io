import hashlib
import sys
from pathlib import Path
import urllib.request

REMOTE_URL = "https://ip-ranges.amazonaws.com/ip-ranges.json"
TARGET_PATH = Path("resources/aws_subnets/global_aws_subnets.json")

def get_file_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main():
    # 1. Fetch remote content
    print("Downloading latest AWS IP ranges...")
    req = urllib.request.Request(REMOTE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        remote_data = response.read()

    remote_hash = get_file_sha256(remote_data)
    print(f"Remote SHA256: {remote_hash}")

    # 2. Read local file hash
    local_hash = None
    if TARGET_PATH.is_file():
        local_data = TARGET_PATH.read_bytes()
        local_hash = get_file_sha256(local_data)
    print(f"Local SHA256:  {local_hash}")

    # 3. Compare and overwrite
    if remote_hash == local_hash:
        print("Hashes match. Nothing to do.")
        sys.exit(0)

    print(f"Hashes differ. Overwriting {TARGET_PATH}...")
    TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
    TARGET_PATH.write_bytes(remote_data)
    print("File updated successfully.")

if __name__ == "__main__":
    main()

