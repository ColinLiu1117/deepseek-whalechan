#!/usr/bin/env python3
"""Create a collection review sheet without cropping or changing originals."""
import argparse
import hashlib
import importlib.util
import os
import math
from pathlib import Path
import shutil
import subprocess
import tempfile

# Small bitmap numerals avoid dependencies on installed fonts. Labels are outside the artwork.
DIGITS = ("010110010010111", "111001111100111", "111001111001111",
          "101101111001001", "111100111001111")
ALL_DIGITS = ("111101101101111", *DIGITS, "111100111101111",
              "111001001001001", "111101111101111", "111101111001111")


def compose(items, output):
    if not items:
        raise ValueError("A collection sheet requires at least one task slot")
    magick = shutil.which("magick")
    if not magick:
        raise RuntimeError("ImageMagick is required")
    if output.exists():
        raise ValueError("Refusing to overwrite a review sheet")
    cell, gutter, label = 600, 16, 36
    columns = math.ceil(math.sqrt(len(items)))
    rows = math.ceil(len(items) / columns)
    width, height = columns * cell + (columns + 1) * gutter, rows * (cell + label) + (rows + 1) * gutter
    command = [magick, "-size", f"{width}x{height}", "xc:white"]
    for n, item in enumerate(items):
        x, y = gutter + (n % columns) * (cell + gutter), gutter + (n // columns) * (cell + label + gutter)
        if item["candidate"]:
            source = Path(item["candidate"])
            if hashlib.sha256(source.read_bytes()).hexdigest() != item["sha256"]:
                raise ValueError("Candidate hash mismatch while composing")
            command += ["(", str(source), "-resize", f"{cell}x{cell}", "-background", "white",
                        "-gravity", "center", "-extent", f"{cell}x{cell}", ")",
                        "-gravity", "NorthWest", "-geometry", f"+{x}+{y+label}", "-composite"]
        else:
            command += ["-fill", "#e5e7eb", "-draw", f"rectangle {x},{y+label} {x+cell-1},{y+label+cell-1}"]
        for digit, number in enumerate(str(n + 1)):
            for k, bit in enumerate(ALL_DIGITS[int(number)]):
                if bit == "1":
                    dx, dy = x + digit * 20 + (k % 3) * 5, y + (k // 3) * 5
                    command += ["-fill", "#111827", "-draw", f"rectangle {dx},{dy} {dx+4},{dy+4}"]
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".sheet-", suffix=".png", dir=output.parent)
    os.close(fd)
    try:
        subprocess.run(command + ["-colorspace", "sRGB", "-alpha", "off", temporary],
                       check=True, capture_output=True, text=True, timeout=60)
        os.replace(temporary, output)
    finally:
        Path(temporary).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("comic_manager", Path(__file__).with_name("manage-run.py"))
    manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(manager)
    import json
    try:
        print(json.dumps(manager.invoke(argparse.Namespace(**vars(args), command="build-review-sheet", handler=manager.review_workflow().build_sheet)), ensure_ascii=False, indent=2))
    except (manager.RunError, ValueError, RuntimeError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(2, str(exc) + "\n")


if __name__ == "__main__":
    main()
