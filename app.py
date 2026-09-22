"""
app.py
=======
Klimaatbeleid vs. werkelijkheid: CO2-uitstoot, hernieuwbare energie en
economische welvaart per land.

Onderzoeksvraag: In hoeverre komt de transitie naar hernieuwbare energie
daadwerkelijk tot uiting in dalende CO2-uitstoot, en hoe verhoudt dit zich
tot het inkomensniveau van landen?

Databronnen: de twee aangeleverde CSV-bestanden in de map data/ (zie data_loader.py).

Overgenomen/geïnspireerde code:
  - Plotly Express choropleth-voorbeeld uit de officiële Plotly-documentatie
    (https://plotly.com/python/choropleth-maps/), aangepast aan onze eigen
    kolommen en kleurenschaal.
  - st.cache_data-gebruik volgens het Streamlit-cachingpatroon uit de
    Streamlit-documentatie (https://docs.streamlit.io/library/advanced-features/caching).
"""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from analysis import fit_ekc, walk_vs_talk
from data_loader import build_dataset

st.set_page_config(
    page_title="Klimaatbeleid vs. werkelijkheid",
    page_icon="🌍",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Data laden
# ---------------------------------------------------------------------------
df, join_log = build_dataset()

st.title("🌍 Klimaatbeleid vs. werkelijkheid")
st.caption(
    "De relatie tussen CO2-uitstoot, hernieuwbare energie en economische welvaart per land "
    f"({join_log['common_year_range'][0]}–{join_log['common_year_range'][1]})"
)

# ---------------------------------------------------------------------------
# Sidebar: interactieve besturing (verplicht: minimaal 1 slider, 1 checkbox, 1 dropdown)
# ---------------------------------------------------------------------------
st.sidebar.header("⚙️ Instellingen")

year_min, year_max = join_log["common_year_range"]
year_range = st.sidebar.slider(
    "Analyseperiode",
    min_value=year_min,
    max_value=year_max,
    value=(year_min, year_max),
    help="Filtert alle grafieken en de kaart op deze periode.",
)

per_capita = st.sidebar.checkbox(
    "Gebruik CO2 per capita (in plaats van totale uitstoot)",
    value=True,
    help="Zet aan om landen fair te vergelijken ongeacht bevolkingsomvang.",
)
co2_col = "co2_per_capita_t" if per_capita else "co2_tonnes"
co2_label = "CO2-uitstoot per capita (ton)" if per_capita else "Totale CO2-uitstoot (ton)"

countries_sorted = sorted(df["country"].dropna().unique())
highlight_country = st.sidebar.selectbox(
    "Land om te highlighten",
    options=countries_sorted,
    index=countries_sorted.index("Netherlands") if "Netherlands" in countries_sorted else 0,
    help="Dit land wordt geaccentueerd in de tijdreeks- en Kuznets-grafieken.",
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Bronnen: Our World in Data — CO2-uitstoot (Global Carbon Project) en "
    "Energie/GDP/bevolking (Energy Institute, Ember, Maddison Project, World Bank)."
)

df_period = df[(df.year >= year_range[0]) & (df.year <= year_range[1])].copy()

tab_data, tab_map, tab_walktalk, tab_ekc, tab_compare = st.tabs(
    ["📥 Data & methode", "🗺️ Wereldkaart", "🚶 Walk vs. Talk", "💰 Kuznets-curve", "⚖️ Landen vergelijken"]
)

# ---------------------------------------------------------------------------
# TAB 1 — Data & methode (dataverkenning + join-verantwoording)
# ---------------------------------------------------------------------------
with tab_data:
    st.subheader("Hoe is deze dataset opgebouwd?")
    st.markdown(
        """
        Twee **afzonderlijke** bestanden worden op schijf (map `data/`) ingelezen en
        samengevoegd op de sleutel **`iso_code` + `year`** (landcode + jaartal):

        1. **CO2-uitstoot** — `annual-co2-emissions-per-country.csv` (Global Carbon Project-cijfers)
        2. **Hernieuwbare energie, GDP & bevolking** — `renewable_energy_share_2000_2025.csv`
        """
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("CO2-rijen (ruw)", f"{join_log['co2_rows_raw']:,}")
    c2.metric("Energie-rijen (ruw)", f"{join_log['energy_rows_raw']:,}")
    c3.metric("Rijen na merge", f"{join_log['merged_rows']:,}")

    st.markdown("**Waarom deze aantallen niet 1-op-1 overeenkomen — en hoe dat is opgelost:**")
    st.markdown(
        f"""
        - Beide bronnen bevatten naast losse landen ook **regio's/aggregaten** (bv. "Africa",
          "High-income countries", "World"). Die hebben geen (bruikbare) ISO3-landcode en zijn
          er daarom uitgefilterd, vóór de merge:
          CO2 {join_log['co2_rows_raw']:,} → {join_log['co2_rows_countries_only']:,} rijen,
          Energie {join_log['energy_rows_raw']:,} → {join_log['energy_rows_countries_only']:,} rijen.
        - De CO2-reeks loopt tot **{year_max}**, de energiereeks vaak nog een paar jaar verder
          (voorlopige cijfers). De jaartallen zijn daarom **automatisch gelijkgetrokken** op de
          overlap van beide bronnen: **{join_log['common_year_range'][0]}–{join_log['common_year_range'][1]}**,
          in plaats van een jaartal hard te coderen.
        - Na het combineren op `iso_code + year` blijven **{join_log['merged_rows']:,} rijen** over
          (landen × jaren waarvoor **beide** bronnen een waarde hebben). Er gaan dus rijen "verloren"
          wanneer een land in slechts één van de twee bronnen voorkomt voor een bepaald jaar — dat is
          het klassieke risico bij een join, en precies waarom we het hier expliciet bijhouden.
        """
    )

    st.markdown("**Wat mist er, en wat is (nog) niet mogelijk?**")
    st.markdown(
        f"""
        - GDP ontbreekt voor ongeveer **{join_log['rows_missing_gdp_pct']:.0%}** van de rijen
          (vooral kleine (eiland)staten en de allerlaatste jaren, omdat GDP-cijfers met vertraging
          verschijnen). Grafieken die GDP gebruiken (de Kuznets-curve) laten die rijen automatisch weg.
        - Het aandeel hernieuwbare energie ontbreekt voor ongeveer
          **{join_log['rows_missing_renewables_pct']:.0%}** van de rijen.
        - De inkomensgroep-indeling hieronder is een **zelf afgeleide** kwartielindeling op basis van
          gemiddelde GDP per capita — géén officiële Wereldbank-classificatie. Voor landen zonder
          GDP-cijfer kan dus ook geen inkomensgroep bepaald worden.
        - Uitspraken over oorzaak-gevolg zijn met deze data niet mogelijk: het dashboard toont
          **correlaties en trends**, geen bewezen causale effecten van beleid op uitstoot.
        """
    )

    st.markdown("**Voorbeeld van de samengevoegde tabel:**")
    st.dataframe(
        df_period[
            ["country", "year", "co2_tonnes", "co2_per_capita_t", "renewables_share_energy",
             "gdp_per_capita", "income_group"]
        ].sort_values(["country", "year"]).head(200),
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# TAB 2 — Wereldkaart
# ---------------------------------------------------------------------------
with tab_map:
    st.subheader("Wereldkaart per jaar")
    map_metric = st.selectbox(
        "Kies een variabele voor de kaart",
        options=[co2_label, "Aandeel hernieuwbare energie (%)", "GDP per capita (US$)"],
        key="map_metric",
    )
    map_year = st.slider("Jaar", min_value=year_range[0], max_value=year_range[1], value=year_range[1])

    metric_col = {
        co2_label: co2_col,
        "Aandeel hernieuwbare energie (%)": "renewables_share_energy",
        "GDP per capita (US$)": "gdp_per_capita",
    }[map_metric]

    map_df = df[df.year == map_year].dropna(subset=[metric_col])
    fig = px.choropleth(
        map_df,
        locations="iso_code",
        color=metric_col,
        hover_name="country",
        color_continuous_scale="YlOrRd" if "co2" in metric_col else "Greens",
        labels={metric_col: map_metric},
        title=f"{map_metric} — {map_year}",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 3 — Walk vs. Talk
# ---------------------------------------------------------------------------
with tab_walktalk:
    st.subheader("Welke landen 'walk the talk', en welke praten er vooral over?")
    st.caption(
        "Vergelijkt per land het begin- en eindjaar van de gekozen periode: is het "
        "aandeel hernieuwbare energie gestegen, én is de CO2-uitstoot daadwerkelijk gedaald?"
    )
    threshold_pp = st.slider(
        "Drempel: minimale stijging in hernieuwbaar-aandeel (procentpunt) om als 'transitie' te tellen",
        min_value=0,
        max_value=30,
        value=5,
        help="Landen met minder groei dan dit worden geclassificeerd als 'geen transitie'.",
    )

    wt = walk_vs_talk(df_period, co2_col=co2_col, threshold_pp=threshold_pp)

    if wt.empty:
        st.info("Niet genoeg data in de gekozen periode voor deze analyse.")
    else:
        counts = wt["category"].value_counts().reindex(
            ["Walk the talk", "Talk, geen walk", "Geen transitie"], fill_value=0
        )
        col_a, col_b = st.columns([1, 2])
        with col_a:
            fig_bar = px.bar(
                counts, orientation="h",
                labels={"value": "Aantal landen", "index": ""},
                color=counts.index,
                color_discrete_map={
                    "Walk the talk": "#2ca02c",
                    "Talk, geen walk": "#ff7f0e",
                    "Geen transitie": "#7f7f7f",
                },
                title="Aantal landen per categorie",
            )
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_b:
            fig_scatter = px.scatter(
                wt, x="delta_renewables_pp", y="delta_co2",
                color="category", hover_name="country",
                labels={
                    "delta_renewables_pp": "Δ aandeel hernieuwbaar (procentpunt)",
                    "delta_co2": f"Δ {co2_label}",
                },
                color_discrete_map={
                    "Walk the talk": "#2ca02c",
                    "Talk, geen walk": "#ff7f0e",
                    "Geen transitie": "#7f7f7f",
                },
                title="Verandering in hernieuwbaar-aandeel vs. verandering in CO2",
            )
            fig_scatter.add_hline(y=0, line_dash="dot", line_color="gray")
            fig_scatter.add_vline(x=threshold_pp, line_dash="dot", line_color="gray")
            if highlight_country in wt.country.values:
                hc = wt[wt.country == highlight_country].iloc[0]
                fig_scatter.add_annotation(
                    x=hc.delta_renewables_pp, y=hc.delta_co2, text=highlight_country,
                    showarrow=True, arrowhead=2,
                )
            st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown(f"**Landen die écht 'walk the talk' laten zien ({co2_label.lower()} daalde):**")
        st.dataframe(
            wt[wt.category == "Walk the talk"].sort_values("delta_co2").reset_index(drop=True),
            use_container_width=True,
        )

# ---------------------------------------------------------------------------
# TAB 4 — Environmental Kuznets Curve
# ---------------------------------------------------------------------------
with tab_ekc:
    st.subheader("Environmental Kuznets Curve: stijgt CO2 mee met welvaart, of vlakt het af?")
    show_fit = st.checkbox("Toon kwadratische regressie-fit (EKC-model)", value=True)
    income_options = ["Alle"] + [g for g in
        ["Laag inkomen", "Lager-midden inkomen", "Hoger-midden inkomen", "Hoog inkomen"]
        if g in df_period.income_group.dropna().unique()]
    income_choice = st.selectbox("Filter op inkomensgroep", options=income_options)

    ekc_df = df_period.dropna(subset=["gdp_per_capita", co2_col])
    if income_choice != "Alle":
        ekc_df = ekc_df[ekc_df.income_group == income_choice]

    fig_ekc = px.scatter(
        ekc_df, x="gdp_per_capita", y=co2_col, color="income_group",
        hover_name="country", log_x=True, opacity=0.55,
        labels={"gdp_per_capita": "GDP per capita (US$, log-schaal)", co2_col: co2_label},
        title="GDP per capita vs. CO2-uitstoot",
    )

    x_grid, y_pred, coeffs = fit_ekc(ekc_df, x_col="gdp_per_capita", y_col=co2_col)
    if show_fit and x_grid is not None:
        fig_ekc.add_scatter(x=x_grid, y=y_pred, mode="lines", name="Kwadratische fit",
                             line=dict(color="black", width=3, dash="dash"))
        a, b, c = coeffs
        top_x = -b / (2 * a) if a != 0 else None
        if a < 0 and top_x is not None and x_grid.min() < top_x < x_grid.max():
            st.info(
                f"De fit piekt bij ongeveer **${top_x:,.0f} GDP per capita** en daalt daarna — "
                "dat is het klassieke Kuznets-patroon (eerst stijgen, dan dalen)."
            )
        elif a > 0:
            st.info("De fit buigt omhoog: in deze selectie stijgt CO2 juist versneld mee met welvaart — geen (klassieke) Kuznets-curve.")
        else:
            st.info("Geen duidelijke piek binnen het waargenomen GDP-bereik van deze selectie.")

    if highlight_country in ekc_df.country.values:
        hc_df = ekc_df[ekc_df.country == highlight_country]
        fig_ekc.add_scatter(
            x=hc_df.gdp_per_capita, y=hc_df[co2_col], mode="markers",
            marker=dict(color="red", size=10, symbol="star"), name=highlight_country,
        )
    st.plotly_chart(fig_ekc, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 5 — Landen vergelijken
# ---------------------------------------------------------------------------
with tab_compare:
    st.subheader("Landen naast elkaar door de tijd")
    compare_countries = st.multiselect(
        "Kies 2 tot 5 landen om te vergelijken",
        options=countries_sorted,
        default=[c for c in ["Netherlands", "Germany", "China", "India"] if c in countries_sorted][:4],
        max_selections=5,
    )
    cmp_df = df_period[df_period.country.isin(compare_countries)]

    if len(compare_countries) < 2:
        st.info("Selecteer minstens 2 landen.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.line(
                cmp_df, x="year", y="renewables_share_energy", color="country",
                labels={"renewables_share_energy": "Aandeel hernieuwbaar (%)", "year": "Jaar"},
                title="Aandeel hernieuwbare energie over tijd",
            )
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.line(
                cmp_df, x="year", y=co2_col, color="country",
                labels={co2_col: co2_label, "year": "Jaar"},
                title=f"{co2_label} over tijd",
            )
            st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
st.caption(
    "Bronnen: Global Carbon Project via Our World in Data (CO2); "
    "Energy Institute, Ember, Maddison Project Database & World Bank via Our World in Data "
    "(energie, GDP, bevolking). Alle brondata: CC BY 4.0."
)
