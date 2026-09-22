"""
analysis.py
============
Analysefuncties die los staan van de Streamlit-UI, zodat ze makkelijk te
testen/uitleggen zijn. Bevat:
  - walk_vs_talk(): per land de verandering in hernieuwbaar-aandeel en in
    CO2 tussen begin- en eindjaar, plus een classificatie.
  - fit_ekc(): een simpel kwadratisch regressiemodel (Environmental Kuznets
    Curve) van CO2 per capita op GDP per capita.
"""

import numpy as np
import pandas as pd


def walk_vs_talk(df: pd.DataFrame, co2_col: str, threshold_pp: float) -> pd.DataFrame:
    """
    Voor elk land: vergelijk het eerste en laatste beschikbare jaar in `df`
    op (a) verandering in aandeel hernieuwbare energie (procentpunt) en
    (b) verandering in CO2 (kolom `co2_col`, absoluut of per capita).

    Classificatie:
      - "Walk the talk"   : hernieuwbaar-aandeel steeg >= threshold_pp EN CO2 daalde
      - "Talk, geen walk" : hernieuwbaar-aandeel steeg >= threshold_pp MAAR CO2 daalde niet
      - "Geen transitie"  : hernieuwbaar-aandeel steeg minder dan threshold_pp
    """
    rows = []
    for country, g in df.groupby("country"):
        g = g.dropna(subset=["renewables_share_energy", co2_col]).sort_values("year")
        if len(g) < 2:
            continue
        first, last = g.iloc[0], g.iloc[-1]
        delta_renew = last["renewables_share_energy"] - first["renewables_share_energy"]
        delta_co2 = last[co2_col] - first[co2_col]
        if delta_renew >= threshold_pp and delta_co2 < 0:
            category = "Walk the talk"
        elif delta_renew >= threshold_pp and delta_co2 >= 0:
            category = "Talk, geen walk"
        else:
            category = "Geen transitie"
        rows.append(
            {
                "country": country,
                "income_group": first.get("income_group"),
                "start_year": int(first["year"]),
                "end_year": int(last["year"]),
                "delta_renewables_pp": delta_renew,
                "delta_co2": delta_co2,
                "category": category,
            }
        )
    return pd.DataFrame(rows)


def fit_ekc(df: pd.DataFrame, x_col: str = "gdp_per_capita", y_col: str = "co2_per_capita_t"):
    """
    Kwadratische regressie y = a*x^2 + b*x + c (Environmental Kuznets Curve).
    Retourneert (x_grid, y_pred, coeffs) voor het tekenen van de fit-lijn,
    of (None, None, None) als er te weinig data is.
    """
    d = df[[x_col, y_col]].replace([np.inf, -np.inf], np.nan).dropna()
    d = d[d[x_col] > 0]
    if len(d) < 10:
        return None, None, None
    coeffs = np.polyfit(d[x_col], d[y_col], deg=2)
    x_grid = np.linspace(d[x_col].min(), d[x_col].max(), 200)
    y_pred = np.polyval(coeffs, x_grid)
    return x_grid, y_pred, coeffs
