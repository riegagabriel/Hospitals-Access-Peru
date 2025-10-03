# -*- coding: utf-8 -*-
"""
Aplicación Streamlit: Análisis Geoespacial de Hospitales en Perú
ADAPTADO para Streamlit Cloud (sin GeoPandas)
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium import Marker, Circle, CircleMarker
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from io import StringIO, BytesIO
import json

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
# FUNCIONES DE CARGA DE DATOS (SIN GEOPANDAS)
# ============================================
@st.cache_data
def load_hospital_data():
    """Carga y procesa datos de hospitales IPRESS"""
    url = "https://github.com/luchoravar/Hospitals-Access-Peru/raw/main/code/data/IPRESS.csv"
    try:
        r = requests.get(url)
        r.raise_for_status()
        raw_data = r.content
        texto = raw_data.decode("latin1", errors="ignore")
        
        # Crear DataFrame
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
        
        # Renombrar columnas de coordenadas para claridad
        df = df.rename(columns={'NORTE': 'lat', 'ESTE': 'lon'})
        
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

@st.cache_data
def load_geojson_distritos():
    """Carga GeoJSON de distritos desde el repositorio"""
    try:
        # URL del GeoJSON (necesitarías convertirlo previamente)
        geojson_url = "https://raw.githubusercontent.com/luchoravar/Hospitals-Access-Peru/main/code/data/distritos_simplified.geojson"
        response = requests.get(geojson_url)
        return response.json()
    except:
        st.warning("GeoJSON no disponible. Usando datos básicos.")
        return None

@st.cache_data
def create_district_summary(df, geojson_data):
    """Crea resumen por distrito usando datos agregados"""
    if geojson_data and 'features' in geojson_data:
        # Extraer UBIGEOs del GeoJSON
        ubigeos = []
        for feature in geojson_data['features']:
            if 'properties' in feature and 'UBIGEO' in feature['properties']:
                ubigeos.append(feature['properties']['UBIGEO'])
        
        # Contar hospitales por UBIGEO
        hosp_por_ubigeo = df['UBIGEO'].value_counts().reset_index()
        hosp_por_ubigeo.columns = ['UBIGEO', 'Frecuencia']
        
        # Crear dataset completo
        summary_df = pd.DataFrame({'UBIGEO': ubigeos})
        summary_df = pd.merge(summary_df, hosp_por_ubigeo, on='UBIGEO', how='left')
        summary_df['Frecuencia'] = summary_df['Frecuencia'].fillna(0).astype(int)
        
        return summary_df
    else:
        # Fallback: solo datos de hospitales
        hosp_por_ubigeo = df['UBIGEO'].value_counts().reset_index()
        hosp_por_ubigeo.columns = ['UBIGEO', 'Frecuencia']
        return hosp_por_ubigeo

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

# ============================================
# FUNCIONES DE VISUALIZACIÓN ALTERNATIVAS
# ============================================
def create_choropleth_map(df, geojson_data):
    """Crea mapa choropleth usando Folium"""
    if not geojson_data:
        st.warning("No hay datos GeoJSON disponibles para el mapa choropleth")
        return folium.Map(location=[-9.19, -75.02], zoom_start=5)
    
    # Crear resumen de datos
    summary_df = create_district_summary(df, geojson_data)
    
    # Crear mapa base
    m = folium.Map(location=[-9.19, -75.02], zoom_start=5, tiles="CartoDB positron")
    
    # Añadir choropleth
    folium.Choropleth(
        geo_data=geojson_data,
        name="choropleth",
        data=summary_df,
        columns=["UBIGEO", "Frecuencia"],
        key_on="feature.properties.UBIGEO",
        fill_color="YlOrRd",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Número de hospitales por distrito",
        nan_fill_color="white"
    ).add_to(m)
    
    # Añadir tooltips
    folium.GeoJson(
        geojson_data,
        name="Distritos",
        tooltip=folium.GeoJsonTooltip(
            fields=["UBIGEO", "NOMBDIST"] if 'NOMBDIST' in geojson_data['features'][0]['properties'] else ["UBIGEO"],
            aliases=["UBIGEO:", "Distrito:"] if 'NOMBDIST' in geojson_data['features'][0]['properties'] else ["UBIGEO:", ""],
            localize=True
        ),
        style_function=lambda x: {
            'fillColor': 'transparent',
            'color': 'transparent',
            'weight': 0
        }
    ).add_to(m)
    
    # Añadir marcadores de hospitales
    marker_cluster = MarkerCluster(name="Hospitales").add_to(m)
    for _, row in df.iterrows():
        popup_text = f"""
        <b>{row.get('Nombre del establecimiento', 'Hospital')}</b><br>
        Departamento: {row.get('Departamento', '')}<br>
        Provincia: {row.get('Provincia', '')}<br>
        Tipo: {row.get('Clasificación', '')}
        """
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=row.get('Nombre del establecimiento', 'Hospital'),
            icon=folium.Icon(color="red", icon="plus-sign", prefix='glyphicon')
        ).add_to(marker_cluster)
    
    folium.LayerControl().add_to(m)
    return m

def create_basic_hospital_map(df):
    """Crea mapa básico con solo hospitales"""
    m = folium.Map(location=[-9.19, -75.02], zoom_start=5, tiles="CartoDB positron")
    
    # Agrupar por departamento para colores
    departamentos = df['Departamento'].unique()
    colors = plt.cm.Set3(np.linspace(0, 1, len(departamentos)))
    color_map = {dept: f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}" 
                 for dept, (r, g, b, _) in zip(departamentos, colors)}
    
    for _, row in df.iterrows():
        color = color_map.get(row['Departamento'], 'blue')
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=6,
            popup=f"{row['Nombre del establecimiento']} - {row['Departamento']}",
            tooltip=row['Nombre del establecimiento'],
            color=color,
            fill=True,
            fillColor=color
        ).add_to(m)
    
    # Añadir leyenda
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; 
                background-color: white; padding: 10px; border: 1px solid grey;
                border-radius: 5px; font-size: 12px;">
    <h4>Departamentos</h4>
    '''
    for dept, color in list(color_map.items())[:10]:  # Mostrar solo primeros 10
        legend_html += f'<p><span style="color:{color}">●</span> {dept}</p>'
    legend_html += '</div>'
    
    m.get_root().html.add_child(folium.Element(legend_html))
    return m

# ============================================
# CARGAR DATOS
# ============================================
with st.spinner('Cargando datos... ⏳'):
    df = load_hospital_data()
    geojson_data = load_geojson_distritos()
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

# Selector de tipo de mapa
map_type = st.sidebar.selectbox(
    "Tipo de Mapa",
    ["Mapa Básico con Hospitales", "Mapa Choropleth (si disponible)"]
)

# ============================================
# TABS PRINCIPALES
# ============================================
tab1, tab2, tab3 = st.tabs(["🗂️ Descripción de Datos", "🗺️ Análisis Estadístico", "🌍 Mapas Interactivos"])

# ============================================
# TAB 1: DESCRIPCIÓN DE DATOS
# ============================================
with tab1:
    st.header("🗂️ Descripción de los Datos")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Hospitales", f"{len(df):,}")
    with col2:
        st.metric("Departamentos", f"{df['Departamento'].nunique()}")
    with col3:
        st.metric("Provincias", f"{df['Provincia'].nunique()}")
    
    st.markdown("---")
    
    st.subheader("📋 Vista Previa de los Datos")
    st.dataframe(
        df[['Nombre del establecimiento', 'Departamento', 'Provincia', 
            'Clasificación', 'UBIGEO', 'lat', 'lon']].head(15),
        use_container_width=True
    )
    
    st.subheader("📊 Distribución Geográfica")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Top 10 Departamentos con más hospitales:**")
        top_deps = df['Departamento'].value_counts().head(10)
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.barplot(y=top_deps.index, x=top_deps.values, ax=ax, palette="viridis")
        ax.set_title("Hospitales por Departamento (Top 10)")
        ax.set_xlabel("Número de Hospitales")
        st.pyplot(fig)
    
    with col2:
        st.write("**Distribución por Tipo:**")
        tipo_counts = df['Clasificación'].value_counts()
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(tipo_counts.values, labels=tipo_counts.index, autopct='%1.1f%%', startangle=90)
        ax.set_title("Tipos de Hospitales")
        st.pyplot(fig)

# ============================================
# TAB 2: ANÁLISIS ESTADÍSTICO
# ============================================
with tab2:
    st.header("📊 Análisis Estadístico")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Resumen por Departamento")
        st.dataframe(hosp_por_dep, use_container_width=True, height=400)
    
    with col2:
        st.subheader("Estadísticas Clave")
        st.metric("Departamento con más hospitales", 
                 f"{hosp_por_dep.iloc[0]['Departamento']}", 
                 f"{hosp_por_dep.iloc[0]['Total_hospitales']} hospitales")
        st.metric("Departamento con menos hospitales", 
                 f"{hosp_por_dep.iloc[-1]['Departamento']}", 
                 f"{hosp_por_dep.iloc[-1]['Total_hospitales']} hospitales")
        st.metric("Promedio por departamento", 
                 f"{hosp_por_dep['Total_hospitales'].mean():.1f}")
    
    st.markdown("---")
    
    # Mapa de calor de coordenadas
    st.subheader("Densidad de Hospitales")
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Scatter plot de hospitales
    scatter = ax.scatter(df['lon'], df['lat'], alpha=0.6, c='red', s=20)
    ax.set_xlabel('Longitud')
    ax.set_ylabel('Latitud')
    ax.set_title('Distribución Geográfica de Hospitales en Perú')
    ax.grid(True, alpha=0.3)
    
    st.pyplot(fig)

# ============================================
# TAB 3: MAPAS INTERACTIVOS
# ============================================
with tab3:
    st.header("🌍 Mapas Interactivos")
    
    if map_type == "Mapa Choropleth (si disponible)" and geojson_data:
        st.subheader("Mapa Choropleth - Hospitales por Distrito")
        with st.spinner('Generando mapa choropleth...'):
            choropleth_map = create_choropleth_map(df, geojson_data)
            folium_static(choropleth_map, width=1200, height=600)
    else:
        st.subheader("Mapa de Distribución de Hospitales")
        st.info("💡 Mostrando mapa básico. Para mapa choropleth, necesitarías un archivo GeoJSON.")
        with st.spinner('Generando mapa de hospitales...'):
            basic_map = create_basic_hospital_map(df)
            folium_static(basic_map, width=1200, height=600)
    
    st.markdown("---")
    
    # Análisis de concentración por región
    st.subheader("🔍 Análisis de Concentración Regional")
    
    # Calcular densidad por departamento
    dept_stats = df.groupby('Departamento').agg({
        'Nombre del establecimiento': 'count',
        'lat': ['mean', 'std'],
        'lon': ['mean', 'std']
    }).round(2)
    
    dept_stats.columns = ['Num_Hospitales', 'Lat_Media', 'Lat_Std', 'Lon_Media', 'Lon_Std']
    dept_stats = dept_stats.sort_values('Num_Hospitales', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Estadísticas por Departamento:**")
        st.dataframe(dept_stats.head(10), use_container_width=True)
    
    with col2:
        st.write("**Departamentos con Mayor Dispersión:**")
        dept_stats['Dispersion'] = dept_stats['Lat_Std'] + dept_stats['Lon_Std']
        dispersos = dept_stats.nlargest(5, 'Dispersion')
        st.dataframe(dispersos[['Num_Hospitales', 'Dispersion']], use_container_width=True)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    <p>🏥 <b>Análisis Geoespacial de Hospitales en Perú</b> | Versión Adaptada para Streamlit Cloud</p>
    <p>Fuente de datos: Ministerio de Salud (MINSA) - Perú | Grupo 1-2-10</p>
</div>
""", unsafe_allow_html=True)
