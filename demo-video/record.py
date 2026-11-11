"""Record the takes with Playwright and log every annotation's bounding box.

The bounding box of an element is logged at the moment it is annotated, while
the recording runs. It cannot be recovered reliably afterwards: the page
scrolls, reruns and changes layout.

Usage: python record.py [take ...]   (default: all takes)
"""

import json
import sys
import time
from pathlib import Path

from common import APP_URL, BUILD, ROOT, H, W, get_duration
from playwright.sync_api import Locator, Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from takes import TAKES, TAKES_WITHOUT_MODELS

FINGERPRINT = ROOT / "models" / "training_data.json"
CLICK_LEAD = 0.7


def resolve(page: Page, spec: dict) -> Locator:
    """Turn a target specification into a locator for a single element."""
    if "css" in spec:
        loc = page.locator(spec["css"])
    elif "role" in spec:
        loc = page.get_by_role(spec["role"], name=spec["name"])
    else:
        loc = page.get_by_text(spec["text"])
    if spec.get("nth_visible"):
        loc = loc.locator("visible=true")
    return loc.nth(spec["nth"]) if "nth" in spec else loc.first


def settle(page: Page, timeout: float = 60) -> None:
    """Wait until Streamlit has finished its run, so no loading state is recorded."""
    try:
        page.wait_for_function(
            """() => {
                const status = document.querySelector('[data-testid="stStatusWidget"]');
                const spinner = document.querySelector('[data-testid="stSpinner"]');
                return (!status || status.offsetParent === null) && !spinner;
            }""",
            timeout=timeout * 1000,
        )
    except PlaywrightTimeout:
        print("  ! settle: timeout")
    time.sleep(0.35)


def scroll(page: Page, px: float, steps: int = 26, delay: float = 0.028) -> None:
    """Scroll in small steps so the video shows a movement instead of a jump."""
    # Keep the pointer off the table, otherwise the table scrolls instead of the page.
    page.mouse.move(40, H / 2)
    for _ in range(steps):
        page.mouse.wheel(0, px / steps)
        time.sleep(delay)
    time.sleep(0.4)


def find_box(page: Page, specs: list[dict]) -> dict | None:
    """Return the first usable bounding box from a chain of target specifications."""
    for spec in specs:
        for _ in range(3):
            try:
                loc = resolve(page, spec)
                loc.scroll_into_view_if_needed(timeout=4000)
                time.sleep(0.45)
                box = loc.bounding_box()
            except Exception:
                box = None
            if box and box["width"] > 24 and box["height"] > 8:
                x0, y0 = max(box["x"], 4), max(box["y"], 4)
                x1 = min(box["x"] + box["width"], W - 4)
                y1 = min(box["y"] + box["height"], H - 4)
                if "sub" in spec:
                    fx0, fy0, fx1, fy1 = spec["sub"]
                    bw, bh = x1 - x0, y1 - y0
                    x0, y0, x1, y1 = x0 + fx0 * bw, y0 + fy0 * bh, x0 + fx1 * bw, y0 + fy1 * bh
                return {"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0}
            time.sleep(0.4)
    return None


def record_take(browser, name: str) -> None:
    out_dir = BUILD / name
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.webm"):
        old.unlink()
    if name in TAKES_WITHOUT_MODELS:
        FINGERPRINT.unlink(missing_ok=True)

    ctx = browser.new_context(
        viewport={"width": W, "height": H},
        record_video_dir=str(out_dir),
        record_video_size={"width": W, "height": H},
        accept_downloads=True,
        locale="nl-NL",
    )
    page = ctx.new_page()
    t0 = time.monotonic()

    def now() -> float:
        return time.monotonic() - t0

    layers: list[dict] = []
    marker = 0.0
    cuts: list[list[float]] = []
    subtitle: dict | None = None

    def close_subtitle() -> None:
        if subtitle:
            subtitle["end"] = now()
            layers.append(subtitle)

    def click(target: dict, do_settle: bool = True, download: bool = False) -> None:
        for attempt in range(3):
            try:
                loc = resolve(page, target)
                box = loc.bounding_box()
                cx, cy = box["x"] + min(box["width"] / 2, 60), box["y"] + box["height"] / 2
                page.mouse.move(cx, cy, steps=12)
                start = now()
                time.sleep(CLICK_LEAD)
                if download:
                    with page.expect_download(timeout=15000):
                        page.mouse.click(cx, cy)
                else:
                    page.mouse.click(cx, cy)
                layers.append(
                    {
                        "id": f"klik_{len(layers)}",
                        "soort": "klik",
                        "start": start,
                        "end": now() + 0.25,
                        "x": cx,
                        "y": cy,
                        "kleur": "blauw",
                    }
                )
                break
            except Exception as error:
                print(f"  ! click attempt {attempt + 1} failed: {str(error)[:120]}")
                time.sleep(0.8)
                settle(page)
        else:
            raise RuntimeError(f"click failed: {target}")
        if do_settle:
            settle(page)

    print(f"take {name}")
    for action, args in TAKES[name]:
        if action == "goto":
            page.goto(APP_URL if args["url"] == "app" else args["url"])
            if args["url"] == "app":
                page.wait_for_selector("text=Start analyse", timeout=60000)
            if args.get("settle", True):
                settle(page)
        elif action == "open_results":
            resolve(page, {"text": "Ik werk volgens deze uitgangspunten."}).click()
            settle(page)
            resolve(page, {"role": "button", "name": "Start analyse"}).click()
            page.wait_for_selector("text=Downloads", timeout=240000)
            settle(page)
            time.sleep(1.0)
        elif action == "wait":
            time.sleep(args["s"])
        elif action == "wait_for":
            page.wait_for_selector(f"text={args['text']}", timeout=args.get("timeout", 60) * 1000)
            settle(page)
        elif action == "scroll":
            scroll(page, args["px"], args.get("steps", 26))
        elif action == "scroll_top":
            scroll(page, -3000, 30)
        elif action == "click":
            click(args["target"], args.get("settle", True), args.get("download", False))
        elif action == "marker":
            marker = now() - args.get("terug", 2.0)
        elif action == "cut_start":
            cuts.append([now()])
        elif action == "cut_end":
            cuts[-1].append(now())
        elif action == "sub":
            close_subtitle()
            subtitle = {
                "id": f"sub_{len(layers)}",
                "soort": "ondertitel",
                "start": now(),
                "text": args["text"],
            }
        elif action == "annotate":
            box = find_box(page, args.get("targets") or [args["target"]])
            if box is None:
                print(f"  ! annotatie {args['id']}: element niet gevonden")
                continue
            start = now()
            time.sleep(args.get("hold", 3.5))
            layers.append(
                {
                    "id": args["id"],
                    "soort": "annotatie",
                    "start": start,
                    "end": now(),
                    "box": box,
                    "label": args["label"],
                    "text": args["text"],
                    "kleur": args["kleur"],
                    "chip": args.get("chip", "auto"),
                }
            )
            time.sleep(0.35)
        else:
            raise ValueError(f"unknown action: {action}")

    time.sleep(0.8)
    close_subtitle()
    wall = now()
    video_path = page.video.path()
    ctx.close()
    raw = out_dir / "raw.webm"
    raw.unlink(missing_ok=True)
    Path(video_path).rename(raw)

    # The video can start slightly before t0; shift the logged times to video time.
    offset = get_duration(raw) - wall
    for layer in layers:
        layer["start"] += offset
        layer["end"] += offset
    data = {
        "take": name,
        "duur": wall + offset,
        "marker": max(0.0, marker + offset),
        "offset": offset,
        "cuts": [[a + offset, b + offset] for a, b in cuts],
        "lagen": layers,
    }
    (out_dir / "annotations.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))

    print(f"  duur {data['duur']:.1f}s, marker {data['marker']:.1f}s, offset {offset:+.2f}s")
    for layer in layers:
        if layer["soort"] == "ondertitel":
            length = layer["end"] - layer["start"]
            rate = len(layer["text"]) / length
            flag = "  <-- te kort" if rate > 21 else ""
            print(f"  sub {length:5.1f}s {rate:4.1f} tekens/s{flag}  {layer['text'][:50]}")


def main() -> None:
    names = sys.argv[1:] or list(TAKES)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        warm = browser.new_context(viewport={"width": W, "height": H})
        warm_page = warm.new_page()
        warm_page.goto(APP_URL)
        warm_page.wait_for_selector("text=Start analyse", timeout=60000)
        warm.close()
        for name in names:
            record_take(browser, name)
        browser.close()


if __name__ == "__main__":
    main()
