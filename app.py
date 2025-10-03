# -*- coding: utf-8 -*-
# streamlit run app.py

import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import folium
from folium.plugins import MarkerCluster
from shapely.geometry import Point
from streamlit_folium import st_folium

st.set_page_config(page_title="Hospitales en Perú", layout="wide")

st.title("🏥 Análisis Geoespacial de Hospitales en Perú")

# -------------------------
# 1) Cargar y limpiar datos
# -------------------------
@st.cache_data
def load_data():
    url = "https://github.com/luchoravar/Hospitals-Access-Peru/raw/main/code/data/IPRESS.csv"
    r = requests.get(url)
    r.raise_for_status()
    texto = r.content.decode("latin1", errors="ignore")
    with open("IPRESS_utf8.csv", "w", encoding="utf-8") as f:
        f.write(texto)
    df = pd.read_csv("IPRESS_utf8.csv")
    return df

df = load_data()
st.write("Datos originales:", df.shape)

# Filtrar hospitales operativos con coordenadas válidas
df = df[df["Condición"] == "EN FUNCIONAMIENTO"]
df = df.dropna(subset=["NORTE", "ESTE"])
df = df[(df["NORTE"] != 0) & (df["ESTE"] != 0)]
df = df[df["Clasificación"].isin([
    "HOSPITALES O CLINICAS DE ATENCION GENERAL",
    "HOSPITALES O CLINICAS DE ATENCION ESPECIALIZADA"
])]
df["UBIGEO"] = df["UBIGEO"].astype(str).str.zfill(6)

st.write("Datos filtrados (hospitales operativos con coordenadas):", df.shape)

# -------------------------
# 2) Shapefile Distritos
# -------------------------
@st.cache_data
def load_shapefile():
    maps = gpd.read_file("https://github.com/luchoravar/Hospitals-Access-Peru/raw/main/code/data/Distritos/DISTRITOS.shp")
    maps = maps[["IDDIST", "geometry"]].rename(columns={"IDDIST": "UBIGEO"})
    maps["UBIGEO"] = maps["UBIGEO"].astype(str).astype(int)
    maps = maps.to_crs(epsg=4326)
    return maps

maps = load_shapefile()

# -------------------------
# 3) Conteo hospitales por distrito
# -------------------------
tabla_frecuencias_ubigeo = df["UBIGEO"].value_counts().reset_index()
tabla_frecuencias_ubigeo.columns = ["UBIGEO", "Frecuencia"]
tabla_frecuencias_ubigeo["UBIGEO"] = tabla_frecuencias_ubigeo["UBIGEO"].astype(int)

dataset = maps.merge(tabla_frecuencias_ubigeo, on="UBIGEO", how="left")
dataset["Frecuencia"] = dataset["Frecuencia"].fillna(0).astype(int)

st.subheader("📊 Conteo de hospitales por distrito")
st.dataframe(tabla_frecuencias_ubigeo.head(15))

# -------------------------
# 4) Mapa estático (matplotlib)
# -------------------------
fig, ax = plt.subplots(figsize=(8, 8))
dataset.plot(
    column="Frecuencia",
    cmap="Reds",
    linewidth=0.5,
    edgecolor="gray",
    legend=True,
    ax=ax
)
ax.set_title("Hospitales públicos por distrito", fontsize=14, fontweight="bold")
st.pyplot(fig)

# -------------------------
# 5) Mapa interactivo (folium)
# -------------------------
st.subheader("🗺️ Mapa interactivo con Folium")

# GeoDataFrame hospitales
hospitales_gdf = gpd.GeoDataFrame(
    df.copy(),
    geometry=gpd.points_from_xy(df["ESTE"], df["NORTE"]),
    crs="EPSG:32718"
).to_crs(epsg=4326)

dataset_choro = dataset.copy()
dataset_choro["UBIGEO"] = dataset_choro["UBIGEO"].astype(str)
geojson_distritos = dataset_choro.to_json()

m = folium.Map(location=[-9.19, -75.02], zoom_start=5, tiles="CartoDB positron")

# Choropleth
folium.Choropleth(
    geo_data=geojson_distritos,
    data=dataset_choro,
    columns=["UBIGEO", "Frecuencia"],
    key_on="feature.properties.UBIGEO",
    fill_color="YlOrRd",
    fill_opacity=0.8,
    line_opacity=0.2,
    legend_name="Número de hospitales por distrito",
    nan_fill_color="white"
).add_to(m)

# Tooltip
folium.GeoJson(
    data=geojson_distritos,
    name="Distritos",
    tooltip=folium.GeoJsonTooltip(
        fields=["UBIGEO", "Frecuencia"],
        aliases=["UBIGEO:", "N° hospitales:"]
    ),
    style_function=lambda x: {"fillOpacity": 0, "color": "none"}
).add_to(m)

# Hospitales cluster
mc = MarkerCluster(name="Hospitales").add_to(m)
for _, row in hospitales_gdf.iterrows():
    popup = f"{row['Nombre del establecimiento']}<br>{row['Departamento']}"
    folium.Marker(
        location=[row.geometry.y, row.geometry.x],
        popup=popup,
        icon=folium.Icon(color="red", icon="plus-sign")
    ).add_to(mc)

# Render folium en Streamlit
st_folium(m, width=1000, height=600)
