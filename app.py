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

# ============================================
# 📍 MAPAS INTERACTIVOS CON FOLIUM
# ============================================

import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from folium import Circle, CircleMarker, Marker
from shapely.geometry import Point

# ---------- Crear GeoDataFrame de hospitales (usar ESTE/NORTE) ----------
hospitales_gdf = gpd.GeoDataFrame(
    df.copy(),
    geometry=gpd.points_from_xy(df["ESTE"], df["NORTE"]),
    crs="EPSG:32718"   # tus coords están en UTM 18S
)

# Reproyectar a WGS84 (EPSG:4326) para visualización en Folium
hospitales_4326 = hospitales_gdf.to_crs(epsg=4326)

# ---------- TASK 1: Choropleth (Hospitales por distrito) ----------
dataset_choro = dataset.copy()
dataset_choro["UBIGEO"] = dataset_choro["UBIGEO"].astype(str)

geojson_distritos = dataset_choro.to_json()

m_choro = folium.Map(location=[-9.19, -75.02], zoom_start=5, tiles="CartoDB positron")

folium.Choropleth(
    geo_data=geojson_distritos,
    name="choropleth",
    data=dataset_choro,
    columns=["UBIGEO", "Frecuencia"],
    key_on="feature.properties.UBIGEO",
    fill_color="YlOrRd",
    fill_opacity=0.8,
    line_opacity=0.2,
    legend_name="Número de hospitales por distrito",
    nan_fill_color="white"
).add_to(m_choro)

# Añadir tooltip en distritos
folium.GeoJson(
    data=geojson_distritos,
    name="Distritos (tooltip)",
    tooltip=folium.GeoJsonTooltip(
        fields=["UBIGEO", "Frecuencia"],
        aliases=["UBIGEO:", "N° hospitales:"],
        localize=True
    ),
    style_function=lambda x: {'fillOpacity': 0, 'color': 'none'}
).add_to(m_choro)

# MarkerCluster de hospitales
marker_cluster = MarkerCluster(name="Hospitales (cluster)").add_to(m_choro)
for _, row in hospitales_4326.iterrows():
    popup_text = (f"{row.get('Nombre del establecimiento','Hospital')}<br>"
                  f"Departamento: {row.get('Departamento','')}, "
                  f"Distrito UBIGEO: {row.get('UBIGEO','')}")
    folium.Marker(
        location=[row.geometry.y, row.geometry.x],
        popup=popup_text,
        icon=folium.Icon(color="red", icon="plus-sign")
    ).add_to(marker_cluster)

m_choro.save("choropleth_hospitales_distrito.html")
print("✅ Mapa guardado: choropleth_hospitales_distrito.html")


# ---------- TASK 2: Proximidad Lima & Loreto ----------
# Cargar CCPP desde GitHub (zip con shapefile)
url = "https://github.com/luchoravar/Hospitals-Access-Peru/raw/main/code/data/CCPP_0.zip"
CCPP = gpd.read_file(f"zip+{url}")

# Asegurar CRS en WGS84
CCPP = CCPP.to_crs("EPSG:4326")
maps = hospitales_4326.copy()

# Filtrar Lima y Loreto
centros_sel = CCPP[CCPP["DEP"].isin(["LIMA", "LORETO"])].copy()
hosp_sel = maps[maps["UBIGEO_DEP"].isin([15, 16])].copy()

# Reproyectar a UTM para distancias
centros_sel = centros_sel.to_crs("EPSG:32718")
hosp_sel = hosp_sel.to_crs("EPSG:32718")

# Buffers de 10 km
centros_sel["buffer_10km"] = centros_sel.geometry.buffer(10000)

# Contar hospitales dentro de cada buffer
centros_sel["Hosp_10km"] = centros_sel.apply(
    lambda row: hosp_sel.intersects(row["buffer_10km"]).sum(), axis=1
)

# Separar Lima y Loreto
centros_lima = centros_sel[centros_sel["DEP"] == "LIMA"].copy()
centros_loreto = centros_sel[centros_sel["DEP"] == "LORETO"].copy()

# Extremos: aislado y concentrado
aislado_lima = centros_lima.loc[centros_lima["Hosp_10km"].idxmin()]
concentrado_lima = centros_lima.loc[centros_lima["Hosp_10km"].idxmax()]
aislado_loreto = centros_loreto.loc[centros_loreto["Hosp_10km"].idxmin()]
concentrado_loreto = centros_loreto.loc[centros_loreto["Hosp_10km"].idxmax()]

# Extraer hospitales por buffer
hosp_aislado_lima = hosp_sel[hosp_sel.intersects(aislado_lima["buffer_10km"])]
hosp_concentrado_lima = hosp_sel[hosp_sel.intersects(concentrado_lima["buffer_10km"])]
hosp_aislado_loreto = hosp_sel[hosp_sel.intersects(aislado_loreto["buffer_10km"])]
hosp_concentrado_loreto = hosp_sel[hosp_sel.intersects(concentrado_loreto["buffer_10km"])]

# Reproyectar todo a WGS84
centros_sel = centros_sel.to_crs("EPSG:4326")
hosp_sel = hosp_sel.to_crs("EPSG:4326")
hosp_aislado_lima = hosp_aislado_lima.to_crs("EPSG:4326")
hosp_concentrado_lima = hosp_concentrado_lima.to_crs("EPSG:4326")
hosp_aislado_loreto = hosp_aislado_loreto.to_crs("EPSG:4326")
hosp_concentrado_loreto = hosp_concentrado_loreto.to_crs("EPSG:4326")

# Crear mapa Folium
m = folium.Map(location=[-9.19, -75.0152], zoom_start=6, tiles='OpenStreetMap')

def dibujar_centro(m, centro, color_circle, color_marker, label, hosp_data):
    centroide = centro.geometry.centroid
    folium.Circle(
        location=[centroide.y, centroide.x],
        radius=10000,
        color=color_circle,
        fill=True,
        fill_color=color_circle,
        fill_opacity=0.15,
        weight=3,
        popup=f"{label}<br>{centro['NOM_POBLAD']}<br>Hosp: {centro['Hosp_10km']}"
    ).add_to(m)

    folium.Marker(
        location=[centroide.y, centroide.x],
        tooltip=f"{label} - {centro['NOM_POBLAD']}: {centro['Hosp_10km']} hospitales",
        icon=folium.Icon(color=color_marker, icon="home", prefix='fa')
    ).add_to(m)

    for _, hosp in hosp_data.iterrows():
        hosp_centroid = hosp.geometry.centroid
        folium.CircleMarker(
            location=[hosp_centroid.y, hosp_centroid.x],
            radius=4,
            color=color_marker,
            fill=True,
            fill_color=color_marker,
            fill_opacity=0.9,
            popup=f"Hospital: {hosp.get('NOMBRE', 'N/A')}"
        ).add_to(m)

# Dibujar resultados
dibujar_centro(m, aislado_lima, "red", "red", "🔴 LIMA - Aislado", hosp_aislado_lima)
dibujar_centro(m, concentrado_lima, "green", "green", "🟢 LIMA - Concentrado", hosp_concentrado_lima)
dibujar_centro(m, aislado_loreto, "orange", "orange", "🔴 LORETO - Aislado", hosp_aislado_loreto)
dibujar_centro(m, concentrado_loreto, "blue", "blue", "🟢 LORETO - Concentrado", hosp_concentrado_loreto)

# Leyenda
legend_html = '''
<div style="position: fixed; bottom: 50px; right: 50px; width: 280px;
            background: white; border:2px solid grey; z-index:9999;
            font-size:13px; padding: 10px; border-radius: 5px;">
<h4>📊 Leyenda</h4>
<p><span style="color:red;">⭕</span> Lima aislado</p>
<p><span style="color:green;">⭕</span> Lima concentrado</p>
<p><span style="color:orange;">⭕</span> Loreto aislado</p>
<p><span style="color:blue;">⭕</span> Loreto concentrado</p>
<p style="font-size:11px; color:gray;">● Hospitales dentro del radio</p>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

m.save("task2_proximity_lima_loreto.html")
print("✅ Mapa guardado: task2_proximity_lima_loreto.html")

