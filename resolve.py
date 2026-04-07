#!/usr/bin/env python3
"""Resolve manifest and file patterns. Writes download plan for download.py."""

import json
import hashlib
import os
import sys
from fnmatch import fnmatch
from pathlib import Path

import boto3

ENDPOINT = "https://5ab2e190b7cfef75dcbfebcf15b14352.r2.cloudflarestorage.com"
BUCKET = "ffxi-patch"


def get_s3_client():
    key_id = os.environ.get("BUCKET_KEY_ID", "")
    app_key = os.environ.get("BUCKET_APP_KEY", "")
    if not key_id or not app_key:
        print("::error::BUCKET_KEY_ID and BUCKET_APP_KEY environment variables required")
        sys.exit(1)
    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        aws_access_key_id=key_id,
        aws_secret_access_key=app_key,
    )


def set_output(name, value):
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"{name}={value}\n")


def parse_patterns(files_inline, files_from):
    patterns = []
    if files_inline:
        for line in files_inline.splitlines():
            line = line.split("#")[0].strip()
            if line:
                patterns.append(line)
    if files_from:
        files_from_path = Path(files_from).resolve()
        workspace = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
        if not str(files_from_path).startswith(str(workspace)):
            print("::error::files-from path must be within the workspace")
            sys.exit(1)
        if files_from_path.is_file():
            with open(files_from_path) as f:
                for line in f:
                    line = line.split("#")[0].strip()
                    if line:
                        patterns.append(line)
    return patterns


def main():
    files_inline = os.environ.get("INPUT_FILES", "")
    files_from = os.environ.get("INPUT_FILES_FROM", "")
    output_dir = os.environ.get("INPUT_OUTPUT_DIR", "dat")
    version = os.environ.get("INPUT_VERSION", "latest")

    patterns = parse_patterns(files_inline, files_from)
    if not patterns:
        print("::error::No files specified. Use 'files' or 'files-from' input.")
        sys.exit(1)

    s3 = get_s3_client()

    print(f"Fetching manifest: versions/{version}/manifest.json")
    resp = s3.get_object(Bucket=BUCKET, Key=f"versions/{version}/manifest.json")
    manifest = json.loads(resp["Body"].read())
    actual_version = manifest["version"]
    print(f"FFXI version: {actual_version}")

    all_files = {f["path"]: f for f in manifest["files"]}
    resolved = {}
    for pattern in patterns:
        matched = False
        for file_path, entry in all_files.items():
            if fnmatch(file_path, pattern):
                resolved[file_path] = entry
                matched = True
        if not matched:
            print(f"::warning::Pattern '{pattern}' matched no files in manifest")

    if not resolved:
        print("::error::No files matched the provided patterns")
        sys.exit(1)

    print(f"Resolved {len(resolved)} files")

    filehash = hashlib.sha256("\n".join(sorted(resolved.keys())).encode()).hexdigest()[:16]

    set_output("version", actual_version)
    set_output("count", str(len(resolved)))
    set_output("filehash", filehash)

    # Write download plan for download.py
    plan_dir = os.environ.get("RUNNER_TEMP", "/tmp")
    plan_path = os.path.join(plan_dir, "ffxi-download-plan.json")
    plan = [{"path": fp, "key": entry["key"]} for fp, entry in sorted(resolved.items())]
    with open(plan_path, "w") as f:
        json.dump(plan, f)

    print(f"Download plan written: {len(plan)} files")


if __name__ == "__main__":
    main()
