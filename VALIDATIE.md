# Validatie · 4 november 2026

Geslaagd:

- Vijf Python-tests: echt reserveverslag (30 namen, waarvan 15 Torhout), tweede doelman, kaartmarkeringen, geblokkeerde pagina en identiteitskoppeling/dubbele verslagen.
- Zes Node-tests: zeven exacte ploegkalenders, verkeerde club/ploeg en reekskalenders weigeren, U21 uitsluiten, dubbele ploeg-ID weigeren, wedstrijd-URL dedupliceren, historische scores bewaren en scorewijzigingen weigeren, aftrapuur/uitstel niet als score interpreteren.
- Python-bouw: 15 Torhout-spelers, zeven gevolgde ploegen, alle ontbrekende speelgegevens onbekend.
- Syntaxiscontrole van collector en dashboard-JavaScript.

Nog niet gevalideerd:

- Live RBFA-teamkalenders en hun filters/paginering. De pagina's konden vanuit deze omgeving niet worden geopend. Hiervoor dient de eerste `Update clubdata`-run op GitHub.
- Visuele en interactieve browsertest. De lokale browserstart is door een systeembeperking geblokkeerd.
- Volledige-verslagmodus met betrouwbare basis/bank/wissels. Deze is nog niet geïmplementeerd; ook A-/B-speelgegevens blijven voorlopig onbekend.

Volledige seizoensdekking wordt nergens als bewezen voorgesteld. De bronfixture is het werkelijk aangeleverde verslag KM Torhout A – R. Knokke FC, 2 november 2026, eindscore 3–5; geen verzonnen spelersdata.
