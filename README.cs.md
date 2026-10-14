# History Unlocked AI

## Skryté zprávy. Otevřený kód. Ověřitelné výsledky.

**AI pomohla přečíst kryptogram z období studené války. Výsledek můžete ověřit sami.**

Projekt historických šifer vede **Zijian Zeng z UCSI University**. Zveřejňuje kód, potřebná výzkumná data a metody: od české monoalfabetické substituce přes PORTAX a otočné mřížky až po podmíněné návrhy čtení pomocí přenosu klíče.

[English](README.md) · [中文](README.zh-CN.md) · [Čeština](README.cs.md) · [日本語](README.ja.md)

**HC Portal #615 je v oficiálním katalogu označen jako Solved a řešení je připsáno Zijianu Zengovi.** Výsledky dalších úloh nyní ověřují další odborníci; jejich závěry budou postupně doplněny.

[Oficiální záznam](https://crypto.hcportal.eu/dashboard/cryptograms/615) · [Veřejný výpis stavu](docs/HC615_PUBLIC_CATALOGUE_STATUS.json) · [Čtení HC615](cases/hc615/docs/SOLUTION.md)

### Reprodukce

```sh
git clone https://github.com/ArtificialZeng/history-unlocked-ai.git
cd history-unlocked-ai
python3 -B scripts/verify_portfolio.py --replay
```

Python 3.10 nebo novější. Ověření funguje offline se standardní knihovnou: kontroluje SHA-256 a spouští devět ověřovacích příkazů pro osm případů. Nevyžaduje AI ani síťové volání. Klonování soukromého repozitáře vyžaduje přístup.

### Přehled

| Případ | Současný výsledek | Kód / poznámka |
|---|---|---|
| HC615 | Oficiálně vyřešeno; reprodukce všech 220 pozorovaných symbolů | [Ověření](cases/hc615/) |
| HC696 | Přesné místní čtení 180 znaků konečné viditelné vrstvy metodou PORTAX | [Ověření](cases/hc696/) |
| HC849 | Reprodukce 64 znaků s veřejně dodanou mřížkou | [Ověření](cases/hc849/) |
| HC851 | Reprodukce 144 znaků s veřejně dodanou mřížkou | [Ověření](cases/hc851/) |
| HC852 | Reprodukce 64 znaků s dodanou mřížkou; alternativy zachovány | [Ověření](cases/hc852/) |
| HC1615 | Podmíněný návrh s převzatým klíčem a pravidlem přídavných tahů | [Ověření](cases/hc1615/) |
| HC1619 | Podmíněné preferované čtení 80/80; konzervativní 79/80 | [Ověření](cases/hc1619/) |
| HC1760 | Podmíněný návrh; bez samostatného solveru v tomto vydání | [Poznámka](cases/hc1760/) |
| HC1446 | Dílčí výsledek; čtyři značky nejsou přiřazeny | [Poznámka](cases/hc1446/) |
| HC1098 | Dílčí výsledek; 48 polí zůstává nečitelných | [Poznámka](cases/hc1098/) |
| HC1679 | Nezávisle auditované podmíněné dílčí čtení; 276 pozic ověřeno, 15 nevyřešených úseků | [Ověření](cases/hc1679/) |

Jedenáct výzkumných záznamů má jasně rozlišenou úroveň důkazů. Srovnávací materiál HC1619 se počítá pouze jednou. [Strojově čitelný seznam](data/CASE_INDEX.json).

### Novinky · 14. října 2026

**Nově: od náhledů k dohledatelným původním obrazům.** Čtyři nové otisky SHA-256 zachycují obě strany pohlednic HC1583 a HC1641 v původním rozlišení. HC1641 prošel omezenou kontrolou vhodnosti pramene; pořadí oddělených oblastí a alternativy spojených tahů ještě vyžadují doslovný záznam jednotlivých pozic. U HC1583 zůstává nesplněný časový limit postupu a u HC1570 neúplné pokrytí alternativ spojování. Při těchto kontrolách nebyl spuštěn žádný řešič historického cíle. [Pokrok a další podmínky](research/SOURCE_PROGRESS.md).

**Historická čtení s důkazy, které si můžete ověřit.** Jedenáct výzkumných záznamů zahrnuje oficiální potvrzení HC615 a nezávisle auditované dílčí čtení HC1679: 276 vybraných pozic, 2 633 kontrol a 15 výslovně nevyřešených úseků. Spustitelné případy zachovávají příkazy k reprodukci i hashe vědeckých vstupů.

**Nejnovější experiment: skóre musí obstát i při kontrole celé zprávy.** U HC1527 proběhl jeden předem stanovený test maskovaného těla zprávy a 99 odpovídajících promíchaných kontrol. Uchováno je všech **1 800 skóre restartů**. Skutečný vstup překonal všechny promíchané kontroly; podmíněná pořadová hodnota p je 0,01. Samostatný aritmetický audit prošel **89 640 kontrolami**, zaslepené posouzení čtyř doslovných výstupů s podporou AI však nepotvrdilo žádnou úplnou souvislou zprávu. Tento model byl zastaven s hodnocením proveditelnosti další práce 79/100. Veřejné číselné záznamy a offline kontrolní program umožňují přepočítat porovnání skóre a ověřit důvod zastavení; neopakují luštění cíle ani neprokazují historickou správnost. [Záznam dokončeného experimentu](research/trials/hc1527_fixed_model_v1/README.md).

**Novinka: hledání klíčů s ověřitelným záznamem.** Běhový nástroj s pevným rozpočtem kontroluje hashe kódu, modelu a vstupu i pevné náhodné semeno, uchovává všech 18 restartů a omezuje dobu běhu i počet procesů. Neznámé symboly zachovává bez doplňování vymyšleného textu. Nová kompilace reprodukovala výsledek P05 včetně jedné chyby. Pevné porovnání s 99 promíchanými kontrolami nyní proběhlo v experimentu HC1527 uvedeném výše. [Prozkoumat běhový nástroj](methods/czech_masked_bounded_runtime/README.md).

**Novinka: obnova čitelného textu i s chybějícími symboly.** V samostatném testu českého textu bez mezer obsahovalo šest syntetických zpráv o délce 400–600 písmen maskované jednotlivé symboly a sloučené úseky neznámé délky. Solver **přesně obnovil známé pozice v 5/6 zprávách a 2 612/2 613 známých znaků (99,96 %)**; samotné frekvenční řazení obnovilo 575/2 613. Samostatný postup s podporou AI nezávisle ověřil **3 156 kontrol**. Jedna chyba zůstává zachována; 387 skrytých původních znaků se nevydává za obnovené. Balíček obsahuje zdrojový kód, pevné masky a semena, všech 162 výstupů restartů, offline ověření a příkazy k novému běhu. Jde o výsledek syntetického testu metody; historické portfolio nadále obsahuje 11 záznamů. [Reprodukovat test maskovaných symbolů](methods/czech_wordless_masked_masc/README.md).

**Novinka: obnova českého textu bez mezer.** Přenosný solver substitučních šifer přesně obnovil všech šest syntetických zpráv o délce 200, 400 a 600 písmen: **2 400/2 400 znaků**, oproti 596/2 400 u samotného frekvenčního řazení. Samostatný audit s podporou AI ověřil 156 kontrol a přesné zpětné zašifrování; opakovaný běh po nové kompilaci odpovídal zmrazenému výstupu. Modul obsahuje zdrojový kód, pevná náhodná semena, kontrolní data a ověřovací příkazy. Testy používají nepoškozenou moderní češtinu; historický rukopis, chybějící symboly a jiné typy šifer vyžadují samostatné ověření. [Reprodukovatelný solver](methods/czech_wordless_masc/README.md).

**Nový přenosný kód:** parser katalogu doplňuje statický nástroj pro sledování řetězce načítání v JavaScriptu. Čtyři syntetické kontroly pokrývají vnořená volání se stejnou počáteční pozicí, lokální funkce, datové kontejnery ve stránce a negativní příklad falešného zdroje. Kód stránky nespouští ani nestahuje data; dynamické a nepodporované výrazy zůstávají nevyřešené. [Spustit čtyři kontroly](research/catalogue_metadata/static_loader/README.md).

**Hledat nové záhady bez opakování již řešených úloh.** Přenosný registr uchovává **2 579 identit** a všechna předchozí vyloučení. Toto vydání přidává čtyři otisky původních obrazů HC1583 a HC1641 a opravuje jeden otisk metadat API u HC1570, který byl chybně označen jako obraz. Otisk zůstává v dokladech o metadatech; vyloučení úloh a skutečné obrazové otisky jsou zachovány. Zachován je také zastavený pokus HC1527 a dřívější otisky HC1550. [Nové doklady o pramenech](research/SOURCE_UPDATE.json) · [Dřívější kontroly katalogu](research/SOURCE_CHECKS.json).

**Nástroje pro další průzkum:** index 846 objektů má deset ověřených vazeb mezi rozhraním a metadaty. Skupina „open“ s 266 objekty zahrnuje i dílčí čtení a klíče. Každý kandidát stále vyžaduje vlastní kontrolu pramene a předchozího řešení. [Důkazy o katalogu](research/CATALOGUE_MAPPING.json) · [Kontrola HC Portal](research/CATALOGUE_REFRESH.json).

**Zveřejněné čtení má přednost před novým útokem.** Přesná tvrzení o dílčím čtení bruselských R982 a R984 je nyní vylučují z fronty nových úloh. Stopy z British Library a SP53/16 čekají na ověření pramene, identity, jazyka či metody. Toto vydání rozšiřuje reprodukovatelnost a výběr úloh; nepřidává úplné rozluštění. [Poznámky k výběru](research/SCREENING_NOTES.md) · [Důkazy a překážky](research/SCREENING_UPDATE.json).

[Výzkumné nástroje](research/README.md) · [Kontroly metod](methods/README.md) · [Změny](CHANGELOG.md)

### Historie, kterou lze zkontrolovat

HC615 je katalogizován jako československý materiál kurzu kryptoanalýzy přibližně z roku 1952. Český text se týká vyslání pracovníků na roční brigádu do Ostravy. Jedna pevná substituce vysvětluje všech 220 pozorovaných symbolů, 32 oddělených úseků a osm řádků. Diakritika a hranice vět nejsou ve všech případech určitelné.

AI pomáhá s organizací, analýzou a programováním. Ověřovací kód ukazuje, co skutečně vyplývá ze zmrazeného přepisu a jaké předpoklady zůstávají podmíněné. Zpětné zašifrování samo o sobě nedokazuje historickou prioritu ani nové čtení vynechaných snímků.

[Návod k reprodukci](docs/REPRODUCIBILITY.md) · [Původní vědecká data a hashe](docs/CORE_PROVENANCE.json) · [Manifest vydání](CODE_CORE_MANIFEST.json)

### Zapojte se

Dejte projektu **Star**, vytvořte **Fork** a spusťte ověřovací skripty. Uvítáme nezávislou kontrolu přepisu, jazykové posouzení a doložené původní odpovědní listy. [Jak přispět](CONTRIBUTING.md).

**Vedoucí výzkumník:** Zijian Zeng, UCSI University, Kuala Lumpur, Malajsie.

Repozitář obsahuje kód, potřebná data, popis metod a stručné představení projektu. [Rozsah licencí](LICENSE_SCOPE.md).
