#!/usr/bin/env python3
"""Verify that the expected submitted-figure deliverables are present."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "submission_figures",
    )
    args = parser.parse_args()
    failures: list[str] = []

    for number in range(1, 17):
        png = args.output_dir / f"Figure_{number:02d}.png"
        if not png.is_file() or png.stat().st_size == 0:
            failures.append(f"missing or empty: {png}")
            continue
        with Image.open(png) as image:
            image.verify()
        print(f"Figure {number:02d}: PNG OK, sha256={digest(png)[:12]}")

        if number >= 5:
            for suffix in (".pdf", ".svg"):
                path = args.output_dir / f"Figure_{number:02d}{suffix}"
                if not path.is_file() or path.stat().st_size == 0:
                    failures.append(f"missing or empty: {path}")

    if failures:
        raise SystemExit("Verification failed:\n- " + "\n- ".join(failures))
    print("Verification passed: 16 submitted figures and all expected vector exports are present.")


if __name__ == "__main__":
    main()
