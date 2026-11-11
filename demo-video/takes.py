"""Declarative description of the demo video: title cards, takes and their order.

Each take is a list of (action, arguments) steps that record.py executes.
Targets are tried in order; the first one with a usable bounding box wins.
"""

from common import ROOT

REPORT_URL = f"file://{ROOT / 'Model_analysis.html'}"

CHECKBOX_DEMO = {"css": '[data-testid="stCheckbox"]', "nth": 0}
CHECKBOX_AGREE = {"text": "Ik werk volgens deze uitgangspunten."}
BUTTON_START = {"role": "button", "name": "Start analyse"}
TABLE = {"css": '[data-testid="stDataFrame"]'}

CARDS = {
    "intro": {
        "eyebrow": "CEDA · Npuls",
        "titel": "De Uitnodigingsregel",
        "sub": "Welke studenten nodig je als eerste uit voor een gesprek?",
    },
    "k1": {
        "eyebrow": "Stap 1",
        "titel": "Analyse starten",
        "sub": "Data kiezen, uitgangspunten bevestigen, modellen trainen",
    },
    "k2": {
        "eyebrow": "Stap 2",
        "titel": "De ranglijst lezen",
        "sub": "Drie modellen, elk met een eigen volgorde",
    },
    "k3": {
        "eyebrow": "Stap 3",
        "titel": "De modelkwaliteit beoordelen",
        "sub": "Het rapport laat zien of de voorspellingen bruikbaar zijn",
    },
    "k4": {
        "eyebrow": "Stap 4",
        "titel": "Resultaten downloaden",
        "sub": "Een bestand per model",
    },
    "outro": {
        "eyebrow": "Zelf proberen",
        "titel": "github.com/cedanl/Uitnodigingsregel",
        "sub": "Installatie en uitleg staan in de README en de documentatie",
    },
}
CARD_FOOTER = "Opgenomen met Playwright op synthetische demo-data · geen echte studentgegevens"

TAKE_START = [
    ("goto", {"url": "app"}),
    (
        "sub",
        {"text": "De app draait op je eigen computer. Studentgegevens verlaten je machine niet."},
    ),
    ("wait", {"s": 3.2}),
    (
        "sub",
        {
            "text": "Kies de meegeleverde demo-data, of upload je eigen trainings- en predictiebestand."
        },
    ),
    (
        "annotate",
        {
            "id": "a1_data",
            "targets": [CHECKBOX_DEMO, {"text": "Gebruik synthetische demo-data"}],
            "label": "1 · Data kiezen",
            "text": "Demo-data staat aan. Vink uit om twee eigen CSV-bestanden te uploaden.",
            "kleur": "blauw",
            "hold": 4.2,
        },
    ),
    (
        "sub",
        {
            "text": "De uitkomst is een signaal voor de begeleider. Het is geen oordeel over de student."
        },
    ),
    (
        "annotate",
        {
            "id": "a2_uitgangspunten",
            "targets": [{"text": "We zetten De Uitnodigingsregel in als ondersteuning"}],
            "label": "2 · Uitgangspunten",
            "text": "Een kans is geen garantie en zegt niets over de oorzaak. De mens beslist.",
            "kleur": "oranje",
            "hold": 4.6,
        },
    ),
    ("click", {"target": CHECKBOX_AGREE}),
    ("sub", {"text": "Pas na het bevestigen van de uitgangspunten kun je de analyse starten."}),
    (
        "annotate",
        {
            "id": "a3_start",
            "targets": [BUTTON_START],
            "label": "3 · Start analyse",
            "text": "De knop is actief zodra de uitgangspunten zijn aangevinkt.",
            "kleur": "blauw",
            "hold": 3.4,
        },
    ),
    ("click", {"target": BUTTON_START, "settle": False}),
    (
        "sub",
        {
            "text": "De app traint drie modellen op de trainingsdata. Met de demo-data duurt dat ongeveer een kwartminuut.",
            "pos": "boven",
        },
    ),
    ("wait", {"s": 1.2}),
    (
        "annotate",
        {
            "id": "a4_trainen",
            "targets": [{"css": '[data-testid="stSpinner"]'}, {"text": "Modellen trainen"}],
            "label": "Trainen",
            "text": "Met eigen data kan dit enkele minuten duren. Daarna worden de modellen hergebruikt.",
            "kleur": "oranje",
            "hold": 4.4,
        },
    ),
    ("wait", {"s": 1.5}),
    ("cut_start", {}),
    ("wait_for", {"text": "Resultaten", "timeout": 240}),
    ("cut_end", {}),
    ("sub", {"text": "Na het trainen staat de ranglijst klaar."}),
    (
        "annotate",
        {
            "id": "a5_klaar",
            "targets": [{"text": "Uitnodigingsregel — Resultaten"}],
            "label": "Klaar",
            "text": "150 studenten uit de predictiedata zijn gerangschikt.",
            "kleur": "groen",
            "hold": 3.4,
            "chip": "onder",
        },
    ),
]

TAKE_RANKING = [
    ("goto", {"url": "app"}),
    ("open_results", {}),
    ("marker", {"terug": 0.6}),
    (
        "sub",
        {
            "text": "De ranglijst zet de studenten met de hoogste voorspelde kans op uitval bovenaan."
        },
    ),
    ("scroll", {"px": 250}),
    (
        "annotate",
        {
            "id": "b1_tabel",
            "targets": [TABLE],
            "label": "1 · Ranglijst",
            "text": "Elke regel is een student. Nummer 1 nodig je als eerste uit.",
            "kleur": "blauw",
            "hold": 4.2,
            "chip": "onder",
        },
    ),
    (
        "sub",
        {
            "text": "De kolom voorspelling is een score om te rangschikken. Lees hem niet als percentage."
        },
    ),
    (
        "annotate",
        {
            "id": "b2_voorspelling",
            "targets": [dict(TABLE, sub=[0.675, 0.0, 1.0, 1.0])],
            "label": "2 · Voorspelling",
            "text": "Hoger betekent eerder uitnodigen. De waarde zelf is geen kans op uitval.",
            "kleur": "oranje",
            "hold": 4.6,
        },
    ),
    (
        "sub",
        {
            "text": "De identificatie staat erbij om de student terug te vinden. Het model gebruikt hem niet."
        },
    ),
    (
        "annotate",
        {
            "id": "b3_id",
            "targets": [dict(TABLE, sub=[0.33, 0.0, 0.675, 1.0])],
            "label": "3 · Identificatie",
            "text": "Een studentnummer of een andere code. Telt niet mee in de voorspelling.",
            "kleur": "blauw",
            "hold": 4.4,
        },
    ),
    ("sub", {"text": "Er zijn drie modellen. Elk model geeft een eigen volgorde."}),
    (
        "annotate",
        {
            "id": "b4_tabs",
            "targets": [{"css": '[data-baseweb="tab-list"]', "sub": [0.0, 0.0, 0.3, 1.0]}],
            "label": "4 · Drie modellen",
            "text": "Random Forest, Lasso en SVM. Het rapport laat zien welke het best presteert.",
            "kleur": "blauw",
            "hold": 4.2,
        },
    ),
    ("click", {"target": {"role": "tab", "name": "Lasso"}}),
    (
        "sub",
        {
            "text": "Niet elk model vindt een verband. Op de demo-data geeft Lasso elke student dezelfde score."
        },
    ),
    (
        "annotate",
        {
            "id": "b5_lasso",
            "targets": [dict(TABLE, nth_visible=True, sub=[0.0, 0.0, 1.0, 0.42])],
            "label": "5 · Let op",
            "text": "Gelijke scores geven geen rangorde. Controleer daarom eerst het rapport.",
            "kleur": "rood",
            "hold": 4.4,
        },
    ),
]

TAKE_REPORT = [
    ("goto", {"url": "app"}),
    ("open_results", {}),
    ("marker", {"terug": 0.6}),
    (
        "sub",
        {
            "text": "Voordat je de ranglijst gebruikt, wil je weten hoe goed de modellen voorspellen."
        },
    ),
    (
        "annotate",
        {
            "id": "c1_knop",
            "targets": [{"role": "button", "name": "Genereer rapport"}],
            "label": "1 · Genereer rapport",
            "text": "Het rapport gaat over de data waarmee je de analyse hebt gestart.",
            "kleur": "blauw",
            "hold": 3.8,
        },
    ),
    ("click", {"target": {"role": "button", "name": "Genereer rapport"}, "settle": False}),
    (
        "sub",
        {
            "text": "Voor het rapport is Quarto nodig. Zonder Quarto werkt de ranglijst wel, het rapport niet."
        },
    ),
    ("wait", {"s": 1.0}),
    (
        "annotate",
        {
            "id": "c2_quarto",
            "targets": [{"css": '[data-testid="stSpinner"]'}, {"text": "Rapport genereren"}],
            "label": "Vereist: Quarto",
            "text": "Quarto installeer je apart. Het rapport maken duurt even: de modellen worden opnieuw getraind.",
            "kleur": "rood",
            "hold": 4.8,
        },
    ),
    (
        "sub",
        {
            "text": "Het rapport traint de modellen op 80 procent van de data en toetst ze op de overige 20 procent."
        },
    ),
    ("wait", {"s": 5.5}),
    ("sub", {"text": "Zo zie je hoe de modellen presteren op studenten die ze nog niet kenden."}),
    ("wait", {"s": 4.5}),
    ("cut_start", {}),
    ("wait_for", {"text": "Download rapport", "timeout": 240}),
    ("cut_end", {}),
    ("sub", {"text": "Het rapport is een HTML-bestand. Je opent het in je browser."}),
    (
        "annotate",
        {
            "id": "c3_download",
            "targets": [{"role": "button", "name": "Download rapport"}],
            "label": "2 · Download rapport",
            "text": "Het bestand staat op je eigen computer en is te delen met collega's.",
            "kleur": "groen",
            "hold": 3.8,
        },
    ),
    ("goto", {"url": REPORT_URL, "settle": False}),
    ("wait", {"s": 1.2}),
    (
        "sub",
        {
            "text": "Bovenaan staat een stoplicht: groen, geel of rood. Rood betekent: gebruik de ranglijst niet."
        },
    ),
    (
        "annotate",
        {
            "id": "c4_stoplicht",
            "targets": [{"text": "Niet bruikbaar"}],
            "label": "3 · Stoplicht",
            "text": "De demo-data is willekeurig gegenereerd. Daarom staat het stoplicht hier op rood.",
            "kleur": "rood",
            "hold": 5.2,
        },
    ),
    (
        "sub",
        {
            "text": "Precisie: welk deel van de uitgenodigde studenten valt uit. Recall: welk deel van de uitvallers nodig je uit."
        },
    ),
    (
        "annotate",
        {
            "id": "c5_prestaties",
            "targets": [
                {"css": "p:has-text('Prestaties van het aanbevolen model')"},
                {"text": "Prestaties van het aanbevolen model"},
            ],
            "label": "4 · Precisie en recall",
            "text": "Gemeten bij 20 procent uitgenodigde studenten. Groen vanaf 40 procent op beide.",
            "kleur": "blauw",
            "hold": 5.6,
        },
    ),
    (
        "sub",
        {"text": "Verderop staan de details per model en de kenmerken die het zwaarst meewegen."},
    ),
    ("scroll", {"px": 1250, "steps": 60}),
    ("wait", {"s": 0.8}),
    (
        "annotate",
        {
            "id": "c6_details",
            "targets": [{"text": "Prestaties bij Verschillende Uitnodigingspercentages"}],
            "label": "5 · Per model",
            "text": "Precisie en recall bij verschillende uitnodigingspercentages.",
            "kleur": "blauw",
            "hold": 4.0,
        },
    ),
]

TAKE_DOWNLOAD = [
    ("goto", {"url": "app"}),
    ("open_results", {}),
    ("marker", {"terug": 0.6}),
    ("sub", {"text": "Onderaan download je de ranglijst als CSV-bestand, een per model."}),
    ("scroll", {"px": 520, "steps": 34}),
    ("wait", {"s": 0.5}),
    (
        "annotate",
        {
            "id": "d1_downloads",
            "targets": [{"css": '[data-testid="stDownloadButton"]', "nth": 0}],
            "label": "1 · Downloaden",
            "text": "Het bestand bevat ranking, identificatie en voorspelling.",
            "kleur": "blauw",
            "hold": 4.0,
            "chip": "boven",
        },
    ),
    (
        "click",
        {"target": {"css": '[data-testid="stDownloadButton"] button', "nth": 0}, "download": True},
    ),
    (
        "sub",
        {
            "text": "Het bestand open je in Excel of deel je met de begeleiders die de gesprekken voeren."
        },
    ),
    (
        "annotate",
        {
            "id": "d2_alle",
            "targets": [
                {"css": '[data-testid="stHorizontalBlock"]:has([data-testid="stDownloadButton"])'}
            ],
            "label": "2 · Een bestand per model",
            "text": "Gebruik het bestand van het model dat het rapport aanbeveelt.",
            "kleur": "groen",
            "hold": 4.2,
        },
    ),
    ("sub", {"text": "Deel de uitkomsten alleen met direct betrokken begeleiders."}),
    ("scroll_top", {}),
    (
        "annotate",
        {
            "id": "d3_terug",
            "targets": [{"role": "button", "name": "Terug"}],
            "label": "Opnieuw",
            "text": "Met Terug start je een analyse op andere data.",
            "kleur": "blauw",
            "hold": 3.4,
        },
    ),
]

TAKES = {
    "start": TAKE_START,
    "ranking": TAKE_RANKING,
    "report": TAKE_REPORT,
    "download": TAKE_DOWNLOAD,
}

# Takes that must start without stored models, so the recording shows training.
TAKES_WITHOUT_MODELS = {"start"}

SEQUENCE = [
    ("card", "intro"),
    ("card", "k1"),
    ("take", "start"),
    ("card", "k2"),
    ("take", "ranking"),
    ("card", "k3"),
    ("take", "report"),
    ("card", "k4"),
    ("take", "download"),
    ("card", "outro"),
]
