import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium

# ================================
# 📂 Carga de datos desde GitHub
# ================================

URL_BASE = "https://github.com/riegagabriel/Hospitals-Access-Peru/raw/main/code/data/"

# Hospitales (CSV)
hospitales_df = pd.read_csv(URL_BASE + "IPRESS_utf8.csv")

# Convertir a GeoDataFrame
hospitales = gpd.GeoDataFrame(
    hospitales_df,
    geometry=gpd.points_from_xy(hospitales_df["LONGITUD"], hospitales_df["LATITUD"]),
    crs="EPSG:4326"
).to_crs(32718)

# Centros poblados (ZIP)
CCPP = gpd.read_file(URL_BASE + "CCPP_0.zip").to_crs(32718)

# Distritos (ZIP de geoBoundaries)
maps = gpd.read_file(URL_BASE + "geoBoundaries-PER-ADM2-all.zip").to_crs(32718)


# ================================
# 📌 Task 1: Análisis Distrital
# ================================
def task1_distritos():
    st.subheader("Task 1: Hospitales por Distrito")

    # Join espacial hospitales ↔ distritos
    hospitales_por_distrito = gpd.sjoin(hospitales, maps, how="left").groupby("DISTRITO").size().reset_index(name="n_hospitales")
    distritos_local = maps.merge(hospitales_por_distrito, on="DISTRITO", how="left").fillna({"n_hospitales": 0})

    distritos_sin = distritos_local[distritos_local["n_hospitales"] == 0]

    st.markdown("**Distritos sin hospitales**")
    st.write(distritos_sin[["DEPARTAMEN", "PROVINCIA", "DISTRITO"]])

    top10 = distritos_local.sort_values("n_hospitales", ascending=False).head(10)
    st.markdown("**Top 10 distritos con más hospitales**")
    st.write(top10[["DEPARTAMEN", "PROVINCIA", "DISTRITO", "n_hospitales"]])

    # 🔹 Mapa Folium
    m1 = folium.Map(location=[-9.19, -75.015], zoom_start=5)

    folium.GeoJson(
        distritos_local,
        style_function=lambda x: {
            "fillColor": "transparent",
            "color": "black",
            "weight": 0.5,
        },
        tooltip=folium.GeoJsonTooltip(fields=["DEPARTAMEN", "PROVINCIA", "DISTRITO", "n_hospitales"])
    ).add_to(m1)

    for idx, row in hospitales.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=2,
            color="red",
            fill=True,
            fill_opacity=0.7
        ).add_to(m1)

    st.subheader("🌍 Mapa Folium - Hospitales por distrito")
    st_folium(m1, width=700, height=500)


# ================================
# 📌 Task 2: Lima & Loreto
# ================================
def task2_lima_loreto():
    st.subheader("Task 2: Distritos y CCPP en Lima y Loreto")

    # Filtrar Lima y Loreto
    centros_sel = CCPP[CCPP["DEP"].isin(["LIMA", "LORETO"])].copy()
    hosp_sel = maps[maps["DEPARTAMEN"].isin(["LIMA", "LORETO"])].copy()

    # Reproyectar
    centros_sel = centros_sel.to_crs("EPSG:32718")
    hosp_sel = hosp_sel.to_crs("EPSG:32718")

    # 🔹 Mapa Folium
    m2 = folium.Map(location=[-9.19, -75.015], zoom_start=6)

    folium.GeoJson(
        hosp_sel,
        name="Distritos",
        style_function=lambda x: {
            "fillColor": "transparent",
            "color": "blue",
            "weight": 1,
        },
        tooltip=folium.GeoJsonTooltip(fields=["DEPARTAMEN", "PROVINCIA", "DISTRITO"])
    ).add_to(m2)

    for idx, row in centros_sel.iterrows():
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            popup=f"Centro poblado: {row['NOMBRE']}",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m2)

    st.subheader("🌍 Mapa Folium - Lima y Loreto")
    st_folium(m2, width=700, height=500)


# ================================
# 🚀 Main
# ================================
st.title("📊 Acceso a Hospitales en Perú")

task1_distritos()
task2_lima_loreto()

