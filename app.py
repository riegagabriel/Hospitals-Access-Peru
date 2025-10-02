# -*- coding: utf-8 -*-
"""
Aplicación Streamlit: Análisis Geoespacial de Hospitales en Perú
Grupo 1-2-10

INSTRUCCIONES PARA COLAB:
1. Guarda este archivo como 'app.py' en tu directorio de trabajo
2. Ejecuta las celdas de instalación y configuración primero
3. Luego ejecuta la celda que inicia Streamlit con localtunnel
"""

import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import folium
from folium import Marker, Circle, CircleMarker
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
import seaborn as sns
from shapely.geometry import Point
import requests
from io import BytesIO
from PIL import Image

# ============================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================
st.set_page_config(
    page_title="Hospitales Perú - Análisis Geoespacial",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# FUNCIONES DE CARGA DE DATOS
# ============================================
@st.cache_data
def load_hospital_data():
    """Carga y procesa datos de hospitales IPRESS"""
    url = "https://github.com/luchoravar/Hospitals-Access-Peru/raw/main/code/data/IPRESS.csv"
    r = requests.get(url)
    r.raise_for_status()
    raw_data = r.content
    texto = raw_data.decode("latin1", errors="ignore")
    
    # Crear DataFrame
    from io import StringIO
    df = pd.read_csv(StringIO(texto))
    
    # Filtrar: solo hospitales operativos
    df = df[df["Condición"] == "EN FUNCIONAMIENTO"]
    
    # Filtrar: coordenadas válidas
    df = df.dropna(subset=["NORTE", "ESTE"])
    df = df[(df["NORTE"] != 0) & (df["ESTE"] != 0)]
    
    # Filtrar: solo hospitales
    df = df[df["Clasificación"].isin([
        "HOSPITALES O CLINICAS DE ATENCION GENERAL",
        "HOSPITALES O CLINICAS DE ATENCION ESPECIALIZADA"
    ])]
    
    # Corregir UBIGEO (rellenar con ceros)
    df['UBIGEO'] = df['UBIGEO'].astype(str).str.zfill(6)
    
    return df

@st.cache_data
def load_district_shapefile():
    """Carga shapefile de distritos"""
    import tempfile
    import os
    
    # Clonar repositorio temporal
    with tempfile.TemporaryDirectory() as tmpdir:
        os.system(f"git clone https://github.com/luchoravar/Hospitals-Access-Peru.git {tmpdir}/repo 2>/dev/null")
        maps = gpd.read_file(f"{tmpdir}/repo/code/data/Distritos/DISTRITOS.shp")
    
    maps = maps[['IDDIST', 'geometry']]
    maps = maps.rename({'IDDIST':'UBIGEO'}, axis=1)
    maps['UBIGEO'] = maps['UBIGEO'].astype(str).astype(int)
    maps = maps.to_crs(epsg=4326)
    
    return maps

@st.cache_data
def load_population_centers():
    """Carga centros poblados"""
    url = "https://github.com/luchoravar/Hospitals-Access-Peru/raw/main/code/data/CCPP_0.zip"
    CCPP = gpd.read_file(f"zip+{url}")
    CCPP = CCPP.to_crs("EPSG:4326")
    return CCPP

# ============================================
# FUNCIONES DE PROCESAMIENTO
# ============================================
@st.cache_data
def create_district_dataset(_maps, df):
    """Crea dataset agregado por distrito"""
    # Tabla de frecuencias por UBIGEO
    tabla_freq = df['UBIGEO'].value_counts().reset_index()
    tabla_freq.columns = ['UBIGEO', 'Frecuencia']
    
    # Merge
    _maps["UBIGEO"] = _maps["UBIGEO"].astype(int)
    tabla_freq["UBIGEO"] = tabla_freq["UBIGEO"].astype(int)
    
    dataset = pd.merge(_maps, tabla_freq, how="left", on="UBIGEO")
    dataset["Frecuencia"] = dataset["Frecuencia"].fillna(0).astype(int)
    
    return gpd.GeoDataFrame(dataset, geometry="geometry", crs="EPSG:4326")

@st.cache_data
def create_department_summary(df):
    """Crea resumen por departamento"""
    hosp_por_dep = df.groupby("Departamento", as_index=False).agg(
        Total_hospitales=("Nombre del establecimiento", "count")
    )
    hosp_por_dep = hosp_por_dep.sort_values(
        by="Total_hospitales",
        ascending=False
    ).reset_index(drop=True)
    
    return hosp_por_dep

@st.cache_data
def proximity_analysis(_CCPP, _maps):
    """Análisis de proximidad para Lima y Loreto"""
    # Filtrar regiones
    centros_sel = _CCPP[_CCPP["DEP"].isin(["LIMA", "LORETO"])].copy()
    hosp_sel = _maps[_maps["UBIGEO"].astype(str).str[:2].isin(['15', '16'])].copy()
    
    # Reproyectar a métrico
    centros_sel = centros_sel.to_crs("EPSG:32718")
    hosp_sel = hosp_sel.to_crs("EPSG:32718")
    
    # Buffers de 10 km
    centros_sel["buffer_10km"] = centros_sel.geometry.buffer(10000)
    
    # Contar hospitales
    hospitales_count = []
    for idx, row in centros_sel.iterrows():
        buffer = row["buffer_10km"]
        dentro = hosp_sel[hosp_sel.intersects(buffer)]
        hospitales_count.append(len(dentro))
    
    centros_sel["Hosp_10km"] = hospitales_count
    
    # Separar por región
    centros_lima = centros_sel[centros_sel["DEP"] == "LIMA"].copy()
    centros_loreto = centros_sel[centros_sel["DEP"] == "LORETO"].copy()
    
    # Identificar extremos
    results = {
        'aislado_lima': centros_lima.loc[centros_lima["Hosp_10km"].idxmin()],
        'concentrado_lima': centros_lima.loc[centros_lima["Hosp_10km"].idxmax()],
        'aislado_loreto': centros_loreto.loc[centros_loreto["Hosp_10km"].idxmin()],
        'concentrado_loreto': centros_loreto.loc[centros_loreto["Hosp_10km"].idxmax()]
    }
    
    # Hospitales en cada buffer
    for key in results.keys():
        centro = results[key]
        hosp_buffer = hosp_sel[hosp_sel.intersects(centro["buffer_10km"])].to_crs("EPSG:4326")
        results[f'hosp_{key}'] = hosp_buffer
    
    # Reproyectar centros a EPSG:4326
    for key in ['aislado_lima', 'concentrado_lima', 'aislado_loreto', 'concentrado_loreto']:
        results[key] = gpd.GeoDataFrame([results[key]], crs="EPSG:32718").to_crs("EPSG:4326").iloc[0]
    
    return results

# ============================================
# CARGAR DATOS
# ============================================
with st.spinner('Cargando datos... ⏳'):
    df = load_hospital_data()
    maps = load_district_shapefile()
    CCPP = load_population_centers()
    dataset = create_district_dataset(maps, df)
    hosp_por_dep = create_department_summary(df)

# ============================================
# SIDEBAR
# ============================================
st.sidebar.title("🏥 Análisis de Hospitales")
st.sidebar.markdown("---")
st.sidebar.info("""
**Proyecto:** Análisis Geoespacial de Hospitales en Perú

**Fuente de datos:**
- MINSA - IPRESS
- Centros Poblados

**Grupo:** 1-2-10
""")

# ============================================
# TABS PRINCIPALES
# ============================================
tab1, tab2, tab3 = st.tabs(["🗂️ Descripción de Datos", "🗺️ Mapas Estáticos & Departamentos", "🌍 Mapas Dinámicos"])

# ============================================
# TAB 1: DESCRIPCIÓN DE DATOS
# ============================================
with tab1:
    st.header("🗂️ Descripción de los Datos")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Hospitales", f"{len(df):,}")
    with col2:
        st.metric("Total de Distritos", f"{dataset['UBIGEO'].nunique():,}")
    with col3:
        st.metric("Total de Departamentos", f"{df['Departamento'].nunique()}")
    
    st.markdown("---")
    
    st.subheader("📋 Unidad de Análisis")
    st.write("""
    **Hospitales públicos operativos** en el Perú, según el registro IPRESS del Ministerio de Salud (MINSA).
    """)
    
    st.subheader("📊 Fuentes de Datos")
    st.write("""
    - **IPRESS (MINSA):** Registro de establecimientos de salud
    - **Centros Poblados:** Shapefile de localidades pobladas del Perú
    - **Distritos:** Shapefile de división político-administrativa
    """)
    
    st.subheader("🔍 Reglas de Filtrado")
    st.write("""
    1. **Condición:** Solo hospitales con estado "EN FUNCIONAMIENTO"
    2. **Coordenadas:** Solo registros con latitud/longitud válidas (no nulas, no cero)
    3. **Clasificación:** Solo establecimientos clasificados como:
       - Hospitales o clínicas de atención general
       - Hospitales o clínicas de atención especializada
    """)
    
    st.markdown("---")
    
    st.subheader("📈 Vista Previa de los Datos")
    st.dataframe(
        df[['Nombre del establecimiento', 'Departamento', 'Provincia', 
            'Clasificación', 'UBIGEO', 'NORTE', 'ESTE']].head(10),
        use_container_width=True
    )
    
    st.subheader("📊 Estadísticas Descriptivas")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Top 5 Departamentos con más hospitales:**")
        top_deps = df['Departamento'].value_counts().head(5)
        st.dataframe(top_deps.reset_index().rename(columns={'index':'Departamento', 'Departamento':'Cantidad'}))
    
    with col2:
        st.write("**Distribución por Clasificación:**")
        dist_clasif = df['Clasificación'].value_counts()
        st.dataframe(dist_clasif.reset_index().rename(columns={'index':'Tipo', 'Clasificación':'Cantidad'}))

# ============================================
# TAB 2: MAPAS ESTÁTICOS
# ============================================
with tab2:
    st.header("🗺️ Mapas Estáticos & Análisis por Departamento")
    
    # Mapa 1: Choropleth por distrito
    st.subheader("1️⃣ Distribución de Hospitales por Distrito")
    
    fig, ax = plt.subplots(figsize=(12, 12))
    dataset.plot(
        column='Frecuencia',
        cmap='Reds',
        linewidth=0.8,
        ax=ax,
        edgecolor='gray',
        legend=True,
        legend_kwds={'label': "Número de hospitales", 'orientation': "vertical"}
    )
    ax.set_title("Hospitales Públicos por Distrito", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Longitud", fontsize=12)
    ax.set_ylabel("Latitud", fontsize=12)
    ax.text(0.5, -0.05, "Fuente: Ministerio de Salud (MINSA) - Perú", 
            ha="center", fontsize=10, color="gray", transform=ax.transAxes)
    plt.tight_layout()
    st.pyplot(fig)
    
    st.markdown("---")
    
    # Mapa 2: Distritos sin hospitales
    st.subheader("2️⃣ Distritos sin Hospitales Públicos")
    
    fig, ax = plt.subplots(figsize=(12, 12))
    dataset.plot(
        column='Frecuencia',
        cmap='Reds',
        linewidth=0.5,
        ax=ax,
        edgecolor='gray',
        legend=False,
        alpha=0.6
    )
    dataset[dataset['Frecuencia'] == 0].plot(
        color='lightblue',
        edgecolor='black',
        linewidth=0.5,
        ax=ax,
        label='0 hospitales'
    )
    ax.set_title("Distritos sin Hospitales Públicos", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Longitud", fontsize=12)
    ax.set_ylabel("Latitud", fontsize=12)
    ax.legend(loc='lower left')
    ax.text(0.5, -0.05, "Fuente: Ministerio de Salud (MINSA) - Perú", 
            ha="center", fontsize=10, color="gray", transform=ax.transAxes)
    plt.tight_layout()
    st.pyplot(fig)
    
    distritos_sin_hosp = (dataset['Frecuencia'] == 0).sum()
    st.info(f"📊 **{distritos_sin_hosp}** distritos ({(distritos_sin_hosp/len(dataset)*100):.1f}%) no tienen hospitales públicos")
    
    st.markdown("---")
    
    # Mapa 3: Top 10 distritos
    st.subheader("3️⃣ Top 10 Distritos con Más Hospitales")
    
    top10 = dataset.nlargest(10, 'Frecuencia')
    
    fig, ax = plt.subplots(figsize=(12, 12))
    dataset.plot(
        color='lightgrey',
        edgecolor='white',
        linewidth=0.3,
        ax=ax
    )
    top10.plot(
        column='Frecuencia',
        cmap='viridis',
        linewidth=0.8,
        edgecolor='black',
        ax=ax,
        legend=True,
        legend_kwds={'label': "Número de hospitales", 'orientation': "vertical"}
    )
    ax.set_title("Top 10 Distritos con Más Hospitales Públicos", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Longitud", fontsize=12)
    ax.set_ylabel("Latitud", fontsize=12)
    ax.text(0.5, -0.05, "Fuente: Ministerio de Salud (MINSA) - Perú", 
            ha="center", fontsize=10, color="gray", transform=ax.transAxes)
    plt.tight_layout()
    st.pyplot(fig)
    
    st.markdown("---")
    
    # Análisis por Departamento
    st.subheader("📊 Análisis por Departamento")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("**Resumen de Hospitales por Departamento**")
        st.dataframe(hosp_por_dep, use_container_width=True, height=400)
        
        st.metric("Mayor cantidad", 
                  f"{hosp_por_dep.iloc[0]['Departamento']}: {hosp_por_dep.iloc[0]['Total_hospitales']}")
        st.metric("Menor cantidad", 
                  f"{hosp_por_dep.iloc[-1]['Departamento']}: {hosp_por_dep.iloc[-1]['Total_hospitales']}")
    
    with col2:
        fig, ax = plt.subplots(figsize=(10, 10))
        sns.barplot(
            data=hosp_por_dep,
            x="Total_hospitales",
            y="Departamento",
            palette="Reds_r",
            ax=ax
        )
        ax.set_title("Número de Hospitales por Departamento", fontsize=14, fontweight="bold")
        ax.set_xlabel("Total de hospitales", fontsize=12)
        ax.set_ylabel("Departamento", fontsize=12)
        plt.tight_layout()
        st.pyplot(fig)

# ============================================
# TAB 3: MAPAS DINÁMICOS
# ============================================
with tab3:
    st.header("🌍 Mapas Dinámicos Interactivos")
    
    # Mapa Nacional Choropleth
    st.subheader("1️⃣ Mapa Nacional: Hospitales por Distrito")
    
    with st.spinner('Generando mapa nacional...'):
        # Crear GeoDataFrame de hospitales
        hospitales_gdf = gpd.GeoDataFrame(
            df.copy(),
            geometry=gpd.points_from_xy(df["ESTE"], df["NORTE"]),
            crs="EPSG:32718"
        )
        hospitales_4326 = hospitales_gdf.to_crs(epsg=4326)
        
        # Preparar dataset para choropleth
        dataset_choro = dataset.copy()
        dataset_choro["UBIGEO"] = dataset_choro["UBIGEO"].astype(str)
        geojson_distritos = dataset_choro.to_json()
        
        # Crear mapa
        m_national = folium.Map(location=[-9.19, -75.02], zoom_start=5, tiles="CartoDB positron")
        
        # Choropleth
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
        ).add_to(m_national)
        
        # Tooltip
        folium.GeoJson(
            data=geojson_distritos,
            name="Distritos (tooltip)",
            tooltip=folium.GeoJsonTooltip(
                fields=["UBIGEO", "Frecuencia"],
                aliases=["UBIGEO:", "N° hospitales:"],
                localize=True
            ),
            style_function=lambda x: {'fillOpacity':0, 'color': 'none'}
        ).add_to(m_national)
        
        # MarkerCluster
        marker_cluster = MarkerCluster(name="Hospitales").add_to(m_national)
        for _, row in hospitales_4326.iterrows():
            popup_text = f"{row.get('Nombre del establecimiento','Hospital')}<br>Dept: {row.get('Departamento','')}"
            folium.Marker(
                location=[row.geometry.y, row.geometry.x],
                popup=popup_text,
                icon=folium.Icon(color="red", icon="plus-sign")
            ).add_to(marker_cluster)
        
        folium.LayerControl().add_to(m_national)
        
        folium_static(m_national, width=1200, height=600)
    
    st.markdown("---")
    
    # Mapa de Proximidad Lima & Loreto
    st.subheader("2️⃣ Análisis de Proximidad: Lima & Loreto")
    st.info("🔍 Radio de análisis: 10 km alrededor de cada centro poblado")
    
    with st.spinner('Calculando análisis de proximidad...'):
        proximity_results = proximity_analysis(CCPP, maps)
        
        # Mostrar resultados
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔴 Lima")
            st.metric("Centro más aislado", 
                      proximity_results['aislado_lima']['NOM_POBLAD'],
                      f"{proximity_results['aislado_lima']['Hosp_10km']} hospitales")
            st.metric("Centro más concentrado", 
                      proximity_results['concentrado_lima']['NOM_POBLAD'],
                      f"{proximity_results['concentrado_lima']['Hosp_10km']} hospitales")
        
        with col2:
            st.markdown("### 🟠 Loreto")
            st.metric("Centro más aislado", 
                      proximity_results['aislado_loreto']['NOM_POBLAD'],
                      f"{proximity_results['aislado_loreto']['Hosp_10km']} hospitales")
            st.metric("Centro más concentrado", 
                      proximity_results['concentrado_loreto']['NOM_POBLAD'],
                      f"{proximity_results['concentrado_loreto']['Hosp_10km']} hospitales")
        
        # Crear mapa
        m_proximity = folium.Map(location=[-9.19, -75.02], zoom_start=6, tiles='OpenStreetMap')
        
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
                    popup="Hospital"
                ).add_to(m)
        
        # Dibujar todos los centros
        dibujar_centro(m_proximity, proximity_results['aislado_lima'], "red", "red", 
                       "🔴 LIMA - Aislado", proximity_results['hosp_aislado_lima'])
        dibujar_centro(m_proximity, proximity_results['concentrado_lima'], "green", "green", 
                       "🟢 LIMA - Concentrado", proximity_results['hosp_concentrado_lima'])
        dibujar_centro(m_proximity, proximity_results['aislado_loreto'], "orange", "orange", 
                       "🟠 LORETO - Aislado", proximity_results['hosp_aislado_loreto'])
        dibujar_centro(m_proximity, proximity_results['concentrado_loreto'], "blue", "blue", 
                       "🔵 LORETO - Concentrado", proximity_results['hosp_concentrado_loreto'])
        
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
        m_proximity.get_root().html.add_child(folium.Element(legend_html))
        
        folium_static(m_proximity, width=1200, height=600)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    <p>🏥 <b>Análisis Geoespacial de Hospitales en Perú</b></p>
    <p>Fuente de datos: Ministerio de Salud (MINSA) - Perú | Grupo 1-2-10</p>
</div>
""", unsafe_allow_html=True)
