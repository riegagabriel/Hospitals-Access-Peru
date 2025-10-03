# -*- coding: utf-8 -*-
"""
Aplicación Streamlit: Análisis Geoespacial de Hospitales en Perú
Grupo 1-2-10

ESTRUCTURA DE 3 TABS REQUERIDA:
1. 🗂️ Data Description
2. 🗺️ Static Maps & Department Analysis  
3. 🌍 Dynamic Maps
"""

import streamlit as st
import pandas as pd
import requests
from io import StringIO
import base64

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
    """Carga y procesa datos de hospitales IPRESS desde GitHub"""
    try:
        url = "https://github.com/luchoravar/Hospitals-Access-Peru/raw/main/code/data/IPRESS.csv"
        r = requests.get(url)
        r.raise_for_status()
        raw_data = r.content
        texto = raw_data.decode("latin1", errors="ignore")
        
        # Crear DataFrame
        df = pd.read_csv(StringIO(texto))
        
        # FILTRADO SEGÚN REQUISITOS:
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
        
        # Corregir UBIGEO
        df['UBIGEO'] = df['UBIGEO'].astype(str).str.zfill(6)
        df = df.rename(columns={'NORTE': 'lat', 'ESTE': 'lon'})
        
        return df
        
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

@st.cache_data
def create_department_summary(df):
    """Crea resumen por departamento para Tab 2"""
    hosp_por_dep = df.groupby("Departamento", as_index=False).agg(
        Total_hospitales=("Nombre del establecimiento", "count")
    )
    hosp_por_dep = hosp_por_dep.sort_values(
        by="Total_hospitales",
        ascending=False
    ).reset_index(drop=True)
    
    return hosp_por_dep

# ============================================
# FUNCIONES PARA MAPAS
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

# URLs de mapas pre-generados (debes tener estos en tu repo)
MAP_URLS = {
    "static_choropleth": "https://raw.githubusercontent.com/luchoravar/Hospitals-Access-Peru/main/choropleth_hospitales_distrito.html",
    "static_zero_hospitals": "https://raw.githubusercontent.com/luchoravar/Hospitals-Access-Peru/main/mapa_sin_hospitales.html", 
    "static_top10": "https://raw.githubusercontent.com/luchoravar/Hospitals-Access-Peru/main/mapa_top10.html",
    "dynamic_national": "https://raw.githubusercontent.com/luchoravar/Hospitals-Access-Peru/main/choropleth_hospitales_distrito.html",
    "dynamic_proximity": "https://raw.githubusercontent.com/luchoravar/Hospitals-Access-Peru/main/task2_proximity_lima_loreto.html"
}

# ============================================
# CARGAR DATOS
# ============================================
with st.spinner('Cargando datos de hospitales... ⏳'):
    df = load_hospital_data()
    hosp_por_dep = create_department_summary(df) if not df.empty else None

# ============================================
# SIDEBAR
# ============================================
st.sidebar.title("🏥 Análisis de Hospitales")
st.sidebar.markdown("---")
st.sidebar.info("""
**Proyecto:** Análisis Geoespacial  
**Fuente:** MINSA - IPRESS  
**Grupo:** 1-2-10
""")

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
    
    if df.empty:
        st.error("No se pudieron cargar los datos")
    else:
        # UNIT OF ANALYSIS
        st.subheader("Unit of Analysis")
        st.write("""
        **Operational public hospitals in Peru** - Establecimientos de salud públicos 
        que se encuentran en funcionamiento según el registro IPRESS del Ministerio de Salud (MINSA).
        """)
        
        # DATA SOURCES
        st.subheader("Data Sources")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("""
            **📊 MINSA – IPRESS**
            - Registro nacional de establecimientos de salud
            - Información sobre ubicación, capacidad y servicios
            - Estado operativo de cada establecimiento
            """)
        
        with col2:
            st.write("""
            **📍 Population Centers**  
            - Shapefile de centros poblados del Perú
            - Ubicaciones geográficas de localidades
            - Usado para análisis de proximidad
            """)
        
        # FILTERING RULES
        st.subheader("Filtering Rules")
        st.write("""
        Se aplicaron los siguientes filtros para garantizar la calidad de los datos:
        """)
        
        filtering_rules = [
            "✅ **Condición operativa**: Solo establecimientos marcados como 'EN FUNCIONAMIENTO'",
            "✅ **Coordenadas válidas**: Eliminados registros con coordenadas nulas o (0, 0)",
            "✅ **Tipología hospitalaria**: Solo 'HOSPITALES O CLINICAS DE ATENCION GENERAL' y 'HOSPITALES O CLINICAS DE ATENCION ESPECIALIZADA'",
            "✅ **UBIGEO completo**: Todos los códigos UBIGEO estandarizados a 6 dígitos"
        ]
        
        for rule in filtering_rules:
            st.write(rule)
        
        st.markdown("---")
        
        # DATA PREVIEW
        st.subheader("Data Preview")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Hospitales", len(df))
        with col2:
            st.metric("Departamentos", df['Departamento'].nunique())
        with col3:
            st.metric("Registros Filtrados", "100% operativos")
        
        st.write("**Muestra de los datos:**")
        st.dataframe(
            df[[
                'Nombre del establecimiento', 
                'Departamento', 
                'Provincia', 
                'Clasificación',
                'UBIGEO'
            ]].head(10),
            use_container_width=True
        )
        
        # DATA QUALITY
        st.subheader("Data Quality Summary")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Completitud de datos:**")
            st.write(f"• Registros iniciales: 20,819")
            st.write(f"• Registros finales: {len(df)}")
            st.write(f"• Tasa de retención: {(len(df)/20819*100):.1f}%")
            
        with col2:
            st.write("**Cobertura geográfica:**")
            st.write(f"• Departamentos cubiertos: {df['Departamento'].nunique()}")
            st.write(f"• Provincias cubiertas: {df['Provincia'].nunique()}")
            st.write(f"• Distritos cubiertos: {df['UBIGEO'].nunique()}")

# ============================================
# TAB 2: STATIC MAPS & DEPARTMENT ANALYSIS
# ============================================
with tab2:
    st.header("🗺️ Static Maps & Department Analysis")
    
    if df.empty:
        st.error("No hay datos disponibles para generar mapas")
    else:
        # STATIC MAPS SECTION
        st.subheader("Static Maps (GeoPandas)")
        
        # Map 1: Choropleth por distrito
        st.write("**1. Distribución de Hospitales por Distrito**")
        html_choropleth = load_html_map(MAP_URLS["static_choropleth"])
        display_html_map(html_choropleth, height=500)
        st.caption("Mapa coroplético que muestra la densidad de hospitales públicos por distrito en el Perú")
        
        st.markdown("---")
        
        # Map 2: Distritos sin hospitales
        st.write("**2. Distritos sin Hospitales Públicos**")
        html_zero = load_html_map(MAP_URLS["static_zero_hospitals"])
        display_html_map(html_zero, height=500)
        st.caption("Distritos que no cuentan con ningún hospital público operativo (resaltados en azul)")
        
        st.markdown("---")
        
        # Map 3: Top 10 distritos
        st.write("**3. Top 10 Distritos con Más Hospitales**")
        html_top10 = load_html_map(MAP_URLS["static_top10"])
        display_html_map(html_top10, height=500)
        st.caption("Los 10 distritos con mayor concentración de hospitales públicos")
        
        st.markdown("---")
        
        # DEPARTMENT ANALYSIS SECTION
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
        
        # Bar Chart (simulado con Streamlit)
        st.write("**Gráfico de Barras - Hospitales por Departamento**")
        
        # Preparamos datos para el gráfico
        chart_data = hosp_por_dep.set_index('Departamento')['Total_hospitales'].head(15)
        st.bar_chart(chart_data)
        
        st.caption("Distribución del número de hospitales públicos por departamento (top 15)")

# ============================================
# TAB 3: DYNAMIC MAPS
# ============================================
with tab3:
    st.header("🌍 Dynamic Maps")
    
    # NATIONAL CHOROPLETH + MARKERS
    st.subheader("National Choropleth + Markers")
    st.write("""
    **Mapa nacional interactivo** que combina:
    - Capa coroplética por distrito
    - Clústeres de marcadores para hospitales individuales
    - Tooltips con información detallada
    - Control de capas para personalizar la visualización
    """)
    
    html_national = load_html_map(MAP_URLS["dynamic_national"])
    display_html_map(html_national, height=600)
    
    st.markdown("---")
    
    # PROXIMITY MAPS - LIMA & LORETO
    st.subheader("Proximity Analysis: Lima & Loreto")
    st.write("""
    **Análisis de proximidad** para las regiones de Lima y Loreto:
    - Radio de análisis: 10 km alrededor de cada centro poblado
    - Identificación de centros más aislados y concentrados
    - Visualización de buffers y hospitales dentro del radio
    - Comparación entre región costera (Lima) y selvática (Loreto)
    """)
    
    # Métricas de proximidad
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🏙️ Lima**")
        st.write("• Región con mayor densidad hospitalaria")
        st.write("• Mejor acceso en áreas urbanas")
        st.write("• Desafíos en zonas periurbanas")
    
    with col2:
        st.write("**🌳 Loreto**")
        st.write("• Región con mayor desafío de acceso")
        st.write("• Baja densidad hospitalaria")
        st.write("• Aislamiento en comunidades ribereñas")
    
    html_proximity = load_html_map(MAP_URLS["dynamic_proximity"])
    display_html_map(html_proximity, height=600)
    
    # Leyenda explicativa
    st.info("""
    **🎨 Leyenda del Mapa de Proximidad:**
    - 🔴 **Lima - Aislado**: Centro poblado con menor acceso a hospitales en Lima
    - 🟢 **Lima - Concentrado**: Centro poblado con mayor acceso a hospitales en Lima  
    - 🟠 **Loreto - Aislado**: Centro poblado con menor acceso a hospitales en Loreto
    - 🔵 **Loreto - Concentrado**: Centro poblado con mayor acceso a hospitales en Loreto
    - ● **Puntos**: Hospitales dentro del radio de 10 km
    """)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p><b>Análisis Geoespacial de Hospitales en Perú</b> | Grupo 1-2-10 | MINSA IPRESS</p>
</div>
""", unsafe_allow_html=True)
