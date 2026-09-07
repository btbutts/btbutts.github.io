#!/usr/bin/env python3
# scripts/subnet_check.py
"""Script to filter aws global subnets and write to txt files"""

import json
from pathlib import Path

# Define the regions used by LG Electronics
LG_REGIONS = {"ap-northeast-2", "us-east-1", "eu-central-1", "eu-west-1"}

# Services to exclude from the AWS IP range filtering (likely not used by LG)
EXCLUDED_SERVICES = {
    "AMAZON_APPFLOW",
    "AMAZON_CONNECT",
    "AURORA_DSQL",
    "CHIME_MEETINGS",
    "CHIME_VOICECONNECTOR",
    "CLOUD9",
    "CODEBUILD",
    "EBS",
    "EC2_INSTANCE_CONNECT",
    "EFS",
    "IVS_LOW_LATENCY",
    "IVS_REALTIME",
    "KINESIS_VIDEO_STREAMS",
    "MEDIA_PACKAGE_V2",
    "ROUTE53_HEALTHCHECKS",
    "ROUTE53_HEALTHCHECKS_PUBLISHING",
    "ROUTE53_RESOLVER",
    "WORKSPACES_GATEWAYS",
}

# Target AWS IP Range endpoint
SCRIPT_DIR = Path(__file__).resolve().parent
AWS_SUBNET_PATH = (
    SCRIPT_DIR.parent
    / "resources"
    / "aws_subnets"
    / "global_aws_subnets.json"
)

OUTPUT_DIR = SCRIPT_DIR.parent / "resources" / "aws_subnets" / "lg"
OUTPUT_FILE_PATH = OUTPUT_DIR / "lg_aws_subnets.json"

def filter_local_aws_ips():
    """Fetch AWS IP ranges and filter for LG Electronics regions.

    Returns:
        dict: A dictionary containing filtered IPv4 and IPv6 prefixes.
              Keys are "ipv4" and "ipv6".
        None: If an error occurs during fetching or parsing.
    """

    if not AWS_SUBNET_PATH.exists():
        print(f"[-] Error: Source file not found at {AWS_SUBNET_PATH}")
        return None

    try:
        # Fetch the JSON data from AWS
        print(f"[+] Reading local AWS subnets from: {AWS_SUBNET_PATH}")
        with open(AWS_SUBNET_PATH, "r", encoding="utf-8") as json_in:
            data = json.load(json_in)

        # Filter lists using exact original schemas
        filtered_prefixes = [
            prefix for prefix in data.get("prefixes", [])
            if prefix.get("region") in LG_REGIONS
            and prefix.get("service") not in EXCLUDED_SERVICES
        ]

        filtered_ipv6_prefixes = [
            ipv6_prefix for ipv6_prefix in data.get("ipv6_prefixes", [])
            if ipv6_prefix.get("region") in LG_REGIONS
            and ipv6_prefix.get("service") not in EXCLUDED_SERVICES
        ]

        # Reconstruct exactly matching the original JSON structural layout
        lg_schema_output = {
            "syncToken": data.get("syncToken"),
            "createDate": data.get("createDate"),
            "prefixes": filtered_prefixes,
            "ipv6_prefixes": filtered_ipv6_prefixes
        }

        print("[+] Filtering Complete.")
        print(f"    Filtered IPv4 prefixes: {len(filtered_prefixes)}")
        print(f"    Filtered IPv6 prefixes: {len(filtered_ipv6_prefixes)}")

        return lg_schema_output

    except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"[-] Error processing or parsing AWS IP JSON: {e}")
        return None


if __name__ == "__main__":
    lg_aws_ips = filter_local_aws_ips()

    if lg_aws_ips:
        # Print combined payload to console as requested
        print(json.dumps(lg_aws_ips, indent=2))

        # Ensure destination path directory exists for local/CI workflow
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Write out exact schema to the local repository directory tree
        try:
            with open(OUTPUT_FILE_PATH, "w", encoding="utf-8") as out_f:
                json.dump(lg_aws_ips, out_f, indent=2)
            print(f"\n[+] Successfully saved output to: {OUTPUT_FILE_PATH}")
        except (OSError, TypeError, ValueError) as write_error:
            print(f"[-] Failed to write JSON output to file: {write_error}")
