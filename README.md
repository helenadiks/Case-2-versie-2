# Klimaatbeleid vs. werkelijkheid 🌍

Streamlit-dashboard voor de case *Analytics* (Introduction to Data Science / Visual Analytics).

**Onderzoeksvraag:** In hoeverre komt de transitie naar hernieuwbare energie daadwerkelijk tot
uiting in dalende CO2-uitstoot, en hoe verhoudt dit zich tot het inkomensniveau van landen?

**Deelvragen:**
- Welke landen laten een reële ontkoppeling zien tussen groei in hernieuwbare energie en
  daling van CO2-uitstoot ("walk"), en welke blijven vooral bij beleidsintenties ("talk")?
- Is er bewijs voor een *Environmental Kuznets Curve* (CO2 stijgt mee met GDP per capita tot
  een bepaald niveau, en vlakt daarna af of daalt)?
- Hoe verschilt dit patroon tussen rijke, opkomende en arme landen?

## Databronnen

Dit dashboard gebruikt **uitsluitend de twee aangeleverde CSV-bestanden**, meegepakt in de
map `data/` van deze repo:

| # | Data | Bestand |
|---|------|---------|
| 1 | CO2-uitstoot per land per jaar | `data/annual-co2-emissions-per-country.csv` |
| 2 | Hernieuwbaar-aandeel, GDP, bevolking | `data/renewable_energy_share_2000_2025.csv` |

Beide bestanden staan gewoon in de repo, dus een schone `git clone` + `pip install` +
`streamlit run app.py` werkt zonder handmatige stappen en zonder internetverbinding.

> ⚠️ **Let op voor de beoordeling:** de opdracht eist letterlijk dat je de data ophaalt via
> een **openbare API**, niet met de hand gedownloade bestanden ("Haal de data in je script op,
> niet met de hand gedownload."). Deze twee CSV's zijn oorspronkelijk van Kaggle gedownload,
> en worden hier vanaf schijf ingelezen — dat voldoet **niet** aan die letterlijke eis, en kan
> meetellen bij het criterium "Data verzameling". Als je dat risico wilt vermijden zonder de
> data zelf te veranderen: zet deze twee bestanden in een eigen (publieke) GitHub-repo en laat
> het script ze ophalen via hun `raw.githubusercontent.com`-URL (met `pandas.read_csv(url)` of
> `requests.get(url)`) in plaats van vanaf schijf. Dat is dezelfde data, maar dan wél "opgehaald"
> via een URL in code in plaats van met de hand gedownload.

Beide bestanden zijn wél **twee volledig gescheiden bestanden**, samengevoegd op de sleutel
`iso_code` (landcode) + `year` — dat voldoet aan de eis "je voegt twee tabellen samen die niet
uit hetzelfde bestand komen".

### Join-verantwoording (rijaantallen voor/na)

Wordt live getoond in het tabblad **"📥 Data & methode"** van het dashboard zelf (met exacte
aantallen), inclusief:
- hoeveel rijen wegvallen omdat het aggregaten/regio's zijn (bv. "Africa", "World") in plaats
  van losse landen;
- hoe de jaartallen van beide bronnen automatisch gelijk worden getrokken (de CO2-reeks stopt
  eerder dan de energiereeks — de app neemt dynamisch de overlap, in plaats van een hard
  gecodeerd jaartal);
- hoeveel rijen overblijven na de merge, en hoeveel % van GDP/hernieuwbaar-aandeel ontbreekt.

## Structuur van dit project

```
.
├── app.py                    # Streamlit-app (UI, tabs, interactie)
├── data_loader.py             # Inlezen + samenvoegen + opschonen
├── analysis.py                 # Walk-vs-talk classificatie + EKC-regressie
├── data/
│   ├── annual-co2-emissions-per-country.csv
│   └── renewable_energy_share_2000_2025.csv
├── requirements.txt
├── .streamlit/config.toml      # Kleurthema
└── README.md
```

## Lokaal draaien

```bash
git clone <jouw-repo-url>
cd <repo-map>
python3 -m venv .venv && source .venv/bin/activate   # optioneel
pip install -r requirements.txt
streamlit run app.py
```

De app heeft **geen internetverbinding** nodig — beide CSV's staan al in de repo — en verder
geen extra configuratie, API-key of handmatige stap.

## Live publiceren via Streamlit Community Cloud

1. Push deze map naar een **publieke GitHub-repository**.
2. Ga naar [share.streamlit.io](https://share.streamlit.io) en log in met je GitHub-account.
3. Klik op **"New app"**, kies je repo/branch en zet **Main file path** op `app.py`.
4. Klik op **Deploy**. Na een paar minuten is de app publiek bereikbaar via een `*.streamlit.app`-link.
5. Zet die link (en je repo-link) in je Teams-melding / presentatie.

Een schone `git clone` + de bovenstaande stappen zijn voldoende — er is geen los databestand
nodig, want alles wordt in `data_loader.py` bij de bron opgehaald.

## Interactieve elementen in het dashboard

| Element | Locatie | Koppeling |
|---|---|---|
| **Slider** — analyseperiode | Sidebar | Filtert alle tabs |
| **Slider** — jaar op de kaart | Wereldkaart | Bepaalt welk jaar de choropleth toont |
| **Slider** — walk/talk-drempel | Walk vs. Talk | Bepaalt de classificatie-grens |
| **Checkbox** — CO2 per capita aan/uit | Sidebar | Wisselt de metric in alle grafieken |
| **Checkbox** — EKC-fit tonen | Kuznets-curve | Toont/verbergt de kwadratische regressielijn |
| **Dropdown** — land highlighten | Sidebar | Accentueert een land in de scatter/tijdreeks-grafieken |
| **Dropdown** — kaart-variabele | Wereldkaart | Wisselt tussen CO2, hernieuwbaar-aandeel, GDP |
| **Dropdown** — inkomensgroep-filter | Kuznets-curve | Filtert de scatterplot op inkomensgroep |
| **Multiselect** — landen vergelijken | Landen vergelijken | Kiest welke landen in de tijdreeksen staan |

## Analyse / afgeleide variabelen

- `co2_per_capita_t` = CO2-uitstoot ÷ bevolking
- `gdp_per_capita` = GDP ÷ bevolking
- `income_group` = eigen kwartiel-indeling (Laag / Lager-midden / Hoger-midden / Hoog inkomen)
  op basis van gemiddelde GDP per capita per land — **geen** officiële Wereldbank-classificatie,
  wat expliciet zo benoemd wordt in de app.
- Walk-vs-talk classificatie: vergelijkt de verandering in hernieuwbaar-aandeel met de
  verandering in CO2 tussen begin- en eindjaar van de gekozen periode (`analysis.py`).
- Kwadratische regressie (`numpy.polyfit`, graad 2) van CO2 per capita op GDP per capita, als
  eenvoudig model om de Environmental Kuznets Curve te toetsen.

## Bronvermelding overgenomen code

- Plotly Express choropleth-opzet: aangepast van het officiële voorbeeld op
  [plotly.com/python/choropleth-maps](https://plotly.com/python/choropleth-maps/).
- `st.cache_data`-gebruik: volgens het cachingpatroon uit de
  [Streamlit-documentatie](https://docs.streamlit.io/library/advanced-features/caching).

## Beperkingen / wat (nog) niet mogelijk is

- Correlatie ≠ causaliteit: het dashboard laat samenhang en trends zien, geen bewijs dat beleid
  X uitstoot Y heeft veroorzaakt.
- GDP-cijfers ontbreken voor de laatste jaren (rapportagevertraging) en voor een aantal kleine
  (eiland)staten — dit vermindert het aantal landen in de Kuznets-curve-analyse.
- De inkomensgroep-indeling is zelf afgeleid en niet gelijk aan officiële Wereldbank-groepen.
