# Geboortejaren toevoegen

Download in het dashboard **Ontbrekende geboortejaren**. Vul de kolom `Geboortejaar` aan en upload het CSV-bestand hier via **Add file → Upload files**. Gebruik telkens een nieuwe bestandsnaam en commit op `main`.

De kolommen zijn `ClubRBFA;Naam;Geboortejaar`. Ook MacroDroid-resultaten met `Ploeg;Naam;Geboortejaar;Gevonden` worden aanvaard. `Gevonden=false` wordt overgeslagen. Bestaande geboortejaren worden bij een conflict niet overschreven; de workflow meldt het conflict.

Na een geslaagde import en publicatie verschijnen de geboortejaren en werken de leeftijdsfilters. Onbekende leeftijden worden niet als jong of ervaren ingedeeld.
