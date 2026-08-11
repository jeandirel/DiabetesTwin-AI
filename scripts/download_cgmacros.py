from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

URL = "https://physionet.org/files/cgmacros/1.0.0/CGMacros_dateshifted365.zip"
EXPECTED_SHA256 = "05c8b0e6f1a2757050aced55ce4bf6ab2ac9b30f2fd8ca193056812d9c621d4d"
S3_SOURCE = "s3://physionet-open/cgmacros/1.0.0/"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _progress(block_count: int, block_size: int, total_size: int) -> None:
    if total_size <= 0:
        return
    downloaded = min(block_count * block_size, total_size)
    percent = downloaded * 100.0 / total_size
    sys.stdout.write(f"\rDownloading CGMacros: {percent:5.1f}% ({downloaded / 1e6:.1f}/{total_size / 1e6:.1f} MB)")
    sys.stdout.flush()


def download_minimal(destination: Path, *, force: bool = False) -> Path:
    """Download only the official CSV files required for forecasting.

    Uses the public PhysioNet S3 distribution documented on the CGMacros page and excludes
    photographs, the microbiome tables, PDFs, and the 627 MB all-in-one ZIP.
    """
    destination.mkdir(parents=True, exist_ok=True)
    marker = destination / ".cgmacros-1.0.0-minimal-ready"
    if marker.exists() and not force:
        print(f"Minimal CGMacros 1.0.0 already prepared in {destination}")
        return destination
    if force and marker.exists():
        marker.unlink()

    if shutil.which("aws") is None:
        raise RuntimeError(
            "The --minimal mode requires the AWS CLI. Install awscli or run without --minimal "
            "to use the official PhysioNet ZIP archive."
        )

    print("Source: PhysioNet CGMacros v1.0.0 (DOI 10.13026/3z8q-x658)")
    print("Mode: bio.csv + participant CGM/lifestyle CSVs only; license remains CC BY-NC-SA 4.0.")
    command = [
        "aws",
        "s3",
        "sync",
        "--no-sign-request",
        S3_SOURCE,
        str(destination),
        "--exclude",
        "*",
        "--include",
        "bio.csv",
        "--include",
        "CGMacros-*/CGMacros-*.csv",
        "--only-show-errors",
    ]
    subprocess.run(command, check=True)

    participant_files = sorted(destination.rglob("CGMacros-*.csv"))
    participant_files = [path for path in participant_files if path.parent.name.startswith("CGMacros-")]
    bio_file = destination / "bio.csv"
    if len(participant_files) != 45 or not bio_file.exists():
        raise RuntimeError(
            f"Unexpected minimal download: participant CSVs={len(participant_files)}, bio.csv={bio_file.exists()}."
        )

    marker.write_text(
        "CGMacros v1.0.0 minimal forecasting files\n"
        "Source: PhysioNet public S3 distribution\n"
        "DOI: 10.13026/3z8q-x658\n"
        "License: CC BY-NC-SA 4.0\n",
        encoding="utf-8",
    )
    total_mb = sum(path.stat().st_size for path in participant_files + [bio_file]) / 1e6
    print(f"Downloaded 45 participant CSVs + bio.csv ({total_mb:.1f} MB) to {destination.resolve()}")
    return destination


def download_and_extract(destination: Path, *, keep_zip: bool = False, force: bool = False) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    zip_path = destination / "CGMacros_dateshifted365.zip"
    marker = destination / ".cgmacros-1.0.0-ready"

    if marker.exists() and not force:
        print(f"CGMacros 1.0.0 already prepared in {destination}")
        return destination

    if force and marker.exists():
        marker.unlink()

    if not zip_path.exists() or force:
        print("Source: PhysioNet CGMacros v1.0.0 (DOI 10.13026/3z8q-x658)")
        print("License: CC BY-NC-SA 4.0. The dataset is not redistributed by this repository.")
        urllib.request.urlretrieve(URL, zip_path, reporthook=_progress)
        print()

    actual = _sha256(zip_path)
    if actual != EXPECTED_SHA256:
        raise RuntimeError(
            "Downloaded archive checksum does not match PhysioNet SHA256SUMS.txt. "
            f"Expected {EXPECTED_SHA256}, got {actual}."
        )

    print("Checksum verified. Extracting archive...")
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(destination)

    marker.write_text(
        "CGMacros v1.0.0\nDOI: 10.13026/3z8q-x658\nLicense: CC BY-NC-SA 4.0\n",
        encoding="utf-8",
    )
    if not keep_zip:
        zip_path.unlink(missing_ok=True)

    print(f"CGMacros ready in {destination.resolve()}")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the official open-access CGMacros dataset from PhysioNet.")
    parser.add_argument("--destination", type=Path, default=Path("data/raw/cgmacros"))
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Download only bio.csv and participant CGM/lifestyle CSVs required for forecasting (AWS CLI required).",
    )
    parser.add_argument("--keep-zip", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--clean", action="store_true", help="Remove destination before downloading.")
    args = parser.parse_args()

    if args.clean and args.destination.exists():
        shutil.rmtree(args.destination)
    if args.minimal:
        download_minimal(args.destination, force=args.force)
    else:
        download_and_extract(args.destination, keep_zip=args.keep_zip, force=args.force)


if __name__ == "__main__":
    main()
