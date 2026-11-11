# Je data aanleveren

De Uitnodigingsregel werkt met twee bestanden:

| Bestand | Inhoud |
|---|---|
| Trainingsdata | Studenten uit eerdere cohorten, van wie bekend is of ze zijn uitgevallen. Hierop leren de modellen. |
| Predictiedata | De huidige studenten, voor wie je een ranglijst wilt. |

SQL-voorbeeldcode om deze bestanden uit je studentinformatiesysteem te halen staat in de repository [Uitnodigingsregel_datapreparatie](https://github.com/cedanl/Uitnodigingsregel_datapreparatie). De definities van de gebruikelijke variabelen staan in de [data dictionary](Variabelen_Definities_v4.xlsx).

## Eisen aan de bestanden

**Bestandsformaat**

- CSV met de kolomnamen op de eerste regel en één student per regel.
- Scheidingsteken: tab, puntkomma, komma of verticale streep. Het scheidingsteken wordt herkend.
- Decimalen met punt of komma. Een decimale komma kan alleen als het scheidingsteken geen komma is.
- Een export uit Excel als "CSV UTF-8" of "CSV (gescheiden door lijstscheidingsteken)" werkt.

**Verplichte kolommen**

| Kolom | Trainingsdata | Predictiedata |
|---|---|---|
| Een kolom die de student identificeert. Standaard heet die `Studentnummer`. | Verplicht | Verplicht |
| `Dropout` | Verplicht: `1` voor uitgevallen, `0` voor niet uitgevallen. Geen lege cellen. Beide waarden moeten voorkomen. | Mag ontbreken. De kolom wordt dan aangevuld met `0`. |

De namen van beide kolommen zijn instelbaar. Heten ze bij jou anders, pas dan `studentnumber_column` en `dropout_column` aan in `src/uitnodigingsregel/metadata/config.yaml`.

De identificatie mag elke waarde zijn waarmee je de student terugvindt: een studentnummer, een ander nummer of een code met letters. De modellen gebruiken deze kolom niet als kenmerk.

**Overige kolommen**

- Alle overige kolommen gebruikt het model als kenmerken van de student, zoals leeftijd, vooropleiding en verzuim.
- Trainings- en predictiedata moeten dezelfde kolommen hebben.
- Minstens één kenmerk moet een getal zijn.
- Kolommen met tekst, zoals een opleidingsnaam, worden omgezet naar een aparte 0/1-kolom per waarde.
- Lege cellen in getalkolommen worden aangevuld op basis van de meest vergelijkbare studenten.
- Dubbele regels worden verwijderd.
- Kolommen die in de trainingsdata voor iedere student dezelfde waarde hebben, worden niet gebruikt.

Laat kolommen weg die je niet als kenmerk wilt gebruiken, zoals naam of e-mailadres.

## Voorbeeld

De eerste kolommen van de demo-data (`data/01-raw/demo/synth_data_train.csv`):

| Studentnummer | StudentAge | Dropout | Aanmel_aantal | max1studie | VooroplNiveau_HAVO | … |
|---|---|---|---|---|---|---|
| 419335 | 16 | 0 | 1.0 | 1.0 | 1 | … |
| 387679 | 15 | 0 | 1.0 | 0.0 | 0 | … |

## Meldingen bij het inlezen

Voldoet een bestand niet aan de eisen, dan stopt de app vóór het trainen met een melding die zegt wat er mis is en welke kolommen het betreft.

| Melding | Oorzaak |
|---|---|
| "ontbreekt de kolom …" | De identificatiekolom of `Dropout` staat niet in het bestand, of het scheidingsteken is niet herkend. De melding toont de gevonden kolommen. |
| "mag alleen 0 en 1 bevatten" | `Dropout` bevat andere waarden of lege cellen. |
| "moeten dezelfde kolommen hebben" | Een kolom staat maar in één van de twee bestanden. |
| "geen kolommen met getallen" | Getallen zijn als tekst opgeslagen, bijvoorbeeld met een eenheid erachter. |

## Privacy

De app draait op je eigen computer. De bestanden die je uploadt worden niet naar een server gestuurd. Voor het rapport schrijft de app de trainingsdata naar een tijdelijk bestand, dat na het maken van het rapport wordt verwijderd.

Uitzondering: is de optionele koppeling met EduPlan ingesteld (`EDUPLAN_BACKEND_URL`), dan stuurt de app de gegevens van een student naar die dienst zodra je die student in de ranglijst selecteert.
