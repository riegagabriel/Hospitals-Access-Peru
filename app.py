# -*- coding: utf-8 -*-
"""
Aplicación Streamlit: Análisis Geoespacial de Hospitales en Perú
Grupo 1-2-10

COMBINACIÓN: 
- Estructura de tabs del compañero
- Tus datos y análisis específicos
- Tus mapas HTML pre-generados
"""

import streamlit as st
import pandas as pd
import requests
from io import StringIO
import matplotlib.pyplot as plt
import seaborn as sns

# ============================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================
st.set_page_config(
    page_title="Hospitales Perú - Análisis Geoespacial", 
    layout="wide"
)
st.title('Dashboard Geoespacial de Hospitales en Perú')

# ============================================
# FUNCIONES DE CARGA DE DATOS (TUS DATOS)
# ============================================
@st.cache_data
def load_hospital_data():
    """Carga y procesa datos de hospitales IPRESS desde GitHub (TUS FILTROS)"""
    try:
        url = "https://github.com/luchoravar/Hospitals-Access-Peru/raw/main/code/data/IPRESS.csv"
        r = requests.get(url)
        r.raise_for_status()
        raw_data = r.content
        texto = raw_data.decode("latin1", errors="ignore")
        
        # Crear DataFrame
        df = pd.read_csv(StringIO(texto))
        
        # TUS FILTROS ESPECÍFICOS:
        # 1. Solo hospitales operativos
        df = df[df["Condición"] == "EN FUNCIONAMIENTO"]
        
        # 2. Coordenadas válidas (no nulas, no cero)
        df = df.dropna(subset=["NORTE", "ESTE"])
        df = df[(df["NORTE"] != 0) & (df["ESTE"] != 0)]
        
        # 3. Solo hospitales (no otros establecimientos)
        df = df[df["Clasificación"].isin([
            "HOSPITALES O CLINICAS DE ATENCION GENERAL",
            "HOSPITALES O CLINICAS DE ATENCION ESPECIALIZADA"
        ])]
        
        # Corregir UBIGEO (tu método)
        df['UBIGEO'] = df['UBIGEO'].astype(str).str.zfill(6)
        df = df.rename(columns={'NORTE': 'latitud', 'ESTE': 'longitud'})
        
        return df
        
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

@st.cache_data
def create_department_summary(df):
    """Crea resumen por departamento (TU ANÁLISIS)"""
    hosp_por_dep = df.groupby("Departamento", as_index=False).agg(
        Total_hospitales=("Nombre del establecimiento", "count")
    )
    hosp_por_dep = hosp_por_dep.sort_values(
        by="Total_hospitales",
        ascending=False
    ).reset_index(drop=True)
    
    return hosp_por_dep

# ============================================
# FUNCIONES PARA CARGAR TUS MAPAS HTML
# ============================================
def load_html_map(map_url):
    """Carga mapa HTML desde GitHub"""
    try:
        response = requests.get(map_url)
        if response.status_code == 200:
            return response.text
        else:
            return None
    except:
        return None

def display_html_map(html_content, height=600):
    """Muestra mapa HTML en Streamlit"""
    if html_content:
        st.components.v1.html(html_content, height=height, scrolling=True)
    else:
        st.warning("El mapa no está disponible en este momento")

# URLs DE TUS MAPAS HTML
MAP_URLS = {
    "choropleth_nacional": "https://raw.githubusercontent.com/luchoravar/Hospitals-Access-Peru/main/choropleth_hospitales_distrito.html",
    "proximidad_lima_loreto": "https://raw.githubusercontent.com/luchoravar/Hospitals-Access-Peru/main/task2_proximity_lima_loreto.html",
    "proximidad_general": "https://raw.githubusercontent.com/luchoravar/Hospitals-Access-Peru/main/proximidad_hospitales.html"
}

# ============================================
# CARGAR DATOS
# ============================================
with st.spinner('Cargando datos y mapas...'):
    df_hospitales = load_hospital_data()
    hosp_por_dep = create_department_summary(df_hospitales) if not df_hospitales.empty else None

# ============================================
# TABS PRINCIPALES - ESTRUCTURA REQUERIDA
# ============================================
tab1, tab2, tab3 = st.tabs([
    "🗂️ Data Description", 
    "🗺️ Static Maps & Department Analysis", 
    "🌍 Dynamic Maps"
])

# ============================================
# TAB 1: DATA DESCRIPTION
# ============================================
with tab1:
    st.header("🗂️ Data Description")
    
    if df_hospitales.empty:
        st.error("No se pudieron cargar los datos")
    else:
        # UNIT OF ANALYSIS
        st.subheader("Unit of Analysis")
        st.write("""
        **Operational public hospitals in Peru** - Hospitales públicos en funcionamiento 
        según el registro IPRESS del Ministerio de Salud (MINSA).
        """)
        
        # DATA SOURCES
        st.subheader("Data Sources")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("""
            **📊 MINSA – IPRESS**
            - Registro nacional de establecimientos de salud
            - 20,819 registros iniciales
            - Filtrado a hospitales operativos con coordenadas válidas
            """)
        
        with col2:
            st.write("""
            **📍 Population Centers**  
            - Shapefile de centros poblados del Perú
            - Usado para análisis de proximidad en Lima y Loreto
            - Cálculo de buffers de 10 km
            """)
        
        # FILTERING RULES
        st.subheader("Filtering Rules")
        
        filtering_rules = [
            "✅ **Operational status**: Solo 'EN FUNCIONAMIENTO'",
            "✅ **Valid coordinates**: Eliminados registros con coordenadas nulas o (0, 0)",
            "✅ **Hospital types**: Solo 'HOSPITALES O CLINICAS DE ATENCION GENERAL' y 'HOSPITALES O CLINICAS DE ATENCION ESPECIALIZADA'",
            "✅ **UBIGEO standardization**: Todos los códigos estandarizados a 6 dígitos"
        ]
        
        for rule in filtering_rules:
            st.write(rule)
        
        st.markdown("---")
        
        # DATA PREVIEW
        st.subheader("Data Preview")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Hospitales", len(df_hospitales))
        with col2:
            st.metric("Departamentos", df_hospitales['Departamento'].nunique())
        with col3:
            st.metric("Registros Finales", f"{len(df_hospitales):,}")
        
        st.write("**Muestra de los datos:**")
        st.dataframe(
            df_hospitales[[
                'Nombre del establecimiento', 
                'Departamento', 
                'Provincia', 
                'Clasificación',
                'UBIGEO'
            ]].head(8),
            use_container_width=True
        )

# ============================================
# TAB 2: STATIC MAPS & DEPARTMENT ANALYSIS
# ============================================
with tab2:
    st.header("🗺️ Static Maps & Department Analysis")
    
    if df_hospitales.empty:
        st.error("No hay datos disponibles")
    else:
        # DEPARTMENT ANALYSIS (TU ANÁLISIS)
        st.subheader("Department Analysis")
        
        # Summary Table
        st.write("**Tabla Resumen por Departamento**")
        st.dataframe(hosp_por_dep, use_container_width=True, height=400)
        
        # Department Metrics
        col1, col2 = st.columns(2)
        
        with col1:
            if not hosp_por_dep.empty:
                st.metric(
                    "Departamento con más hospitales",
                    f"{hosp_por_dep.iloc[0]['Departamento']}",
                    f"{hosp_por_dep.iloc[0]['Total_hospitales']} hospitales"
                )
        
        with col2:
            if not hosp_por_dep.empty:
                st.metric(
                    "Departamento con menos hospitales", 
                    f"{hosp_por_dep.iloc[-1]['Departamento']}",
                    f"{hosp_por_dep.iloc[-1]['Total_hospitales']} hospitales"
                )
        
        # Bar Chart (como tu compañero pero con tus datos)
        st.write("**Gráfico de Barras - Hospitales por Departamento**")
        
        # Preparamos datos para el gráfico (top 15)
        chart_data = hosp_por_dep.set_index('Departamento')['Total_hospitales'].head(15)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.barplot(
            x=chart_data.values,
            y=chart_data.index,
            ax=ax,
            palette="Reds_r"
        )
        ax.set_title('Top 15 Departamentos con más Hospitales', fontsize=16)
        ax.set_xlabel('Número de Hospitales')
        st.pyplot(fig)
        
        st.markdown("---")
        
        # STATIC MAPS SECTION
        st.subheader("Static Maps")
        st.info("Mapas estáticos generados con GeoPandas - Visualización de distribución de hospitales")
        
        # Mapa 1: Choropleth por distrito
        st.write("**1. Distribución de Hospitales por Distrito**")
        html_choropleth = load_html_map(MAP_URLS["choropleth_nacional"])
        display_html_map(html_choropleth, height=500)

# ============================================
# TAB 3: DYNAMIC MAPS
# ============================================
with tab3:
    st.header("🌍 Dynamic Maps")
    
    # NATIONAL CHOROPLETH + MARKERS
    st.subheader("National Choropleth + Markers")
    st.write("""
    **Mapa nacional interactivo** que combina:
    - Capa coroplética por distrito (Folium)
    - Clústeres de marcadores para hospitales individuales
    - Tooltips con información detallada
    - Control de capas interactivo
    """)
    
    html_national = load_html_map(MAP_URLS["choropleth_nacional"])
    display_html_map(html_national, height=600)
    
    st.markdown("---")
    
    # PROXIMITY MAPS - LIMA & LORETO
    st.subheader("Proximity Analysis: Lima & Loreto")
    st.write("""
    **Análisis de proximidad** para las regiones de Lima y Loreto (radio de 10 km):
    - Identificación de centros más aislados y concentrados
    - Visualización de buffers y hospitales dentro del radio
    - Comparación entre región costera y selvática
    """)
    
    # Métricas de proximidad (de tu análisis)
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🏙️ Lima**")
        st.write("• Mayor densidad hospitalaria")
        st.write("• Mejor acceso en áreas urbanas")
        st.write("• Centros concentrados vs aislados")
    
    with col2:
        st.write("**🌳 Loreto**")
        st.write("• Mayor desafío de acceso")
        st.write("• Baja densidad hospitalaria") 
        st.write("• Aislamiento en comunidades")
    
    html_proximity = load_html_map(MAP_URLS["proximidad_lima_loreto"])
    display_html_map(html_proximity, height=600)
    
    # Mapa adicional de proximidad general
    st.markdown("---")
    st.subheader("Mapa de Proximidad General")
    html_general = load_html_map(MAP_URLS["proximidad_general"])
    display_html_map(html_general, height=500)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p><b>Análisis Geoespacial de Hospitales en Perú</b> | Grupo 1-2-10 | Fuente: MINSA IPRESS</p>
</div>
""", unsafe_allow_html=True)
