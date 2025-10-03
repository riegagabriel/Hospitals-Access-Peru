import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

st.set_page_config(page_title="Análisis Geoespacial de Hospitales en el Perú", layout="wide")

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

# Crear directorio output si no existe
OUTPUT_DIR.mkdir(exist_ok=True)

# Cargar datos (necesitas tener estos datos disponibles)
# Para este ejemplo, crearemos datos de ejemplo o puedes cargarlos desde archivos
try:
    hosp_dist = pd.DataFrame({
        'DEPARTAMENTO': ['LIMA', 'CAJAMARCA', 'PUNO', 'TUMBES'],
        'TOTAL_HOSPITALES': [92, 17, 16, 3]
    })
except:
    hosp_dist = pd.DataFrame({
        'DEPARTAMENTO': ['LIMA', 'CAJAMARCA', 'PUNO', 'TUMBES'],
        'TOTAL_HOSPITALES': [92, 17, 16, 3]
    })

## Tabs 
tab2, tab3 = st.tabs([' 🗺️ Mapas y análisis estático', ' 🌍 Mapas dinámicos'])

# contenido de tab2
with tab2:
    st.subheader('Análisis por Distrito')

    # columnas 
    c, d, e = st.columns(3, border=True)

    with c:    
        st.subheader(" 🏥 Total de Hospitales Públicos por Distrito")
        try:
            st.image(str(OUTPUT_DIR / 'hops_pub_distri.png'), width=500)
        except FileNotFoundError:
            st.warning("Imagen no encontrada: hops_pub_distri.png")

    with d: 
        st.subheader(' 🏥 Distritos sin hospitales')
        try:
            st.image(str(OUTPUT_DIR / 'distrit_sin_hosp.png'), width=500)
        except FileNotFoundError:
            st.warning("Imagen no encontrada: distrit_sin_hosp.png")

    with e:
        st.subheader(' 🏥 Top 10 distritos con mayor número de hospitales')
        try:
            st.image(str(OUTPUT_DIR / 'top10distrit.png'), width=500)
        except FileNotFoundError:
            st.warning("Imagen no encontrada: top10distrit.png")

    st.subheader('Análisis por Departamento')

    with st.container():
        # columnas
        f, g, h = st.columns(3, border=True)
        
        with f:
            st.subheader('Tabla Resumen')
            st.dataframe(hosp_dist)
            
        with g:
            st.subheader('Cantidad de Hospitales públicos operativos por Departamento')
            st.bar_chart(hosp_dist, x='TOTAL_HOSPITALES', y='DEPARTAMENTO', horizontal=True)
    
    st.subheader('Análisis de Proximidad')

    with st.container():
        # columnas
        i, = st.columns(1, border=True)

        with i:
            st.subheader('Lima')
            try:
                with open(OUTPUT_DIR / "proximidad_hospitales.html", 'r', encoding='utf-8') as f:
                    fol_1 = f.read()
                st.components.v1.html(fol_1, height=600)
            except FileNotFoundError:
                st.warning("Archivo HTML no encontrado: proximidad_hospitales.html")

with tab3:
    k, = st.columns(1, border=True)

    with k:
        st.subheader('Lima - Loreto')
        try:
            with open(OUTPUT_DIR / "task2_proximity_lima_loreto_pruebaindivi.html", 'r', encoding='utf-8') as f:
                fol_4 = f.read()
            st.components.v1.html(fol_4, height=600)
        except FileNotFoundError:
            st.warning("Archivo HTML no encontrado: task2_proximity_lima_loreto_pruebaindivi.html")
    
    m, = st.columns(1, border=True)

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
