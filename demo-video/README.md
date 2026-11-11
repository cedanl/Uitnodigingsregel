# Demo-video

Scripts voor de video in de README. De video wordt opgenomen in een browser zonder venster en daarna voorzien van markeringen en ondertitels.

| Bestand | Doet |
|---|---|
| `takes.py` | Beschrijft de titelkaarten en de stappen per opname, inclusief alle teksten |
| `record.py` | Neemt de opnames op en legt per markering de positie van het element vast |
| `overlays.py` | Maakt de titelkaarten, markeringen en ondertitels als afbeelding |
| `compose.py` | Voegt alles samen tot twee video's: zonder en met markeringen |
| `verify.py` | Controleert of elke markering en ondertitel op zijn tijdstip in beeld is |

## Opnieuw maken

Nodig: `ffmpeg`, Quarto en de Python-pakketten `playwright` en `pillow` (`uv pip install playwright pillow`, daarna `uv run playwright install chromium`).

1. Start de app in een eerste terminal: `uv run uitnodigingsregel`
2. Voer in een tweede terminal, vanuit de map `demo-video`, de scripts in deze volgorde uit: `record.py`, `overlays.py`, `compose.py`, `verify.py`.

Wijzig je alleen teksten in `takes.py`, dan is opnieuw opnemen niet nodig. Begin dan bij `overlays.py`.

De opname gebruikt de synthetische demo-data en traint de modellen in `models/` opnieuw.

## Publiceren

GitHub speelt een video alleen in de README af als het adres begint met `https://github.com/user-attachments/assets/`. Zo'n adres ontstaat door het bestand in de browser te uploaden:

1. Open een issue in deze repository en scrol naar het tekstvak onder "Add a comment".
2. Sleep `uitnodigingsregel-showcase-highlighted.mp4` in dat tekstvak.
3. Wacht tot er een regel verschijnt die begint met `https://github.com/user-attachments/assets/` en klik op "Comment".
4. Zet dat adres op een eigen regel in `README.md`, onder het kopje "Demo".

De documentatiesite gebruikt het bestand bij de release `demo-videos`. Werk dat bij met:

```
gh release upload demo-videos uitnodigingsregel-showcase-highlighted.mp4 uitnodigingsregel-showcase.mp4 --clobber
```
