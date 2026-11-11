"""Verify that every overlay layer is visible in the final video at its time.

The final video is decoded once. For each layer the frame in the middle of its
time window is checked: inside the layer's rectangle there must be enough
pixels in the layer's accent colour (or the dark subtitle bar). The same
frames are saved to build/check/ for a visual review.

Exits non-zero when a layer is missing.
"""

import json
import shutil
import subprocess
import sys

import numpy as np
from common import BUILD, FINAL_VIDEO, FPS, KLEUR, ONDERTITEL_RGB, H, W, get_duration, hex_to_rgb
from PIL import Image

TOLERANCE = 45
THRESHOLD = {"annotatie": 120, "klik": 60, "ondertitel": 3000}


def main() -> None:
    timeline = json.loads((BUILD / "out" / "timeline.json").read_text())
    offsets, elapsed = {}, 0.0
    for part in timeline["parts"]:
        offsets[part.split("/")[-1]] = elapsed
        elapsed += get_duration(part)

    # A layer can span several segments; check it once, in the middle of its whole window.
    windows: dict[tuple, dict] = {}
    for layer in timeline["layers"]:
        key = (layer["clip"], layer["id"])
        start, end = offsets[layer["clip"]] + layer["start"], offsets[layer["clip"]] + layer["end"]
        if key in windows:
            windows[key]["start"] = min(windows[key]["start"], start)
            windows[key]["end"] = max(windows[key]["end"], end)
        else:
            windows[key] = dict(layer, start=start, end=end)
    checks: dict[int, list[dict]] = {}
    for window in windows.values():
        checks.setdefault(round((window["start"] + window["end"]) / 2 * FPS), []).append(window)

    check_dir = BUILD / "check"
    shutil.rmtree(check_dir, ignore_errors=True)
    check_dir.mkdir(parents=True)
    decoder = subprocess.Popen(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(FINAL_VIDEO),
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ],
        stdout=subprocess.PIPE,
    )
    frame_size, index, missing, checked = W * H * 3, 0, 0, 0
    while True:
        buffer = decoder.stdout.read(frame_size)
        if len(buffer) < frame_size:
            break
        if index in checks:
            frame = np.frombuffer(buffer, dtype=np.uint8).reshape(H, W, 3).astype(np.int16)
            for layer in checks[index]:
                x, y, w, h = layer["rect"]
                target = (
                    ONDERTITEL_RGB
                    if layer["soort"] == "ondertitel"
                    else hex_to_rgb(KLEUR[layer["kleur"]])
                )
                region = frame[y : y + h, x : x + w]
                count = int((np.abs(region - np.array(target)).max(axis=2) < TOLERANCE).sum())
                ok = count >= THRESHOLD[layer["soort"]]
                checked += 1
                missing += not ok
                print(
                    f"{'OK  ' if ok else 'MIST'} {index / FPS:7.2f}s {layer['clip']:<16} "
                    f"{layer['id']:<20} {count:>6} px"
                )
                if layer["soort"] == "annotatie":
                    Image.fromarray(frame.astype(np.uint8)).save(
                        check_dir / f"{index:05d}_{layer['id']}.jpg", quality=82
                    )
        index += 1
    decoder.wait()

    print(f"\n{checked} lagen gecontroleerd, {missing} ontbreken; video {index / FPS:.1f}s")
    if missing or checked != len(windows):
        sys.exit(1)


if __name__ == "__main__":
    main()
