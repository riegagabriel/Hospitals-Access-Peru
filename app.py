import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

st.set_page_config(page_title="Análisis Geoespacial de Hospitales en el Perú", layout="wide")

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

# Crear directorio output si no existe
OUTPUT_DIR.mkdir(exist_ok=True)

## Tabs 
tab2, tab3 = st.tabs([' 🗺️ Mapas y análisis estático', ' 🌍 Mapas dinámicos'])

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
- Distribución de hospitales por distrito
- Análisis departamental
- Mapas de proximidad en Lima y Loreto
- Visualizaciones interactivas

**Fuente de datos:** Ministerio de Salud (MINSA)
""")
