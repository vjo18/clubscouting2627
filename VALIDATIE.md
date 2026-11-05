# Validatie · 5 november 2026

Geslaagd:

- 11 Python-tests voor beperkte en volledige wedstrijdbladen, automatische spelerkoppeling binnen een club, competitiefilter, minutenpercentages, rugnummers en geboortejarenimport.
- 10 Node-tests voor de 49 exacte ploegkalenders, selectie van competitiewedstrijden, deduplicatie, behoud van scores en de jonge/ervaren weinigminutenfilters.
- Een echt volledig wedstrijdblad: keeperrood op minuut 45 = 45 minuten, basisuitwisseling op 68 = 68 minuten, invaller op 68 = 22 minuten, ongebruikte reservekeeper = 0 minuten. Teamsommen 945 en 990.
- Een ongescheiden reservenlijst wordt niet als basiself geïnterpreteerd.
- Vier selecties met 90, 30, 0 en 0 minuten geven 120/360 = 33,3%.
- Rugnummers houden zowel hun aantallen als de koppeling met iedere selectie.
- Onbekende leeftijd, onbekende minuten en geen selectie worden niet ten onrechte als weinig minuten ingedeeld.
- CSV-import ondersteunt het bestaande MacroDroid-formaat, slaat onbekende spelers over, is herhaalbaar en overschrijft geen conflicterende geboortejaren.
- Runtimecontrole van de interface met een testdocument: laden, paginering, jonge weinigminutenfilter, spelersfiche en de export van alle ontbrekende geboortejaren.
- Syntaxiscontrole en geslaagde GitHub-controleworkflow.

Broncontrole:

- De eerste grote inlezing voor alle 13 clubs en 49 ploegen wordt apart gevolgd via Update clubdata.
- Volledige seizoensdekking wordt niet aangenomen: gevonden uitslagen, geïmporteerde bladen, nog niet ingelezen ploegen en bronwaarschuwingen zijn zichtbaar.
- De minuutberekening geldt alleen voor ploegen met minutes_enabled=true en een expliciete, consistent verwerkte volledige opstelling.
- Een visuele browsertest is niet afgerond in de lokale omgeving; de interactielogica is wel getoetst.
