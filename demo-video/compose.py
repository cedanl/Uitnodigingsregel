"""Compose the recordings, overlay layers and title cards into the two videos.

Overlays are not added as separate ffmpeg inputs: with a dozen inputs the
filter graph runs out of memory. Instead each clip's timeline is cut at every
layer boundary, the layers active in a segment are flattened into one image,
and the segments form one overlay track with alpha (ffv1/yuva420p). The final
pass then has two inputs: the recording and that track.

The raw recordings are never modified.
"""

import json
import shutil

from common import BUILD, CARD_SECONDS, FINAL_VIDEO, FPS, RAW_VIDEO, H, W, get_duration, run
from PIL import Image
from takes import SEQUENCE

FADE = 0.35
CARD_FADE = 0.45
ENCODE = [
    "-c:v",
    "libx264",
    "-preset",
    "veryfast",
    "-crf",
    "20",
    "-pix_fmt",
    "yuv420p",
    "-r",
    str(FPS),
    "-movflags",
    "+faststart",
    "-an",
]
NORMALISE = (
    f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
    f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=white,fps={FPS},format=yuv420p"
)


def to_frame(seconds: float) -> int:
    return round(seconds * FPS)


def build_clips(data: dict, duration: float) -> list[tuple[float, float]]:
    """Return the parts of the recording to keep: after the marker, minus the cuts."""
    clips, start = [], data["marker"]
    for cut_start, cut_end in data.get("cuts", []):
        clips.append((start, cut_start))
        start = cut_end - 0.5
    clips.append((start, duration))
    return clips


def build_segments(layers: list[dict], clip: tuple[float, float]) -> list[tuple[int, int, list]]:
    """Cut a clip at every layer boundary and list the layers active in each segment.

    Cut points are snapped to frames. Overlap is tested with a margin of half a
    frame, so a layer whose end rounds just below a boundary does not disappear.
    """
    clip_start, clip_end = clip
    total = to_frame(clip_end - clip_start)
    spans = []
    for layer in layers:
        first = max(0, to_frame(layer["start"] - clip_start))
        last = min(total, to_frame(layer["end"] - clip_start))
        if last - first >= 1:
            spans.append((first, last, layer))
    points = sorted({0, total, *(p for first, last, _ in spans for p in (first, last))})
    segments: list[tuple[int, int, list]] = []
    for a, b in zip(points, points[1:], strict=False):
        active = [layer for first, last, layer in spans if first < b and last > a]
        if segments and [x["id"] for x in segments[-1][2]] == [x["id"] for x in active]:
            segments[-1] = (segments[-1][0], b, active)
        else:
            segments.append((a, b, active))
    return segments


def build_overlay_track(segments: list, work_dir, name: str):
    """Flatten the layers per segment and encode them as one track with alpha."""
    parts = []
    for index, (a, b, active) in enumerate(segments):
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        # Subtitles go on top so an annotation never hides them.
        for layer in sorted(active, key=lambda item: item["soort"] == "ondertitel"):
            canvas.alpha_composite(
                Image.open(layer["png"]).convert("RGBA"), (layer["px"], layer["py"])
            )
        scene = work_dir / f"{name}_scene_{index:03d}.png"
        canvas.save(scene)
        part = work_dir / f"{name}_scene_{index:03d}.mkv"
        run(
            [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-framerate",
                FPS,
                "-i",
                scene,
                "-frames:v",
                b - a,
                "-c:v",
                "ffv1",
                "-pix_fmt",
                "yuva420p",
                "-r",
                FPS,
                "-an",
                part,
            ]
        )
        parts.append(part)
    listing = work_dir / f"{name}_scenes.txt"
    listing.write_text("".join(f"file '{part}'\n" for part in parts))
    track = work_dir / f"{name}_overlay.mkv"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listing, "-c", "copy", track])
    return track


def render_take(name: str, out_dir) -> tuple[list, list, list[dict]]:
    """Render a take's clips with and without overlays; return paths and layer timing."""
    take_dir = BUILD / name
    data = json.loads((take_dir / "layers.json").read_text())
    raw = take_dir / "raw.webm"
    highlighted, plain, timing, elapsed = [], [], [], 0.0
    for index, clip in enumerate(build_clips(data, get_duration(raw))):
        frames = to_frame(clip[1] - clip[0])
        length = frames / FPS
        clip_name = f"{name}_{index}"
        segments = build_segments(data["lagen"], clip)
        track = build_overlay_track(segments, out_dir / "scenes", clip_name)
        fades = f"fade=t=in:st=0:d={FADE},fade=t=out:st={length - FADE:.3f}:d={FADE}"
        source = ["-thread_queue_size", "64", "-ss", f"{clip[0]:.3f}", "-i", raw]

        plain_path = out_dir / f"{clip_name}_raw.mp4"
        run(
            [
                "ffmpeg",
                "-y",
                *source,
                "-vf",
                f"{NORMALISE},{fades}",
                "-frames:v",
                frames,
                *ENCODE,
                plain_path,
            ]
        )
        final_path = out_dir / f"{clip_name}.mp4"
        run(
            [
                "ffmpeg",
                "-y",
                *source,
                "-thread_queue_size",
                "64",
                "-i",
                track,
                "-filter_complex",
                f"[0:v]{NORMALISE}[basis];[1:v]format=rgba[laag];"
                f"[basis][laag]overlay=0:0:shortest=1,{fades}[uit]",
                "-map",
                "[uit]",
                "-frames:v",
                frames,
                *ENCODE,
                final_path,
            ]
        )
        plain.append(plain_path)
        highlighted.append(final_path)
        for a, b, active in segments:
            for layer in active:
                timing.append(
                    {
                        "id": layer["id"],
                        "soort": layer["soort"],
                        "kleur": layer.get("kleur"),
                        "clip": f"{clip_name}.mp4",
                        "start": a / FPS,
                        "end": b / FPS,
                        "rect": [layer["px"], layer["py"], layer["pw"], layer["ph"]],
                    }
                )
        elapsed += length
    return highlighted, plain, timing


def render_card(key: str, out_dir):
    path = out_dir / f"card_{key}.mp4"
    fades = (
        f"fade=t=in:st=0:d={CARD_FADE},fade=t=out:st={CARD_SECONDS - CARD_FADE:.3f}:d={CARD_FADE}"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-framerate",
            FPS,
            "-i",
            BUILD / "cards" / f"{key}.png",
            "-vf",
            f"{NORMALISE},{fades}",
            "-frames:v",
            to_frame(CARD_SECONDS),
            *ENCODE,
            path,
        ]
    )
    return path


def concat(paths: list, target) -> None:
    listing = BUILD / "out" / f"{target.stem}.txt"
    listing.write_text("".join(f"file '{path}'\n" for path in paths))
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            listing,
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            target,
        ]
    )


def main() -> None:
    out_dir = BUILD / "out"
    shutil.rmtree(out_dir, ignore_errors=True)
    (out_dir / "scenes").mkdir(parents=True)

    final_parts, raw_parts, timeline = [], [], []
    for kind, key in SEQUENCE:
        if kind == "card":
            final_parts.append(render_card(key, out_dir))
            continue
        highlighted, plain, timing = render_take(key, out_dir)
        final_parts.extend(highlighted)
        raw_parts.extend(plain)
        timeline.extend(timing)
        print(f"take {key}: {len(highlighted)} clip(s)")

    concat(raw_parts, RAW_VIDEO)
    concat(final_parts, FINAL_VIDEO)
    (out_dir / "timeline.json").write_text(
        json.dumps({"parts": [str(p) for p in final_parts], "layers": timeline}, indent=1)
    )
    shutil.rmtree(out_dir / "scenes")
    for video in (RAW_VIDEO, FINAL_VIDEO):
        size = video.stat().st_size / 1e6
        print(f"{video.name}: {get_duration(video):.1f}s, {size:.1f} MB")


if __name__ == "__main__":
    main()
