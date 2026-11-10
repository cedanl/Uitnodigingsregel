# Resultaten lezen

De app levert twee dingen op: een ranglijst van studenten en een rapport over de kwaliteit van de modellen. Lees eerst het rapport. Dat bepaalt of je de ranglijst kunt gebruiken en van welk model.

## De ranglijst

Per model krijg je een lijst met drie kolommen:

| Kolom | Betekenis |
|---|---|
| `ranking` | Plaats in de lijst. Nummer 1 heeft volgens het model het hoogste risico op uitval. |
| `Studentnummer` | De student, in de identificatiekolom uit je eigen bestand. |
| `voorspelling` | De uitkomst van het model waarop de volgorde is gebaseerd. Hoger betekent meer risico. |

De score is geen exacte kans op uitval. Vergelijk scores niet tussen modellen en gebruik de volgorde, niet het getal.

De methode nodigt studenten uit vanaf de bovenkant van de lijst. Hoeveel studenten je uitnodigt, bepaal je zelf op basis van het rapport en de beschikbare begeleidingstijd.

## De drie modellen

De app traint drie modellen op dezelfde data: Random Forest, Lasso en SVM (Support Vector Machine). Ze leggen op verschillende manieren verbanden tussen de kenmerken van studenten en uitval. Welk model het best werkt, verschilt per instelling en per dataset. Het rapport wijst het model aan dat op jouw data het best presteert.

## Het rapport

Het rapport beschrijft de trainingsdata van je analyse. Bovenaan staat op welk bestand het gebaseerd is en hoeveel studenten dat bestand bevat. Controleer die regel.

**Hoe de kwaliteit gemeten wordt**

Het rapport zet 20% van de trainingsdata apart, traint de modellen op de overige 80% en kijkt hoe goed ze de uitval in die 20% voorspellen. Van die studenten is de werkelijke uitkomst bekend. De modellen in het rapport zijn daarom niet dezelfde als die van de ranglijst, die op alle trainingsdata zijn getraind.

**Twee maten**

| Maat | Vraag die hij beantwoordt |
|---|---|
| Precisie | Welk deel van de uitgenodigde studenten valt werkelijk uit? |
| Recall | Welk deel van alle uitvallers zit bij de uitgenodigde studenten? |

Nodig je meer studenten uit, dan stijgt de recall en daalt de precisie meestal.

**Het stoplicht**

Het rapport beoordeelt elk model bij een uitnodiging van de bovenste 20% van de lijst:

| Kleur | Voorwaarde | Betekenis |
|---|---|---|
| 🟢 Betrouwbaar | Precisie en recall beide 40% of hoger | Bruikbaar voor gerichte uitnodigingen. |
| 🟡 Gebruik met voorzichtigheid | Precisie en recall beide 30% of hoger | Het model geeft een matig signaal. |
| 🔴 Niet bruikbaar | Lager | Gebruik de ranglijst niet. Het rapport noemt wat je aan de data kunt controleren. |

**Het aantal uit te nodigen studenten kiezen**

De precisie- en recallgrafieken in het rapport laten per percentage uitgenodigde studenten zien wat je kunt verwachten. Kies het percentage waarbij de recall hoog genoeg is voor je doel en het aantal gesprekken past bij de beschikbare begeleiding.

**Overige onderdelen**

- Datakwaliteit: aantallen en ontbrekende waarden per kolom.
- Belangrijkste kenmerken per model: welke kenmerken het zwaarst wegen in de voorspelling. Dit zijn verbanden in de data, geen oorzaken van uitval.

## Uitgangspunten bij gebruik

- Een plaats in de ranglijst is een signaal voor een gesprek, geen oordeel over de student en geen verklaring voor uitval.
- De begeleider beslist. Het model neemt geen beslissingen.
- Deel uitkomsten alleen met direct betrokken begeleiders.
- Gebruik het model niet voor selectie, uitsluiting of geautomatiseerde beslissingen.

Voor invoering binnen een instelling zijn een DPIA, een ethische toetsing en een toetsing aan de AI-verordening nodig. De [Datacoalitie Datagedreven Onderzoek](https://datagedrevenonderzoekmbo.nl/themas/voorspelmodel) heeft hiervoor hulpmiddelen.
