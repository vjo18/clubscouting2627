# clubscouting2627

Clubgerichte scouting voor Ardooie, seizoen 2026–2027. Structuur: **club → ploegen → speler → wedstrijdbladen**. Een aparte repo naast [scouting2627](https://github.com/vjo18/scouting2627).

## Welke kalenders gebruiken we?

**Alleen de kalender van elke gevolgde ploeg.** De collector haalt geen volledige reekskalenders op. Een wedstrijd die bij twee gevolgde ploegen terugkomt, krijgt één genormaliseerde wedstrijd-URL en wordt één keer per run opgehaald. Alleen spelers van de geconfigureerde clubs en ploegen verschijnen in het dashboard.

| Club | Ploeg | RBFA-ploeg-ID | Kalender |
|---|---|---|---|
| Sportkring Roeselare | A | 360196 | [Ploegkalender](https://www.rbfa.be/nl/club/2656/ploeg/360196/kalender) |
| Sportkring Roeselare | Reserven | 360198 | [Ploegkalender](https://www.rbfa.be/nl/club/2656/ploeg/360198/kalender) |
| Sportkring Roeselare | U19 | 360199 | [Ploegkalender](https://www.rbfa.be/nl/club/2656/ploeg/360199/kalender) |
| KM Torhout | A | 364284 | [Ploegkalender](https://www.rbfa.be/nl/club/1185/ploeg/364284/kalender) |
| KM Torhout | B | 364282 | [Ploegkalender](https://www.rbfa.be/nl/club/1185/ploeg/364282/kalender) |
| KM Torhout | Reserven A | 364285 | [Ploegkalender](https://www.rbfa.be/nl/club/1185/ploeg/364285/kalender) |
| KM Torhout | U19 | 381025 | [Ploegkalender](https://www.rbfa.be/nl/club/1185/ploeg/381025/kalender) |

U21 is uitgesloten. Stamnummer, RBFA-club-ID en ploeg-ID zijn aparte gegevens: Torhout heeft stamnummer 00822, club-ID 1185 en meerdere ploeg-IDs. In het reserveverslag heet Res A ook **KM Torhout A**; ploeg-ID 364285 voorkomt verwarring met het eerste elftal.

De ploegkalender bevat ook beker- en oefenwedstrijden. **Alleen competitiewedstrijden tellen mee.** Per ploeg staat in `league_competitions` de exact goedgekeurde RBFA-reeksnaam. Onbekende of lege labels worden niet meegeteld. Deze filter geldt voor selecties, minuten, scoutsignalen, dekking, spelersfiches en CSV-export, ook voor eerder ingelezen verslagen. De overige ruwe verslagen blijven als bronarchief bewaard, maar beïnvloeden het dashboard niet.

## Eerste gegevens ophalen

Open [Actions → Update clubdata](https://github.com/vjo18/clubscouting2627/actions/workflows/update.yml) en klik **Run workflow** op `main`.

De workflow:

1. Controleert de code en ploegconfiguratie.
2. Leest de zeven ploegkalenders met Chromium/Puppeteer en opent de gevonden wedstrijdbladen met score.
3. Controleert ploeg-IDs en score; verwerkt de bladen eerst in een tijdelijke dataset.
4. Bouwt het cluboverzicht. Pas als alle gevonden bladen succesvol verwerkt zijn, worden de gegevens naar `main` gecommit.
5. Levert het downloadbare artifact **clubscout-dashboard** en diagnostiek.

Een wijziging aan `config/clubs.json` op `main` start ook een update. Er is nog geen wekelijkse planning. Bij een ontbrekend spelersblad, geblokkeerde pagina of tegenstrijdige score stopt de run en blijft de vorige opgeslagen dataset behouden. Bij een gelijktijdige wijziging aan `main` kan de niet-geforceerde push worden geweigerd; start de run dan opnieuw.

De ploegkalenders en wedstrijdbladen zijn via GitHub Actions ingelezen. Volledige seizoensdekking blijft afzonderlijk te controleren. De workflow **Controle en dashboard** heeft geen browser of live RBFA nodig.

## Dashboard openen

Het dashboard staat in `public/` en heeft geen frontend-build nodig:

```bash
python3 -m clubscout.build
python3 -m http.server 8000 --directory public
```

Open http://localhost:8000. Na een Actions-run kun je ook het artifact **clubscout-dashboard** downloaden, uitpakken en die map met `python3 -m http.server 8000` openen. Een rechtstreekse `file://`-opening werkt niet betrouwbaar vanwege het laden van JSON.

Voor een vaste weblink staat de workflow **Publiceer dashboard** klaar. Stel eenmalig bij **Settings → Pages → Build and deployment → Source** de optie **GitHub Actions** in. Open daarna **Actions → Publiceer dashboard → Run workflow** op `main`. Na een geslaagde deployment staat de link in het environment `github-pages`; de verwachte URL is https://vjo18.github.io/clubscouting2627/. Het dashboard is pas gepubliceerd zodra die deployment slaagt. Daarna publiceert een geslaagde **Update clubdata**-run het dashboard opnieuw. Het dashboard bevat zoeken, clubkeuze, selecties per ploeg, filters op meerdere ploegen en scoutsignalen, spelersfiches en CSV-export. Het dashboard gebruikt de ingelezen competitiewedstrijden van de zeven gevolgde ploegen.

## Selectie is niet hetzelfde als spelen

De oorspronkelijke scraper uit RBFA2627 bepaalt basisplaatsen met `homePlayerCount < 11` en `awayPlayerCount < 11`. Bij ontbrekende wissels kent hij die spelers 90 minuten toe. Dat is onjuist voor het aangeleverde reserveverslag: de spelers staan op rugnummer en zelfs de tweede Knokke-doelman staat tussen de eerste elf.

Deze versie leest daarom conservatief:

| Gegeven | Behandeling |
|---|---|
| Naam op wedstrijdblad | Selectie/vermelding |
| Eindscore | Letterlijk uit wedstrijdheader, gecontroleerd tegen de kalender |
| Ploeg | RBFA-club-ID en ploeg-ID uit bronlink |
| Doelman en kapitein | Letterlijke GK/C-markering |
| Kaarten | Geobserveerde markeringen met minuut; geen bewijs van speeltijd |
| Basis, bank, invalbeurt en minuten | Onbekend (`null`) |
| Goals per speler | Onbekend (`null`), geen nul door ontbrekende events |

De parser gebruikt voorlopig bij **alle** bladen deze veilige modus. Voor de analyse “reserve zit geregeld ongebruikt op de A-bank” is nog een betrouwbare volledige-verslagmodus nodig. Hiervoor is een representatieve A-/B-HTML met herkenbare scheiding tussen basis/bank en wissels nodig. Oude afgeleide minuten worden niet geïmporteerd.

## Dezelfde speler bij meerdere ploegen

Spelers met dezelfde volledige naam binnen dezelfde club worden **automatisch als dezelfde speler behandeld**, ongeacht bij welke gevolgde ploeg ze op het wedstrijdblad staan. Hoofdletters, extra spaties en Unicode-opmaak worden gelijkgetrokken; accenten en verschillende spellingen blijven onderscheiden. Dezelfde naam bij verschillende clubs blijft apart.

Je hoeft geen spelers handmatig te koppelen. Eén speler krijgt één rij met selecties per A-, B-, reserve- en U19-ploeg en een gezamenlijke spelersfiche. De filter **Bij meerdere ploegen** gebruikt deze automatische naamkoppeling. Ook geboortejaren zijn hiervoor niet verplicht. Dit is de gekozen koppelregel; de bron levert geen unieke speler-ID.

De interne speler-ID is `name:` gevolgd door de genormaliseerde volledige naam, bijvoorbeeld `name:jan janssens`. Bestaande handmatige IDs blijven alleen als alias bruikbaar voor eerder ingevulde geboortejaren. Tegenstrijdige geboortejaren worden niet overschreven.

Geboortejaren vul je in `data_raw/birthyears.csv` aan:

```csv
club_id;person_id;birth_year
torhout;name:jan janssens;2006
```

Onbekende en conflicterende geboortejaren blijven leeg. Er wordt geen exacte leeftijd verzonnen uit alleen een geboortejaar.

Scoutsignalen zijn beschrijvend:

- **Bij meerdere ploegen:** dezelfde speler op basis van club en naam staat op bladen van meerdere gevolgde ploegen.
- **Minstens 3 selecties elders en geen A-selectie in ingelezen data:** met waarschuwing de A-dekking te controleren.

Dit bewijst geen transferinteresse, blessure, officiële speelgerechtigdheid of structurele uitsluiting door de trainer.

## Dekking en gegevensbehoud

De interface toont per ploeg het aantal geïmporteerde bladen en, na een scrape, het aantal verwerkte gevonden uitslagen. Dat bewijst nog geen volledige seizoensdekking: onbekende filters, client-side laadproblemen of RBFA-beperkingen kunnen wedstrijden verbergen. De collector bewaart daarom eerder gevonden wedstrijden en markeert volledigheid als `unverified`.

De collector probeert zichtbare kalenderfilters en meer-laden/volgende-knoppen. Seizoenfilters worden niet doorlopen. Geen herkenbare wedstrijden of spelers betekent een fout. Scorewijzigingen vereisen controle; de collector overschrijft ze niet stilzwijgend. Bestaande verslagen worden hergebruikt na controle van ploeg-ID en kalenderscore. Met `npm run scrape -- --refresh-reports` kun je ze volledig opnieuw ophalen, bijvoorbeeld na een parserverbetering.

## Lokaal scrapen en testen

Python 3.11+ voor verwerking; Node 22+ voor scraping en Node-tests. Op Linux zonder desktop ook Xvfb.

```bash
npm install
npm test
npm run scrape
npm run dev
```

Een HTML-bestand kun je ook handmatig importeren:

```bash
python3 scripts/import_report.py /pad/naar/wedstrijd.html --source https://www.rbfa.be/nl/wedstrijd/7544599
python3 -m clubscout.build
```

Gebruik gerenderde HTML zoals het meegestuurde bestand, niet de lege Angular-paginabron. Hetzelfde bronadres vervangt hetzelfde verslag en wordt niet dubbel geteld.

## Bestanden

- `config/clubs.json`: de clubs, ploeg-IDs en kalenderlinks.
- `config/player_identity.csv`: optionele oudere IDs voor geboortejaarcompatibiliteit; niet nodig om spelers te koppelen.
- `clubscout/parser.py`: conservatieve HTML-parser.
- `clubscout/build.py`: cluboverzicht, identiteiten en dekking.
- `scripts/capture.mjs`: ploegkalenders en wedstrijdbladen ophalen.
- `data_raw/`: genormaliseerde brongegevens.
- `public/`: dashboard en afgeleide JSON.
- `tests/`: tests en uitgeknipte HTML van het echte reserveverslag.
- `VALIDATIE.md`: uitgevoerde controles en beperkingen.


