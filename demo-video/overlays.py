"""Render title cards and overlay layers (ring, arrow, chip, subtitle) as PNG.

Layers are rendered with a browser because ring glow, text wrapping and the
SVG arrow are a stylesheet in CSS. Every layer PNG is cropped to its alpha
content; the offset is stored so compose.py can place it.

Texts are read from takes.py, so wording can change without a new recording.
"""

import html
import json

from common import BUILD, FONT, KLEUR, H, W
from PIL import Image
from playwright.sync_api import Page, sync_playwright
from takes import CARD_FOOTER, CARDS, TAKES

SUBTITLE_ZONE = 118  # px at the bottom kept free for subtitles

BASE_CSS = f"""
html, body {{ margin: 0; width: {W}px; height: {H}px; background: transparent;
  font-family: {FONT}; overflow: hidden; }}
"""

ANNOTATION_HTML = """<style>{base}
#ring {{ position: absolute; left: {x}px; top: {y}px; width: {w}px; height: {h}px;
  box-sizing: border-box; border: 4px solid {c}; border-radius: 12px;
  box-shadow: 0 0 0 4px {c}40, 0 0 24px {c}8c; }}
#chip {{ position: absolute; left: 0; top: 0; max-width: 372px; box-sizing: border-box;
  background: #ffffff; border-left: 8px solid {c}; border-radius: 12px;
  padding: 12px 18px 13px 16px; box-shadow: 0 10px 30px rgba(15,23,42,.30); }}
#chip b {{ display: block; color: {c}; font-size: 18px; margin-bottom: 3px; }}
#chip span {{ color: #0f172a; font-size: 16.5px; line-height: 1.34; }}
svg {{ position: absolute; left: 0; top: 0; }}
</style>
<div id="ring"></div>
<svg id="pijl" width="{W}" height="{H}"></svg>
<div id="chip"><b>{label}</b><span>{text}</span></div>
<script>
(() => {{
const W = {W}, H = {H}, ZONE = {zone}, GAP = 44, mode = "{mode}";
const chipEl = document.getElementById('chip');
const ring = document.getElementById('ring').getBoundingClientRect();
const cw = chipEl.offsetWidth, ch = chipEl.offsetHeight;
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
let left, top, side;
const cx = ring.left + ring.width / 2;
// Prefer the empty space beside the element, so the chip does not cover the interface.
const fits = {{
  rechts: ring.right + GAP + cw <= W - 20,
  boven: ring.top - ch - GAP >= 18,
  onder: ring.bottom + GAP + ch <= H - ZONE,
  links: ring.left - GAP - cw >= 20,
}};
side = mode !== 'auto' ? mode
  : ['rechts', 'boven', 'onder', 'links'].find(s => fits[s]) || 'binnen';
const cy = ring.top + ring.height / 2;
if (side === 'boven' || side === 'onder') {{
  top = side === 'boven' ? ring.top - ch - GAP : ring.bottom + GAP;
  left = clamp(cx + 34, 36, W - 36 - cw);
}} else if (side === 'rechts' || side === 'links') {{
  left = side === 'rechts' ? ring.right + GAP : ring.left - GAP - cw;
  top = clamp(cy - ch / 2 + 26, 24, H - ZONE - ch);
}} else {{
  left = ring.right - cw - 22; top = ring.top + 58;
}}
chipEl.style.left = left + 'px'; chipEl.style.top = top + 'px';
if (side !== 'binnen') {{
  const chip = chipEl.getBoundingClientRect();
  let x1, y1, x2, y2;
  if (side === 'boven' || side === 'onder') {{
    x1 = chip.left + 30;
    y1 = side === 'boven' ? chip.bottom + 2 : chip.top - 2;
    x2 = clamp(x1 - 46, ring.left + 14, ring.right - 14);
    y2 = side === 'boven' ? ring.top - 7 : ring.bottom + 7;
  }} else {{
    y1 = chip.top + chip.height / 2;
    x1 = side === 'rechts' ? chip.left - 2 : chip.right + 2;
    y2 = clamp(y1 - 30, ring.top + 14, ring.bottom - 14);
    x2 = side === 'rechts' ? ring.right + 7 : ring.left - 7;
  }}
  const dx = x2 - x1, dy = y2 - y1;
  const bend = clamp((Math.abs(dx) + Math.abs(dy)) * 0.28, -70, 70);
  const qx = (x1 + x2) / 2 + (side === 'boven' || side === 'onder' ? -bend * 0.5 : 0);
  const qy = (y1 + y2) / 2 + (side === 'rechts' || side === 'links' ? -bend * 0.5 : 0);
  document.getElementById('pijl').innerHTML = `
    <defs><marker id="punt" markerWidth="9" markerHeight="9" refX="6.5" refY="4.5"
      orient="auto"><path d="M0 0 L9 4.5 L0 9 Z" fill="{c}"/></marker></defs>
    <path d="M ${{x1}} ${{y1}} Q ${{qx}} ${{qy}} ${{x2}} ${{y2}}" fill="none" stroke="{c}"
      stroke-width="4" stroke-linecap="round" marker-end="url(#punt)"/>`;
}}
}})();
</script>"""

SUBTITLE_HTML = """<style>{base}
#balk {{ position: absolute; left: 50%; {edge}: 30px; transform: translateX(-50%);
  max-width: 1180px; width: max-content; box-sizing: border-box;
  background: rgba(15,23,42,.90); color: #ffffff; font-size: 24px; line-height: 1.32;
  font-weight: 600; padding: 15px 30px 16px 26px; border-radius: 14px;
  border-left: 8px solid #c8785a; text-align: center; }}
</style><div id="balk">{text}</div>"""

CLICK_HTML = """<style>{base}
#klik {{ position: absolute; left: {x}px; top: {y}px; width: 44px; height: 44px;
  margin: -22px 0 0 -22px; box-sizing: border-box; border: 5px solid {c}; border-radius: 50%; }}
</style><div id="klik"></div>"""

CARD_HTML = """<style>{base}
body {{ background: #1a1a1a; color: #ffffff; }}
#rand {{ position: absolute; left: 0; top: 0; width: 18px; height: 100%; background: #c8785a; }}
#blok {{ position: absolute; left: 130px; top: 50%; transform: translateY(-56%); width: 1150px; }}
#eyebrow {{ color: #f0d4d4; font-size: 26px; letter-spacing: .12em; text-transform: uppercase;
  font-weight: 600; margin-bottom: 22px; }}
#titel {{ font-size: {size}px; font-weight: 700; line-height: 1.1; margin-bottom: 26px; }}
#sub {{ font-size: 32px; color: #e5e7eb; line-height: 1.35; }}
#voet {{ position: absolute; left: 130px; bottom: 54px; font-size: 19px; color: #9ca3af; }}
</style>
<div id="rand"></div>
<div id="blok"><div id="eyebrow">{eyebrow}</div><div id="titel">{titel}</div>
<div id="sub">{sub}</div></div><div id="voet">{voet}</div>"""


def crop_to_alpha(path, margin: int = 6) -> tuple[int, int, int, int]:
    """Crop a PNG to its visible content and return (x, y, width, height).

    An uncropped full-frame layer costs megabytes per layer during composition.
    """
    image = Image.open(path).convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise RuntimeError(f"empty layer: {path}")
    x0, y0 = max(bbox[0] - margin, 0), max(bbox[1] - margin, 0)
    x1, y1 = min(bbox[2] + margin, W), min(bbox[3] + margin, H)
    image.crop((x0, y0, x1, y1)).save(path)
    return x0, y0, x1 - x0, y1 - y0


def layer_html(layer: dict) -> str:
    colour = KLEUR.get(layer.get("kleur", "blauw"))
    if layer["soort"] == "ondertitel":
        edge = "top" if layer.get("pos") == "boven" else "bottom"
        return SUBTITLE_HTML.format(base=BASE_CSS, edge=edge, text=html.escape(layer["text"]))
    if layer["soort"] == "klik":
        return CLICK_HTML.format(base=BASE_CSS, x=layer["x"], y=layer["y"], c=colour)
    box, pad = layer["box"], 9
    x, y = max(box["x"] - pad, 2), max(box["y"] - pad, 2)
    bottom = min(box["y"] + box["height"] + pad, H - 2)
    if box["y"] < H - SUBTITLE_ZONE - 80:
        # Keep a ring that runs to the bottom of the screen clear of the subtitle.
        bottom = min(bottom, H - SUBTITLE_ZONE + 6)
    return ANNOTATION_HTML.format(
        base=BASE_CSS,
        c=colour,
        W=W,
        H=H,
        zone=SUBTITLE_ZONE,
        mode=layer.get("chip", "auto"),
        x=x,
        y=y,
        w=min(box["x"] + box["width"] + pad, W - 2) - x,
        h=bottom - y,
        label=html.escape(layer["label"]),
        text=html.escape(layer["text"]),
    )


def apply_current_texts(name: str, layers: list[dict]) -> None:
    """Replace logged texts with the current wording in takes.py."""
    steps = TAKES[name]
    by_id = {args["id"]: args for action, args in steps if action == "annotate"}
    subtitles = [args for action, args in steps if action == "sub"]
    logged = [layer for layer in layers if layer["soort"] == "ondertitel"]
    if len(logged) != len(subtitles):
        raise RuntimeError(f"{name}: subtitles changed in number; record the take again")
    for layer, args in zip(logged, subtitles, strict=True):
        layer["text"] = args["text"]
        layer["pos"] = args.get("pos", "onder")
    for layer in layers:
        if layer["soort"] == "annotatie":
            for key in ("label", "text", "kleur", "chip"):
                if key in by_id[layer["id"]]:
                    layer[key] = by_id[layer["id"]][key]


def render(page: Page, content: str, path, transparent: bool = True) -> None:
    page.set_content(content)
    page.wait_for_timeout(120)
    page.screenshot(path=str(path), omit_background=transparent)


def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_context(viewport={"width": W, "height": H}).new_page()

        cards_dir = BUILD / "cards"
        cards_dir.mkdir(parents=True, exist_ok=True)
        for key, card in CARDS.items():
            size = 58 if len(card["titel"]) > 30 else 84
            content = CARD_HTML.format(
                base=BASE_CSS,
                size=size,
                voet=html.escape(CARD_FOOTER),
                **{k: html.escape(v) for k, v in card.items()},
            )
            render(page, content, cards_dir / f"{key}.png", transparent=False)

        for name in TAKES:
            take_dir = BUILD / name
            data = json.loads((take_dir / "annotations.json").read_text())
            apply_current_texts(name, data["lagen"])
            layer_dir = take_dir / "lagen"
            layer_dir.mkdir(exist_ok=True)
            for layer in data["lagen"]:
                path = layer_dir / f"{layer['id']}.png"
                render(page, layer_html(layer), path)
                layer["png"] = str(path)
                layer["px"], layer["py"], layer["pw"], layer["ph"] = crop_to_alpha(path)
            (take_dir / "layers.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
            print(f"{name}: {len(data['lagen'])} lagen")
        browser.close()


if __name__ == "__main__":
    main()
