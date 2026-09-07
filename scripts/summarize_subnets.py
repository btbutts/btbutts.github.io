#!/usr/bin/env python3
# scripts/subnet_check.py
"""Compact CIDRs to minimal form and output to a text file one CIDR per line"""

import ipaddress
import json
import sys
from pathlib import Path


def generate_output_paths(supplied_path: Path) -> tuple[Path, Path]:
    """Appends '_ipv4' and '_ipv6' to the file name stem of a given Path."""
    # .stem yields 'aws_subnets' from 'aws_subnets.txt'
    ipv4_path = supplied_path.with_stem(f"{supplied_path.stem}_ipv4")
    ipv6_path = supplied_path.with_stem(f"{supplied_path.stem}_ipv6")
    return ipv4_path, ipv6_path

def summarize_cidrs(input_path: Path, ipv4_output_path: Path, ipv6_output_path: Path) -> None:
    """Summarize CIDRs into collapsed IPv4 and IPv6 lists"""
    ipv4_cidrs = []
    ipv6_cidrs = []

    # Load and parse the AWS IP ranges JSON
    with open(input_path, mode='r', encoding="utf-8") as json_file:
        subnet_data = json.load(json_file)

    # Extract IPv4 CIDRs
    for entry in subnet_data.get("prefixes", []):
        ipv4_cidr_string = entry.get("ip_prefix")
        if ipv4_cidr_string:
            try:
                ipv4_cidrs.append(ipaddress.ip_network(ipv4_cidr_string))
            except ValueError as error:
                print(f"Skipping invalid IPv4 CIDR: {ipv4_cidr_string} ({error})", file=sys.stderr)

    # Extract IPv6 CIDRs
    for entry in subnet_data.get("ipv6_prefixes", []):
        ipv6_cidr_string = entry.get("ipv6_prefix")
        if ipv6_cidr_string:
            try:
                ipv6_cidrs.append(ipaddress.ip_network(ipv6_cidr_string))
            except ValueError as error:
                print(f"Skipping invalid IPv6 CIDR: {ipv6_cidr_string} ({error})", file=sys.stderr)

    # Collapse networks independently
    # (collapse_addresses cannot mix v4 and v6)
    collapsed_ipv4 = list(ipaddress.collapse_addresses(ipv4_cidrs))
    collapsed_ipv6 = list(ipaddress.collapse_addresses(ipv6_cidrs))

    # Output summarized IPv4 & IPv6 CIDRs
    with open(ipv4_output_path, mode="w", encoding="utf-8") as ipv4_file:
        ipv4_file.writelines(f"{network}\n" for network in collapsed_ipv4)
    with open(ipv6_output_path, mode="w", encoding="utf-8") as ipv6_file:
        ipv6_file.writelines(f"{network}\n" for network in collapsed_ipv6)

    # Summarization Analysis
    total_cidr_count = len(ipv4_cidrs) + len(ipv6_cidrs)
    total_collapsed_cidrs = len(collapsed_ipv4) + len(collapsed_ipv6)
    reduction_percentage = ((total_cidr_count - total_collapsed_cidrs) / total_cidr_count) * 100

    print(f"Original entries:   {total_cidr_count:,}")
    print(f"Summarized entries: {total_collapsed_cidrs:,}")
    print(f"Reduction:          {reduction_percentage:.1f}%")
    print(f"Saved IPv4 CIDRs to:      {ipv4_output_path}")
    print(f"Saved IPv6 CIDRs to:      {ipv6_output_path}")

if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    # Default paths if arguments are not supplied via CLI
    default_input_path = (
        repo_root
        / "resources"
        / "aws_subnets"
        / "global_aws_subnets.json"
    )
    default_output_path = repo_root / "aws_subnets.txt"

    target_input = Path(sys.argv[1]) if len(sys.argv) > 1 else default_input_path
    target_output_base = Path(sys.argv[2]) if len(sys.argv) > 2 else default_output_path

    # Dynamically generate independent output paths for IPv4 and IPv6
    target_ipv4_output, target_ipv6_output = generate_output_paths(target_output_base)

    summarize_cidrs(target_input, target_ipv4_output, target_ipv6_output)
