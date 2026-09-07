#!/usr/bin/env python3
# scripts/subnet_check.py
"""Compact CIDRs to minimal form and output to a text file one CIDR per line"""

import ipaddress
import json
import sys
from pathlib import Path

MAX_LINES_PER_SEGMENT = 999

def generate_output_paths(supplied_path: Path) -> tuple[Path, Path]:
    """Appends '_ipv4' and '_ipv6' to the file name stem of a given Path."""
    # .stem yields 'aws_subnets' from 'aws_subnets.txt'
    ipv4_path = supplied_path.with_stem(f"{supplied_path.stem}_ipv4")
    ipv6_path = supplied_path.with_stem(f"{supplied_path.stem}_ipv6")
    return ipv4_path, ipv6_path

def remove_stale_segments(segment_dir: Path, output_path: Path) -> None:
    """Delete leftover <stem>_segmentN.txt files from a previous larger run."""
    stale_pattern = f"{output_path.stem}_segment*{output_path.suffix}"
    for stale_file in segment_dir.glob(stale_pattern):
        stale_file.unlink()

def write_segmented_files(
    networks: list,
    output_path: Path,
    segment_dir: Path,
) -> list[Path]:
    """Write networks into segment files of at most MAX_LINES_PER_SEGMENT lines.

    Filenames follow <output_stem>_segmentN<suffix>, e.g.
    aws_subnets_ipv4_segment1.txt
    """
    segment_dir.mkdir(parents=True, exist_ok=True)
    remove_stale_segments(segment_dir, output_path)

    written_paths: list[Path] = []
    if not networks:
        return written_paths

    total_networks = len(networks)
    for start_index in range(0, total_networks, MAX_LINES_PER_SEGMENT):
        chunk = networks[start_index:start_index + MAX_LINES_PER_SEGMENT]
        segment_number = (start_index // MAX_LINES_PER_SEGMENT) + 1
        segment_path = segment_dir / (
            f"{output_path.stem}_segment{segment_number}{output_path.suffix}"
        )
        with open(segment_path, mode="w", encoding="utf-8") as segment_file:
            segment_file.writelines(f"{network}\n" for network in chunk)
        written_paths.append(segment_path)

    return written_paths

def summarize_cidrs(
    input_path: Path,
    ipv4_output_path: Path,
    ipv6_output_path: Path,
    segment_dir: Path,
) -> None:
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
                print(
                    f"Skipping invalid IPv4 CIDR: {ipv4_cidr_string} ({error})",
                    file=sys.stderr
                )

    # Extract IPv6 CIDRs
    for entry in subnet_data.get("ipv6_prefixes", []):
        ipv6_cidr_string = entry.get("ipv6_prefix")
        if ipv6_cidr_string:
            try:
                ipv6_cidrs.append(ipaddress.ip_network(ipv6_cidr_string))
            except ValueError as error:
                print(
                    f"Skipping invalid IPv6 CIDR: {ipv6_cidr_string} ({error})",
                    file=sys.stderr
                )

    # Collapse networks independently
    # (collapse_addresses cannot mix v4 and v6)
    collapsed_ipv4 = list(ipaddress.collapse_addresses(ipv4_cidrs))
    collapsed_ipv6 = list(ipaddress.collapse_addresses(ipv6_cidrs))

    # Output summarized IPv4 & IPv6 CIDRs
    with open(ipv4_output_path, mode="w", encoding="utf-8") as ipv4_file:
        ipv4_file.writelines(f"{network}\n" for network in collapsed_ipv4)
    with open(ipv6_output_path, mode="w", encoding="utf-8") as ipv6_file:
        ipv6_file.writelines(f"{network}\n" for network in collapsed_ipv6)

    # Segmented copies for devices that cap imports at 1000 lines
    ipv4_segment_paths = write_segmented_files(
        collapsed_ipv4, ipv4_output_path, segment_dir
    )
    ipv6_segment_paths = write_segmented_files(
        collapsed_ipv6, ipv6_output_path, segment_dir
    )

    # Summarization Analysis
    total_cidr_count = len(ipv4_cidrs) + len(ipv6_cidrs)
    total_collapsed_cidrs = len(collapsed_ipv4) + len(collapsed_ipv6)
    if total_cidr_count:
        reduction_percentage = (
            (total_cidr_count - total_collapsed_cidrs) / total_cidr_count
        ) * 100
    else:
        reduction_percentage = 0.0

    print(f"Original entries:   {total_cidr_count:,}")
    print(f"Summarized entries: {total_collapsed_cidrs:,}")
    print(f"Reduction:          {reduction_percentage:.1f}%")
    print(f"Saved IPv4 CIDRs to:      {ipv4_output_path}")
    print(f"Saved IPv6 CIDRs to:      {ipv6_output_path}")
    print(f"IPv4 segments ({len(collapsed_ipv4):,} lines, max {MAX_LINES_PER_SEGMENT}/file):")
    for segment_path in ipv4_segment_paths:
        print(f"  {segment_path}")
    print(f"IPv6 segments ({len(collapsed_ipv6):,} lines, max {MAX_LINES_PER_SEGMENT}/file):")
    for segment_path in ipv6_segment_paths:
        print(f"  {segment_path}")

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
    default_segment_dir = repo_root / "resources" / "aws_subnets"

    target_input = Path(sys.argv[1]) if len(sys.argv) > 1 else default_input_path
    target_output_base = Path(sys.argv[2]) if len(sys.argv) > 2 else default_output_path

    # Dynamically generate independent output paths for IPv4 and IPv6
    target_ipv4_output, target_ipv6_output = generate_output_paths(target_output_base)

    summarize_cidrs(
        target_input,
        target_ipv4_output,
        target_ipv6_output,
        default_segment_dir,
    )
