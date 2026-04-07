#!/usr/bin/env python3
"""Download files from B2 using the plan written by resolve.py."""

import json
import os
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import boto3

ENDPOINT = "https://5ab2e190b7cfef75dcbfebcf15b14352.r2.cloudflarestorage.com"
BUCKET = "ffxi-patch"

_thread_local = threading.local()


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


def get_thread_s3():
    if not hasattr(_thread_local, "s3"):
        _thread_local.s3 = get_s3_client()
    return _thread_local.s3


def download_file(key, output_path):
    s3 = get_thread_s3()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output_path.parent, suffix=".zst", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        s3.download_file(BUCKET, key, str(tmp_path))
        subprocess.run(["zstd", "-d", "-f", str(tmp_path), "-o", str(output_path)],
                       check=True, capture_output=True)
    finally:
        tmp_path.unlink(missing_ok=True)


def main():
    output_dir = Path(os.environ.get("INPUT_OUTPUT_DIR", "dat"))
    plan_dir = os.environ.get("RUNNER_TEMP", "/tmp")
    plan_path = os.path.join(plan_dir, "ffxi-download-plan.json")

    with open(plan_path) as f:
        plan = json.load(f)

    print(f"Downloading {len(plan)} files...")
    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    failed = 0
    total = len(plan)
    lock = threading.Lock()

    def do_download(entry):
        download_file(entry["key"], output_dir / entry["path"])
        return entry["path"]

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(do_download, entry): entry["path"] for entry in plan}
        for future in as_completed(futures):
            fp = futures[future]
            with lock:
                try:
                    future.result()
                    downloaded += 1
                    print(f"  [{downloaded + failed}/{total}] {fp}", flush=True)
                except Exception as e:
                    failed += 1
                    print(f"::warning::Failed to download {fp}: {e}", flush=True)

    print(f"\nDone: {downloaded} downloaded, {failed} failed")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
