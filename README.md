Studenten uitval voorspellen

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


# Student dropout model

## Project Structure

```
├── LICENSE
├── Makefile                     <- Convenience commands
├── README.md
├── main.py                      <- Pipeline entrypoint
├── Model_analysis.qmd           <- Quarto analysis report
├── config.yaml                  <- Root configuration
├── data/
│   ├── 01-raw/                  <- Original, immutable data
│   │   ├── demo/                <- Synthetic demo data (committed)
│   │   └── user_data/           <- User-provided data (gitignored)
│   ├── 02-prepared/             <- Standardized intermediate data
│   └── 03-output/               <- Processed datasets
├── models/                      <- Trained models (.joblib) and predictions
│   └── predictions/             <- Output files
├── reports/                     <- Generated analysis (HTML, figures)
│   └── figures/
├── src/uitnodigingsregel/       <- Installable Python package
│   ├── dataset.py               <- Data cleaning (deduplication, imputation)
│   ├── features.py              <- Feature engineering
│   ├── evaluate.py              <- Model evaluation and settings
│   ├── visualize.py             <- Plotting functions
│   ├── analyze.py               <- Analysis helpers
│   ├── modeling/
│   │   ├── train.py             <- Model training (RF, Lasso, SVM)
│   │   └── predict.py           <- Model prediction
│   └── metadata/
│       └── config.yaml          <- Hyperparameters and settings
├── app/                         <- Streamlit interactive app
│   ├── main.py
│   └── config.toml
├── tests/                       <- Unit tests
└── pyproject.toml               <- Project configuration
```

## Prerequisites
If you do not have a Python environment set up, follow these steps:
1. Install uv on your system:

- For Windows

Copy line below in Windows PowerShell
```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
Please refer to the official installation guide of [uv](https://docs.astral.sh/uv/getting-started/installation/) for other operating systems and more detailed information.

2. Clone the repository:

Download git if necessary: https://git-scm.com/downloads
```
git clone https://github.com/cedanl/Uitnodigingsregel.git

cd Uitnodigingsregel
```

3. Install dependencies:
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
uv run streamlit run app/main.py
```

### Output files
After execution, the generated prediction files will be saved in `models/predictions/`.


## Contributors
Thank you to all the people who have already contributed to Uitnodigingsregel [[contributors](https://github.com/cedanl/Uitnodigingsregel/graphs/contributors)].

[![](https://github.com/tin900.png?size=50)](https://github.com/tin900)
[![](https://github.com/MondriaanBI.png?size=50)](https://github.com/MondriaanBI)
[![](https://github.com/asewnandan.png?size=50)](https://github.com/asewnandan)
[![](https://github.com/StevenRamondt.png?size=50)](https://github.com/StevenRamondt)

## Credits
This product was originally created with [Cookiecutter Data Science](https://github.com/drivendataorg/cookiecutter-data-science) and migrated to the [CEDA package standard](https://github.com/cedanl/.github/tree/main/standards).

--------
