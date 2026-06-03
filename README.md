# Uitnodigingsregel

Python implementatie van de Uitnodigingsregel — een machine learning model dat studenten met een verhoogd uitvalrisico signaleert. Bedoeld voor data scientists en developers die het model opzetten en beheren binnen hun onderwijsinstelling.

# Waarom de Uitnodigingsregel
Onderwijsinstellingen worstelen al jaren om meer grip op uitval te krijgen. Steeds vaker wordt hierbij gebruikgemaakt van data over de studieontwikkeling van studenten.

In haar promotieonderzoek introduceerde [Irene Eegdeman](https://www.linkedin.com/in/irene-eegdeman-1b0a6b25) een methode om studenten met een verhoogd risico op uitval
vroegtijdig te signaleren. Met behulp van studiedata en machine learning-modellen is de zogenaamde 'uitnodigingsregel' ontwikkeld.
Deze methode biedt SLB'ers en mentoren een signaleringssysteem om uitvalpreventie en -interventies effectiever in te zetten.

De methodiek genereert een geordende lijst van studenten op basis van hun uitvalkans. Zie een concreet voorbeeld met synthetische data bij ROC Mondriaan.

<img src="references/Afbeelding1.png" width="400">


## Achtergrond
Wil je meer weten over de Uitnodigingsregel? Bekijk dan [deze presentatie](https://datagedrevenonderzoekmbo.nl/wp-content/uploads/2023/09/Presentatie-MBO-Digitaal.pdf) van de MBO Digitaal-conferentie, waarin de belangrijkste resultaten, geleerde lessen en praktische tips worden gedeeld. Daarnaast geeft deze [praatplaat](https://datagedrevenonderzoekmbo.nl/wp-content/uploads/2023/09/Praatplaat-Methode-EegdemanV2-1-scaled.jpg) een visueel overzicht van de methode.

Meer informatie over het voorkomen van studentenuitval door middel van verklaringen en voorspellingen is te vinden in [dit artikel](https://www.onderwijskennis.nl/kennisbank/studentenuitval-voorkomen-door-verklaren-en-voorspellen). Voor de wetenschappelijke basis achter de methode kun je het [proefschrift van Irene Eegdeman](https://research.vu.nl/en/publications/enhancing-study-success-in-dutch-vocational-education) raadplegen.

Wil je de Uitnodigingsregel toepassen binnen jouw onderwijsinstelling? Houd dan rekening met een uitgebreide voorbereiding, waaronder een DPIA (Data Protection Impact Assessment) maar ook ethische toetsing en toetsing aan de AI-verordening. De Datacoalitie Datagedreven Onderzoek heeft deze methodiek zorgvuldig naar de praktijk vertaald. Lees [hier meer](https://datagedrevenonderzoekmbo.nl/themas/voorspelmodel) over dit proces en bekijk de [ontwikkelde producten](https://datagedrevenonderzoekmbo.nl/themas/voorspelmodel/praktijkpilot-de-uitnodigingsregel) die kunnen helpen bij een succesvolle implementatie van de Uitnodigingsregel.


# Aan de slag

Volledige documentatie, pipeline-overzicht en projectstructuur: **[cedanl.github.io/Uitnodigingsregel](https://cedanl.github.io/Uitnodigingsregel/)**

## Datavoorbereiding

SQL-voorbeeldcode voor de invoerdata is beschikbaar via de [Uitnodigingsregel_datapreparatie](https://github.com/cedanl/Uitnodigingsregel_datapreparatie) repo. Zorg dat de voorbereide data aanwezig is in `data/02-prepared/` voordat je de pipeline draait. Of gebruik de synthetische demo-data.
Een overzicht van alle basis variabelen staat in de [data dictionary](docs/Variabelen_Definities_v4.xlsx).

## Installatie

### Via Scoop (Windows, aanbevolen)
Installeer [Scoop](https://scoop.sh) als je dat nog niet hebt, en voer daarna uit:
```powershell
scoop bucket add uitnodigingsregel https://github.com/cedanl/Uitnodigingsregel
scoop install uitnodigingsregel
uitnodigingsregel
```

### Handmatig (Windows, macOS, Linux)
1. Installeer [uv](https://docs.astral.sh/uv/getting-started/installation/):

   **Windows (PowerShell):**
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   **macOS / Linux:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone de repository:
   ```
   git clone https://github.com/cedanl/Uitnodigingsregel.git
   cd Uitnodigingsregel
   ```

3. Installeer dependencies:
   ```
   uv sync
   ```

## Gebruik

### 1 Datakwaliteit
Gebruik `Model_analysis.qmd` om een HTML-rapport te genereren voor datakwaliteit en modelprestaties:
```
uv run quarto render Model_analysis.qmd
```
Het HTML-bestand wordt aangemaakt in dezelfde map als het analysebestand.

### 2 Voorspellingen draaien
Draai de pipeline om een gerangschikte lijst van studenten te genereren:
```
uv run python main.py
```

### 3 Interactieve app
Start de Streamlit-app voor interactieve verkenning:
```
uv run uitnodigingsregel
```

### Outputbestanden
Na uitvoering worden de voorspellingsbestanden opgeslagen in `models/predictions/`.


## Contributors
Thank you to all the people who have already contributed to Uitnodigingsregel [[contributors](https://github.com/cedanl/Uitnodigingsregel/graphs/contributors)].

<a href="https://github.com/tin900"><img src="https://github.com/tin900.png" width="50" height="50" alt="tin900"></a>
<a href="https://github.com/MondriaanBI"><img src="https://github.com/MondriaanBI.png" width="50" height="50" alt="MondriaanBI"></a>
<a href="https://github.com/asewnandan"><img src="https://github.com/asewnandan.png" width="50" height="50" alt="asewnandan"></a>
<a href="https://github.com/StevenRamondt"><img src="https://github.com/StevenRamondt.png" width="50" height="50" alt="StevenRamondt"></a>


## Credits
This product was originally created with [Cookiecutter Data Science](https://github.com/drivendataorg/cookiecutter-data-science) and migrated to the [CEDA package standard](https://github.com/cedanl/.github/tree/main/standards).

--------
