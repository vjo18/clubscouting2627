# Clubscouting 2026–2027 · Ardooie

[Open het dashboard](https://vjo18.github.io/clubscouting2627/)

Het dashboard volgt de 13 clubs en 49 ploegen uit het aangeleverde overzicht. Ploegkalenders worden afgeleid van de ploeglink door `/overzicht` te vervangen door `/kalender`. De nieuw opgegeven U21-ploegen zijn inbegrepen. De configuratie staat in `config/clubs.json`.

## Alleen competitie

Alleen de per ploeg opgegeven competitie telt mee. Beker-, oefenwedstrijden en onbekende reeksen beïnvloeden de statistieken niet. Bij een herkenbare competitie-ID heeft die voorrang; anders wordt de exact opgegeven reeksnaam gebruikt. De kalender van de ploeg is de bron, niet de hele reeks. Dezelfde wedstrijd wordt één keer ingelezen, ook wanneer twee gevolgde ploegen elkaar treffen.

Dezelfde volledige naam binnen dezelfde club wordt automatisch als dezelfde speler behandeld. Hoofdletters, extra spaties en Unicode-opmaak worden gelijkgetrokken. Namen bij andere clubs blijven apart. Er is geen handmatige spelerkoppeling nodig.

## Selecties, minuten en rugnummers

Per ploeg toont het dashboard het aantal selecties en alle waargenomen rugnummers, met het aantal keer dat elk nummer voorkomt. In de spelersfiche vind je het rugnummer bij iedere selectie en een link naar het wedstrijdblad.

Bij de 25 ploegen waarvoor **Speelminuten = Ja** staat, verschijnen ook de speelminuten en het minutenpercentage:

**gespeelde minuten ÷ mogelijke minuten binnen de selecties × 100**

Voorbeeld: 4 selecties met 90, 30, 0 en 0 minuten geven 120 / 360 = 33,3%. Een ongebruikte bankplaats is dus één selectie met 0 minuten. Wedstrijden waarvoor de speler niet geselecteerd was, tellen niet mee in deze noemer.

De parser gebruikt een expliciete scheiding tussen de basiself en **Wisselspelers**, wisselminuten en rode kaarten. Hij gebruikt niet de eerste elf rugnummers van een ongescheiden spelerslijst. Een echte volledige wedstrijd is als testfixture opgenomen: 990 teamminuten voor Roeselare en 945 voor Merelbeke na een rode kaart op minuut 45. Toegevoegde tijd wordt voor het percentage niet bij de standaard 90 minuten geteld.

Als bij een ploeg met minutenregistratie niet alle selecties betrouwbaar berekenbaar zijn, verschijnt een minutencontrole in plaats van een misleidend percentage. Zo'n speler wordt niet als weinigspeler ingedeeld. Bij ploegen zonder minutenregistratie staan uitsluitend selecties en rugnummers; er is geen waarschuwing over ontbrekende minuten.

## Scoutingfilters

- **Jong: t.e.m. 20 jaar · weinig minuten**.
- **Ervaren: 23+ · weinig minuten**.
- De grens **minder dan x%** is aanpasbaar van 0 tot 100, standaard 25%.
- Kies of je vergelijkt bij de A-ploeg, alle ploegen met minutenregistratie of één specifieke ploeg.

Een speler moet een gekend geboortejaar, minstens één selectie bij de gekozen ploeg en een volledig berekenbaar percentage hebben. Geen selecties of ontbrekende minuten betekenen niet automatisch 0%. Leeftijd is kalenderjaar min geboortejaar en wordt met ≈ getoond. Dit is een benadering zolang we geen volledige geboortedatum kennen.

## Geboortejaren toevoegen zoals in scouting2627

1. Klik in het dashboard op **Ontbrekende geboortejaren**. Dit downloadt alle spelers zonder geboortejaar, over alle clubs, met `ClubRBFA;Naam;Geboortejaar`.
2. Vul de viercijferige geboortejaren in. Laat club en naam staan. Bewaar als CSV.
3. Open [de uploadmap](https://github.com/vjo18/clubscouting2627/tree/main/data_raw/birthyear_uploads), kies **Add file → Upload files** en gebruik telkens een nieuwe bestandsnaam. Commit op `main`.
4. De workflow **Verwerk geboortejaren** importeert de CSV, werkt `data_raw/birthyears.csv` en de spelersdata bij en start daarna **Publiceer dashboard**.
5. Vernieuw het dashboard na de groene publicatie. De ontbrekende lijst wordt korter en de leeftijdsfilters kunnen de toegevoegde spelers gebruiken.

Ook MacroDroid-resultaten met `Ploeg;Naam;Geboortejaar;Gevonden` zijn toegestaan. De ploegkolom kan de clubnaam uit de export of een eenduidige bronploegnaam bevatten. `Gevonden=false`, ongeldige jaren, onbekende club/speler-combinaties en dubbelzinnige clubnamen worden overgeslagen. De import koppelt altijd binnen een club, nooit wereldwijd op alleen de spelersnaam.

Een herhaalde upload maakt geen dubbele geboortejaren. Bij een tegenstrijdig jaar stopt de import zonder bestaande geboortejaren te overschrijven. De oude resultatenbestanden blijven bewaard. De optionele oude `player_identity.csv` dient uitsluitend voor compatibiliteit met eerder ingevoerde geboortejaren.

## Gegevens bijwerken en broncontrole

Open [Actions → Update clubdata](https://github.com/vjo18/clubscouting2627/actions/workflows/update.yml) en kies **Run workflow**. Configuratiewijzigingen starten ook een update; er is nog geen wekelijkse planning.

De collector gebruikt drie browserpagina's tegelijk. Oude, gecontroleerde verslagen worden hergebruikt; verslagen die nog geen volledige minutenparser hebben doorlopen, worden opnieuw opgehaald voor de ploegen met minutenregistratie. Met `npm run scrape -- --refresh-reports` kun je alle verslagen opnieuw bekijken.

De verwerking gebeurt eerst in een tijdelijke dataset. De gespeelde competitie, ploeg-IDs en score worden gecontroleerd. Bij een onbereikbare kalender of ontbrekend verslag blijven eerdere gegevens behouden. Andere succesvol verwerkte ploegen kunnen worden bijgewerkt; bronwaarschuwingen en ontbrekende eerste kalenders zijn zichtbaar in het dashboard. De dekking per ploeg toont hoeveel gevonden uitslagen daadwerkelijk verwerkt zijn. Dat bewijst nog geen volledige seizoensdekking.

Een geslaagde data- of geboortejarenworkflow publiceert automatisch via GitHub Pages. De publicatie haalt eerst de actuele main op, voegt de nieuwe brongegevens toe en berekent het dashboard opnieuw met de nieuwste code en geboortejaren. Wijzigt main tijdens het opslaan, dan wordt dit maximaal vier keer opnieuw geprobeerd zonder geforceerde push. Gegenereerde spelers-JSON wordt niet gerebased.

Vóór publicatie bewaart Update clubdata de brongegevens als het artifact **clubscout-brongegevens** (14 dagen), zodat een eventuele opslagfout geen volledige herscrape vereist. Een tijdelijk onvolledig geladen kalender met minder dan twee verschillende wedstrijden wordt geweigerd; eerdere gegevens blijven bewaard.

## Lokaal

Python 3.11+, Node 22+ en voor live scraping Chrome/Puppeteer; op Linux zonder desktop ook Xvfb.

```bash
npm install
npm test
npm run scrape
npm run dev
```

Open http://localhost:8000. Alleen opnieuw berekenen: `python3 -m clubscout.build`. Geboortejaren importeren zonder scrapen: `python3 scripts/import_birthyears.py`.

Een handmatig gerenderd HTML-bestand importeren:

```bash
python3 scripts/import_report.py /pad/naar/wedstrijd.html --source https://www.rbfa.be/nl/wedstrijd/7544599
python3 -m clubscout.build
```

Een scoutsignaal beschrijft de beschikbare gegevens. Het bewijst geen transferinteresse, blessure, officiële speelgerechtigdheid of reden voor niet-selectie.
