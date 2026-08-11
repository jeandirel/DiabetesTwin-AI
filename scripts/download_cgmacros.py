from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

URL = "https://physionet.org/files/cgmacros/1.0.0/CGMacros_dateshifted365.zip"
EXPECTED_SHA256 = "05c8b0e6f1a2757050aced55ce4bf6ab2ac9b30f2fd8ca193056812d9c621d4d"
S3_BUCKET_URL = "https://physionet-open.s3.amazonaws.com"
S3_PREFIX = "cgmacros/1.0.0/"
_PARTICIPANT_KEY = re.compile(r"cgmacros/1\.0\.0/CGMacros-(\d{3})/CGMacros-\1\.csv$")


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


def _list_s3_keys(prefix: str) -> list[tuple[str, int]]:
    objects: list[tuple[str, int]] = []
    continuation: str | None = None
    namespace = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}

    while True:
        params = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if continuation:
            params["continuation-token"] = continuation
        url = f"{S3_BUCKET_URL}/?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=60) as response:
            root = ET.fromstring(response.read())

        for item in root.findall("s3:Contents", namespace):
            key_node = item.find("s3:Key", namespace)
            size_node = item.find("s3:Size", namespace)
            if key_node is not None and key_node.text:
                objects.append((key_node.text, int(size_node.text or 0) if size_node is not None else 0))

        truncated = (root.findtext("s3:IsTruncated", default="false", namespaces=namespace) or "false").lower()
        if truncated != "true":
            break
        continuation = root.findtext("s3:NextContinuationToken", namespaces=namespace)
        if not continuation:
            break
    return objects


def download_minimal(destination: Path, *, force: bool = False) -> Path:
    """Download only bio.csv plus the 45 participant CSVs needed for forecasting.

    This uses the same public PhysioNet S3 distribution but skips meal photographs, microbiome files,
    PDFs, and the 627 MB all-in-one ZIP. It is intended for reproducible model training and CI.
    """
    destination.mkdir(parents=True, exist_ok=True)
    marker = destination / ".cgmacros-1.0.0-minimal-ready"
    if marker.exists() and not force:
        print(f"Minimal CGMacros 1.0.0 already prepared in {destination}")
        return destination
    if force and marker.exists():
        marker.unlink()

    print("Source: PhysioNet CGMacros v1.0.0 (DOI 10.13026/3z8q-x658)")
    print("Mode: forecasting CSVs only; raw data remain CC BY-NC-SA 4.0.")
    objects = _list_s3_keys(S3_PREFIX)
    selected = [(key, size) for key, size in objects if key == f"{S3_PREFIX}bio.csv" or _PARTICIPANT_KEY.match(key)]
    participant_count = sum(bool(_PARTICIPANT_KEY.match(key)) for key, _ in selected)
    if participant_count != 45 or not any(key.endswith("/bio.csv") for key, _ in selected):
        raise RuntimeError(
            f"Unexpected PhysioNet listing: found {participant_count} participant CSVs and "
            f"bio.csv={any(key.endswith('/bio.csv') for key, _ in selected)}."
        )

    total_bytes = sum(size for _, size in selected)
    print(f"Downloading {len(selected)} CSV files ({total_bytes / 1e6:.1f} MB) instead of the full archive...")
    for index, (key, _) in enumerate(sorted(selected), start=1):
        relative = Path(key).relative_to(S3_PREFIX)
        output = destination / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists() and not force:
            continue
        encoded_key = urllib.parse.quote(key, safe="/")
        urllib.request.urlretrieve(f"{S3_BUCKET_URL}/{encoded_key}", output)
        print(f"[{index:02d}/{len(selected)}] {relative}")

    marker.write_text(
        "CGMacros v1.0.0 minimal forecasting files\n"
        "Source: PhysioNet public S3 distribution\n"
        "DOI: 10.13026/3z8q-x658\n"
        "License: CC BY-NC-SA 4.0\n",
        encoding="utf-8",
    )
    print(f"Minimal CGMacros ready in {destination.resolve()}")
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
        help="Download only bio.csv and participant CGM/lifestyle CSVs required for forecasting.",
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
