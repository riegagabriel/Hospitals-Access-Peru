# app.py
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import requests

st.set_page_config(layout="wide", page_title="Hospitales Perú")

# ------------------------------
# CARGA DE DATOS
# ------------------------------
@st.cache_data
def cargar_datos():
    url = "https://github.com/luchoravar/Hospitals-Access-Peru/raw/main/code/data/IPRESS.csv"
    r = requests.get(url)
    texto = r.content.decode("latin1", errors="ignore")
    with open("IPRESS_utf8.csv", "w", encoding="utf-8") as f:
        f.write(texto)
    df = pd.read_csv("IPRESS_utf8.csv")

    # Filtro hospitales en funcionamiento con coordenadas válidas
    df = df[df["Condición"] == "EN FUNCIONAMIENTO"]
    df = df.dropna(subset=["NORTE", "ESTE"])
    df = df[(df["NORTE"] != 0) & (df["ESTE"] != 0)]
    df = df[df["Clasificación"].isin([
        "HOSPITALES O CLINICAS DE ATENCION GENERAL",
        "HOSPITALES O CLINICAS DE ATENCION ESPECIALIZADA"
    ])]

    df["UBIGEO"] = df["UBIGEO"].astype(str).str.zfill(6)
    return df

df = cargar_datos()
st.title("🏥 Análisis Geoespacial de Hospitales en Perú")
st.write(f"Total hospitales analizados: **{df.shape[0]}**")

st.dataframe(df.head())

# ------------------------------
# MAPA ESTÁTICO DISTRITAL
# ------------------------------
@st.cache_data
def cargar_mapas():
    maps = gpd.read_file("https://github.com/luchoravar/Hospitals-Access-Peru/raw/main/code/data/Distritos/DISTRITOS.shp")
    maps = maps[['IDDIST', 'geometry']]
    maps = maps.rename({'IDDIST':'UBIGEO'}, axis=1)
    maps["UBIGEO"] = maps["UBIGEO"].astype(str).str.zfill(6)
    maps = maps.to_crs(epsg=4326)
    return maps

maps = cargar_mapas()

# Frecuencia por distrito
tabla_frecuencias = df['UBIGEO'].value_counts().reset_index()
tabla_frecuencias.columns = ['UBIGEO', 'Frecuencia']
dataset = maps.merge(tabla_frecuencias, how="left", on="UBIGEO").fillna(0)

# Plot estático
st.subheader("Mapa estático: Número de hospitales por distrito")
fig, ax = plt.subplots(figsize=(8, 8))
dataset.plot(column="Frecuencia", cmap="Reds", linewidth=0.5, edgecolor="gray", ax=ax, legend=True)
ax.set_title("Hospitales públicos por distrito", fontsize=14)
st.pyplot(fig)

# ------------------------------
# BARRAS POR DEPARTAMENTO
# ------------------------------
hosp_por_dep = df.groupby("Departamento", as_index=False).agg(
    Total_hospitales=("Nombre del establecimiento", "count")
).sort_values(by="Total_hospitales", ascending=False)

st.subheader("Número de hospitales por departamento")
fig, ax = plt.subplots(figsize=(8, 6))
sns.barplot(data=hosp_por_dep, x="Total_hospitales", y="Departamento", palette="Reds_r", ax=ax)
ax.set_title("Hospitales por departamento", fontsize=14)
st.pyplot(fig)

# ------------------------------
# MAPA INTERACTIVO FOLIUM
# ------------------------------
st.subheader("Mapa interactivo: Hospitales y densidad distrital")

# GeoDataFrame de hospitales
hospitales_gdf = gpd.GeoDataFrame(
    df.copy(),
    geometry=gpd.points_from_xy(df["ESTE"], df["NORTE"]),
    crs="EPSG:32718"
).to_crs(epsg=4326)

# Choropleth
geojson_distritos = dataset.to_json()
m = folium.Map(location=[-9.19, -75.02], zoom_start=5, tiles="CartoDB positron")

folium.Choropleth(
    geo_data=geojson_distritos,
    data=dataset,
    columns=["UBIGEO", "Frecuencia"],
    key_on="feature.properties.UBIGEO",
    fill_color="YlOrRd",
    legend_name="Número de hospitales por distrito"
).add_to(m)

marker_cluster = MarkerCluster(name="Hospitales").add_to(m)
for _, row in hospitales_gdf.iterrows():
    folium.Marker(
        location=[row.geometry.y, row.geometry.x],
        popup=f"{row.get('Nombre del establecimiento','Hospital')}<br>{row.get('Departamento','')}"
    ).add_to(marker_cluster)

st_folium(m, width=800, height=600)


