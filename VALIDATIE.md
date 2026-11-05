# Validatie · 5 november 2026

Geslaagd:

- 12 Python-tests voor beperkte en volledige wedstrijdbladen, automatische spelerkoppeling binnen een club, competitiefilter, minutenpercentages, rugnummers en geboortejarenimport.
- 10 Node-tests voor de 49 exacte ploegkalenders, selectie van competitiewedstrijden, deduplicatie, behoud van scores en de jonge/ervaren weinigminutenfilters.
- Een echt volledig wedstrijdblad: keeperrood op minuut 45 = 45 minuten, basisuitwisseling op 68 = 68 minuten, invaller op 68 = 22 minuten, ongebruikte reservekeeper = 0 minuten. Teamsommen 945 en 990.
- Een ongescheiden reservenlijst wordt niet als basiself geïnterpreteerd.
- Vier selecties met 90, 30, 0 en 0 minuten geven 120/360 = 33,3%.
- Rugnummers houden zowel hun aantallen als de koppeling met iedere selectie.
- Onbekende leeftijd, onbekende minuten en geen selectie worden niet ten onrechte als weinig minuten ingedeeld.
- CSV-import ondersteunt het bestaande MacroDroid-formaat, slaat onbekende spelers over, is herhaalbaar en overschrijft geen conflicterende geboortejaren.
- Runtimecontrole van de interface met een testdocument: laden, paginering, jonge weinigminutenfilter, spelersfiche en de export van alle ontbrekende geboortejaren.
- Integratietest van publicatie met een verouderde checkout, nieuwere geboortejaren en een extra wijziging precies vóór de push: opnieuw berekenen en herproberen behouden de actuele gegevens.
- Syntaxiscontrole en geslaagde GitHub-controleworkflow (22 tests).

Broncontrole:

- Update clubdata #7 is geslaagd, inclusief bronbackup, publicatie op actuele main en GitHub Pages. De gepubliceerde dataset bevatte 907 spelers en 269 geboortejaren. Drie kalenders en meerdere wedstrijdbladen hadden nog bronwaarschuwingen; dit is geen bewijs van volledige dekking.
- Een volgende aanvulronde probeert ontbrekende bronnen opnieuw. De actuele dekking staat in het dashboard.
- Volledige seizoensdekking wordt niet aangenomen: gevonden uitslagen, geïmporteerde bladen, nog niet ingelezen ploegen en bronwaarschuwingen zijn zichtbaar.
- De minuutberekening geldt alleen voor ploegen met minutes_enabled=true en een expliciete, consistent verwerkte volledige opstelling.
- Een visuele browsertest is niet afgerond in de lokale omgeving; de interactielogica is wel getoetst.
