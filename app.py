import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

st.set_page_config(page_title="Análisis Geoespacial de Hospitales en el Perú", layout="wide")

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

# Crear directorio output si no existe
OUTPUT_DIR.mkdir(exist_ok=True)

# Cargar los DataFrames desde los archivos Excel
try:
    df_departamento = pd.read_excel("frecuencia_departamento.xlsx")
    df_distrito = pd.read_excel("frecuencia_distrito.xlsx") 
    df_provincia = pd.read_excel("frecuencia_provincia.xlsx")
    
    # Renombrar columnas para consistencia
    df_departamento = df_departamento.rename(columns={'DEPARTAMEN': 'Departamento', 'Cant de Hosp': 'Cantidad_Hospitales'})
    df_distrito = df_distrito.rename(columns={'DISTRITO': 'Distrito', 'Cant de Hosp': 'Cantidad_Hospitales'})
    df_provincia = df_provincia.rename(columns={'PROVINCIA': 'Provincia', 'Cant de Hosp': 'Cantidad_Hospitales'})
    
except FileNotFoundError as e:
    st.error(f"Error al cargar los archivos Excel: {e}")
    df_departamento = pd.DataFrame()
    df_distrito = pd.DataFrame()
    df_provincia = pd.DataFrame()

## Tabs 
tab1, tab2, tab3 = st.tabs(['📊 Análisis Estadístico', '🗺️ Mapas y análisis estático', '🌍 Mapas dinámicos'])

# contenido de tab1 - Análisis Estadístico
with tab1:
    st.subheader('Análisis Estadístico por División Política')
    
    # Departamento
    st.subheader('🏢 Por Departamento')
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Tabla de Departamentos**")
        if not df_departamento.empty:
            st.dataframe(df_departamento.sort_values('Cantidad_Hospitales', ascending=False), use_container_width=True)
        else:
            st.warning("No hay datos de departamentos disponibles")
    
    with col2:
        st.write("**Gráfico de Departamentos**")
        if not df_departamento.empty:
            st.bar_chart(df_departamento.set_index('Departamento')['Cantidad_Hospitales'])
        else:
            st.warning("No hay datos para graficar")
    
    # Provincia
    st.subheader('🏛️ Por Provincia')
    col3, col4 = st.columns(2)
    
    with col3:
        st.write("**Top 10 Provincias**")
        if not df_provincia.empty:
            top_provincias = df_provincia.nlargest(10, 'Cantidad_Hospitales')
            st.dataframe(top_provincias, use_container_width=True)
        else:
            st.warning("No hay datos de provincias disponibles")
    
    with col4:
        st.write("**Gráfico de Top 10 Provincias**")
        if not df_provincia.empty:
            top_provincias = df_provincia.nlargest(10, 'Cantidad_Hospitales')
            st.bar_chart(top_provincias.set_index('Provincia')['Cantidad_Hospitales'])
        else:
            st.warning("No hay datos para graficar")
    
    # Distrito
    st.subheader('🏘️ Por Distrito')
    col5, col6 = st.columns(2)
    
    with col5:
        st.write("**Top 10 Distritos**")
        if not df_distrito.empty:
            top_distritos = df_distrito.nlargest(10, 'Cantidad_Hospitales')
            st.dataframe(top_distritos, use_container_width=True)
        else:
            st.warning("No hay datos de distritos disponibles")
    
    with col6:
        st.write("**Gráfico de Top 10 Distritos**")
        if not df_distrito.empty:
            top_distritos = df_distrito.nlargest(10, 'Cantidad_Hospitales')
            st.bar_chart(top_distritos.set_index('Distrito')['Cantidad_Hospitales'])
        else:
            st.warning("No hay datos para graficar")
    
    # Métricas resumen
    st.subheader('📈 Métricas Resumen')
    if not df_departamento.empty and not df_distrito.empty and not df_provincia.empty:
        col7, col8, col9, col10 = st.columns(4)
        
        with col7:
            total_hospitales = df_departamento['Cantidad_Hospitales'].sum()
            st.metric("Total Hospitales", total_hospitales)
        
        with col8:
            total_departamentos = len(df_departamento)
            st.metric("Total Departamentos", total_departamentos)
        
        with col9:
            total_provincias = len(df_provincia)
            st.metric("Total Provincias", total_provincias)
        
        with col10:
            total_distritos = len(df_distrito)
            st.metric("Total Distritos", total_distritos)

# contenido de tab2
with tab2:
    st.subheader('Análisis por Distrito')

    # columnas
    c, d, e = st.columns(3)

    with c:    
        st.subheader(" 🏥 Total de Hospitales Públicos por Distrito")
        try:
            st.image(str(OUTPUT_DIR / 'hops_pub_distri.png'), width=500)
        except FileNotFoundError:
            st.warning("Imagen no encontrada: hops_pub_distri.png")
            st.info("Ejecuta primero el código de generación de mapas estáticos")

    with d: 
        st.subheader(' 🏥 Distritos sin hospitales')
        try:
            st.image(str(OUTPUT_DIR / 'distrit_sin_hosp.png'), width=500)
        except FileNotFoundError:
            st.warning("Imagen no encontrada: distrit_sin_hosp.png")
            st.info("Ejecuta primero el código de generación de mapas estáticos")

    with e:
        st.subheader(' 🏥 Top 10 distritos con mayor número de hospitales')
        try:
            st.image(str(OUTPUT_DIR / 'top10distrit.png'), width=500)
        except FileNotFoundError:
            st.warning("Imagen no encontrada: top10distrit.png")
            st.info("Ejecuta primero el código de generación de mapas estáticos")

    st.subheader('Análisis de Proximidad')

    with st.container():
        st.markdown("""
        <style>
        .bordered-container {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            margin: 10px 0;
        }
        </style>
        <div class="bordered-container">
        """, unsafe_allow_html=True)
        
        st.subheader('Lima')
        try:
            with open(OUTPUT_DIR / "proximidad_hospitales.html", 'r', encoding='utf-8') as f:
                fol_1 = f.read()
            st.components.v1.html(fol_1, height=600)
        except FileNotFoundError:
            st.warning("Archivo HTML no encontrado: proximidad_hospitales.html")
            st.info("Ejecuta primero el código de generación de mapas interactivos")
        
        st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.subheader('Mapas Interactivos')
    
    k = st.columns(1)[0]

    with k:
        st.subheader('Lima - Loreto')
        try:
            with open(OUTPUT_DIR / "task2_proximity_lima_loreto_pruebaindivi.html", 'r', encoding='utf-8') as f:
                fol_4 = f.read()
            st.components.v1.html(fol_4, height=600)
        except FileNotFoundError:
            st.warning("Archivo HTML no encontrado: task2_proximity_lima_loreto_pruebaindivi.html")
            st.info("Ejecuta primero el código de generación de mapas interactivos")
    
    m = st.columns(1)[0]

    with m:
        st.markdown("""
#### Lima

* El mapa muestra un área concentrada en Lima, en La Victoria con cerca de 28 hospitales. Al contrario, Rigopampa se ve aislado, con 0.

#### Loreto

* En Loreto observamos que la mayor cantidad de hospitales corresponde a San Antonio de Gallito, con 6. Mientras que Pueblo Nuevo, apenas cuenta con 1.
""")

# Información adicional
st.sidebar.markdown("""
### Información del Proyecto
**Análisis Geoespacial de Hospitales en Perú**

Este dashboard presenta:
- Análisis estadístico por división política
- Distribución de hospitales por distrito
- Mapas de proximidad en Lima y Loreto
- Visualizaciones interactivas

**Fuente de datos:** Ministerio de Salud (MINSA)
""")
