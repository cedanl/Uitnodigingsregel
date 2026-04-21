"""app/styles.py — CSS en kleurconstanten voor de Uitnodigingsregel-frontend."""

# ─────────────────────────────────────────────
# Kleurconstanten
# ─────────────────────────────────────────────

TERRACOTTA = "#c8785a"
ROZE_BG    = "#f0d4d4"
ROZE_LICHT = "#fae8e8"

# ─────────────────────────────────────────────
# CSS — Startscherm
# ─────────────────────────────────────────────

START_CSS = """
<style>
@import url('https://api.fontshare.com/v2/css?f[]=general-sans@400,500,600,700&display=swap');

[data-testid="stApp"] { background-color: #f0d4d4; font-family: 'General Sans', sans-serif; font-weight: 500; }
[data-testid="stSidebarCollapsedControl"] { display: none; }
[data-testid="stHeader"] { background-color: #f0d4d4 !important; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }

/* ── Bestand uploaden ── */
[data-testid="stFileUploader"] {
    background: #f2e4e4 !important;
    border-radius: 12px !important;
    padding: 4px 12px !important;
}
[data-testid="stFileUploaderDropzone"] {
    border: none !important;
    background: transparent !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background-color: #1a1a1a !important;
    color: white !important;
    border-radius: 50px !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    border: none !important;
    letter-spacing: 0.06em !important;
}

/* ── START knop ── */
[data-testid="stBaseButton-primary"] {
    background-color: #1a1a1a !important;
    color: white !important;
    border-radius: 50px !important;
    font-weight: 700 !important;
    font-size: 17px !important;
    height: 60px !important;
    width: 100% !important;
    border: none !important;
    letter-spacing: 0.05em !important;
}
[data-testid="stBaseButton-primary"]:hover { background-color: #333 !important; }
[data-testid="stBaseButton-primary"]:disabled { background-color: #aaa !important; cursor: not-allowed !important; }

/* ── Demo-data checkbox ── */
[data-testid="stCheckbox"] label p {
    font-size: 15px !important;
    font-weight: 500 !important;
    color: #1a1a1a !important;
}

/* ── Bottom bar startscherm (roze) ── */
[data-testid="stBottom"] { background-color: #f0d4d4 !important; }
[data-testid="stBottomBlockContainer"] { background-color: #f0d4d4 !important; }
</style>
"""

# ─────────────────────────────────────────────
# CSS — Hoofdscherm
# ─────────────────────────────────────────────

MAIN_CSS = """
<style>
@import url('https://api.fontshare.com/v2/css?f[]=general-sans@400,500,600,700&display=swap');

[data-testid="stApp"]      { background-color: #f0d4d4; font-family: 'General Sans', sans-serif; }
[data-testid="stHeader"]   { background-color: #fae8e8 !important; z-index: 998 !important; }
[data-testid="stToolbar"]  { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stSidebarCollapsedControl"] { display: none; }
.block-container           { padding-top: 0 !important; max-width: 1100px; margin: 0 auto; }

/* ── Sticky header-rij ── */
div.block-container > [data-testid="stVerticalBlock"] > div:has(> [data-testid="stHorizontalBlock"]) {
    background-color: #fae8e8 !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 9999 !important;
    box-shadow: 0 2px 8px rgba(200,120,100,0.10), 0 0 0 100vmax #fae8e8 !important;
    clip-path: inset(-8px -100vmax) !important;
}

/* ── Witte card ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: white !important;
    border-radius: 20px !important;
    border: none !important;
    box-shadow: 0 4px 32px rgba(180,100,90,0.13);
    padding: 4px 8px !important;
}

/* ── Terug-knop ── */
div.nav-terug button {
    background: transparent !important;
    border: none !important;
    color: #888 !important;
    font-size: 13px !important;
    box-shadow: none !important;
}
div.nav-terug button:hover { color: #1a1a1a !important; }

/* ── Primaire knoppen (zwart) ── */
button[kind="primary"],
[data-testid="stBaseButton-primary"] {
    background-color: #1a1a1a !important;
    color: white !important;
    border-radius: 50px !important;
    font-weight: 700 !important;
    letter-spacing: 0.07em !important;
    border: none !important;
    font-size: 13px !important;
}

/* ── Download-knop ── */
[data-testid="stDownloadButton"] button {
    background-color: #1a1a1a !important;
    color: white !important;
    border-radius: 50px !important;
    border: none !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    letter-spacing: 0.07em !important;
    white-space: nowrap !important;
}

/* ── Slider-accent ── */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background-color: #c8785a !important;
    border-color: #c8785a !important;
}

/* ── Bottom bar (lichtroze) ── */
[data-testid="stBottom"]               { background-color: #fae8e8 !important; }
[data-testid="stBottomBlockContainer"] { background-color: #fae8e8 !important; }
</style>
"""
