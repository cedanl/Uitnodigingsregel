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

### Via Scoop (Windows)
```powershell
scoop bucket add uitnodigingsregel https://github.com/cedanl/Uitnodigingsregel
scoop install uitnodigingsregel
uitnodigingsregel
```

### Handmatig
1. Installeer [uv](https://docs.astral.sh/uv/getting-started/installation/):
```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
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

## Use of program

### 1 Data quality
Use the `Model_analysis.qmd` file to create an HTML report to validate data quality and model performance.
```
uv sync
uv run quarto render Model_analysis.qmd
```
The HTML output file is created in the same folder as the analysis file.

### 2 Make predictions
Run the pipeline to generate ranked student predictions:
```
uv run python main.py
```

### 3 Interactive app
Launch the Streamlit app for interactive exploration:
```
uv run uitnodigingsregel
```

### Output files
After execution, the generated prediction files will be saved in `models/predictions/`.


## Contributors
Thank you to all the people who have already contributed to Uitnodigingsregel [[contributors](https://github.com/cedanl/Uitnodigingsregel/graphs/contributors)].

<a href="https://github.com/tin900"><img src="https://github.com/tin900.png" width="50" height="50" alt="tin900"></a>
<a href="https://github.com/MondriaanBI"><img src="https://github.com/MondriaanBI.png" width="50" height="50" alt="MondriaanBI"></a>
<a href="https://github.com/asewnandan"><img src="https://github.com/asewnandan.png" width="50" height="50" alt="asewnandan"></a>
<a href="https://github.com/StevenRamondt"><img src="https://github.com/StevenRamondt.png" width="50" height="50" alt="StevenRamondt"></a>


## Credits
This product was originally created with [Cookiecutter Data Science](https://github.com/drivendataorg/cookiecutter-data-science) and migrated to the [CEDA package standard](https://github.com/cedanl/.github/tree/main/standards).

--------
