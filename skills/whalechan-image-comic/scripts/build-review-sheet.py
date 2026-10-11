#!/usr/bin/env python3
"""Create a five-slot collection review sheet without cropping or changing originals."""
import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

# Small bitmap numerals avoid dependencies on installed fonts. Labels are outside the artwork.
DIGITS = ("010110010010111", "111001111100111", "111001111001111",
          "101101111001001", "111100111001111")


def compose(items, output):
    if len(items) != 5:
        raise ValueError("A collection sheet requires exactly five task slots")
    magick = shutil.which("magick")
    if not magick:
        raise RuntimeError("ImageMagick is required")
    if output.exists():
        raise ValueError("Refusing to overwrite a review sheet")
    cell, gutter, label = 600, 16, 36
    width, height = 3 * cell + 4 * gutter, 2 * (cell + label) + 3 * gutter
    command = [magick, "-size", f"{width}x{height}", "xc:white"]
    for n, item in enumerate(items):
        x, y = gutter + (n % 3) * (cell + gutter), gutter + (n // 3) * (cell + label + gutter)
        if item["candidate"]:
            source = Path(item["candidate"])
            if hashlib.sha256(source.read_bytes()).hexdigest() != item["sha256"]:
                raise ValueError("Candidate hash mismatch while composing")
            command += ["(", str(source), "-resize", f"{cell}x{cell}", "-background", "white",
                        "-gravity", "center", "-extent", f"{cell}x{cell}", ")",
                        "-gravity", "NorthWest", "-geometry", f"+{x}+{y+label}", "-composite"]
        else:
            command += ["-fill", "#e5e7eb", "-draw", f"rectangle {x},{y+label} {x+cell-1},{y+label+cell-1}"]
        for k, bit in enumerate(DIGITS[n]):
            if bit == "1":
                dx, dy = x + (k % 3) * 5, y + (k // 3) * 5
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
