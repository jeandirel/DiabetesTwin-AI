from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

HTTP_URL = "https://physionet.org/files/cgmacros/1.0.0/CGMacros_dateshifted365.zip"
S3_ZIP = "s3://physionet-open/cgmacros/1.0.0/CGMacros_dateshifted365.zip"
EXPECTED_SHA256 = "05c8b0e6f1a2757050aced55ce4bf6ab2ac9b30f2fd8ca193056812d9c621d4d"


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


def _download_archive(zip_path: Path) -> None:
    print("Source: PhysioNet CGMacros v1.0.0 (DOI 10.13026/3z8q-x658)")
    print("License: CC BY-NC-SA 4.0. The dataset is not redistributed by this repository.")

    if shutil.which("aws") is not None:
        print("Downloading from the official PhysioNet public S3 distribution...")
        subprocess.run(
            [
                "aws",
                "s3",
                "cp",
                "--no-sign-request",
                S3_ZIP,
                str(zip_path),
                "--only-show-errors",
            ],
            check=True,
        )
    else:
        print("AWS CLI not found; falling back to the official PhysioNet HTTPS archive...")
        urllib.request.urlretrieve(HTTP_URL, zip_path, reporthook=_progress)
        print()


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
        _download_archive(zip_path)

    actual = _sha256(zip_path)
    if actual != EXPECTED_SHA256:
        zip_path.unlink(missing_ok=True)
        raise RuntimeError(
            "Downloaded archive checksum does not match PhysioNet SHA256SUMS.txt. "
            f"Expected {EXPECTED_SHA256}, got {actual}."
        )

    print("Checksum verified. Extracting archive...")
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(destination)

    marker.write_text(
        "CGMacros v1.0.0\n"
        "DOI: 10.13026/3z8q-x658\n"
        "License: CC BY-NC-SA 4.0\n"
        f"SHA256: {EXPECTED_SHA256}\n",
        encoding="utf-8",
    )
    if not keep_zip:
        zip_path.unlink(missing_ok=True)

    participant_files = [
        path
        for path in destination.rglob("CGMacros-*.csv")
        if path.parent.name.startswith("CGMacros-")
    ]
    print(f"CGMacros ready in {destination.resolve()} ({len(participant_files)} participant CSV files found)")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the official open-access CGMacros dataset from PhysioNet.")
    parser.add_argument("--destination", type=Path, default=Path("data/raw/cgmacros"))
    parser.add_argument("--keep-zip", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--clean", action="store_true", help="Remove destination before downloading.")
    args = parser.parse_args()

    if args.clean and args.destination.exists():
        shutil.rmtree(args.destination)
    download_and_extract(args.destination, keep_zip=args.keep_zip, force=args.force)


if __name__ == "__main__":
    main()
