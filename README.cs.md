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

Python 3.10 nebo novější. Ověření funguje offline se standardní knihovnou: kontroluje SHA-256 a spouští osm ověřovacích příkazů pro sedm případů. Nevyžaduje AI ani síťové volání. Klonování soukromého repozitáře vyžaduje přístup.

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

Deset záznamů není deset potvrzených řešení. Srovnávací materiál HC1619 se počítá pouze jednou. [Strojově čitelný seznam](data/CASE_INDEX.json).

### Historie, kterou lze zkontrolovat

HC615 je katalogizován jako československý materiál kurzu kryptoanalýzy přibližně z roku 1952. Český text se týká vyslání pracovníků na roční brigádu do Ostravy. Jedna pevná substituce vysvětluje všech 220 pozorovaných symbolů, 32 oddělených úseků a osm řádků. Diakritika a hranice vět nejsou ve všech případech určitelné.

AI pomáhá s organizací, analýzou a programováním. Ověřovací kód ukazuje, co skutečně vyplývá ze zmrazeného přepisu a jaké předpoklady zůstávají podmíněné. Zpětné zašifrování samo o sobě nedokazuje historickou prioritu ani nové čtení vynechaných snímků.

[Návod k reprodukci](docs/REPRODUCIBILITY.md) · [Původní vědecká data a hashe](docs/CORE_PROVENANCE.json) · [Manifest vydání](CODE_CORE_MANIFEST.json)

### Zapojte se

Dejte projektu **Star**, vytvořte **Fork** a spusťte ověřovací skripty. Uvítáme nezávislou kontrolu přepisu, jazykové posouzení a doložené původní odpovědní listy. [Jak přispět](CONTRIBUTING.md).

**Vedoucí výzkumník:** Zijian Zeng, UCSI University, Kuala Lumpur, Malajsie.

Repozitář obsahuje kód, potřebná data, popis metod a stručné představení projektu. [Rozsah licencí](LICENSE_SCOPE.md).
