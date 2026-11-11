"""Shared settings and helpers for the demo video scripts."""

import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
BUILD = HERE / "build"
NAAM = "uitnodigingsregel"
RAW_VIDEO = HERE / f"{NAAM}-showcase.mp4"
FINAL_VIDEO = HERE / f"{NAAM}-showcase-highlighted.mp4"

APP_URL = "http://localhost:8501"
W, H, FPS = 1440, 900, 25
CARD_SECONDS = 3.4

# Colours carry meaning: blue = explanation, green = result, orange = nuance, red = limitation.
KLEUR = {
    "blauw": "#2563eb",
    "groen": "#15803d",
    "oranje": "#d97706",
    "rood": "#b91c1c",
}
ONDERTITEL_RGB = (15, 23, 42)
FONT = "'Source Sans 3', 'Source Sans Pro', 'DejaVu Sans', 'Noto Color Emoji', sans-serif"


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and raise with its stderr tail when it fails."""
    result = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed ({result.returncode}):\n{result.stderr[-1500:]}")
    return result


def get_duration(path: Path) -> float:
    """Return the duration of a video in seconds.

    Playwright writes webm without a duration in the header, so ffprobe can
    return nothing. In that case the file is decoded and the last timestamp is used.
    """
    probe = run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        check=False,
    )
    try:
        return float(probe.stdout.strip())
    except ValueError:
        decoded = run(["ffmpeg", "-i", path, "-f", "null", "-"], check=False)
        times = re.findall(r"time=(\d+):(\d+):(\d+\.?\d*)", decoded.stderr)
        if not times:
            raise RuntimeError(f"Could not determine duration of {path}") from None
        hours, minutes, seconds = times[-1]
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    """Convert '#rrggbb' to an (r, g, b) tuple."""
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
