import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

st.set_page_config(page_title="Análisis Geoespacial de Hospitales en el Perú", layout="wide")


BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"


## Tabs 

tab2, tab3 = st.tabs([' 🗺️ Mapas y análisis estático', ' 🌍 Mapas dinámicos'])


# contenido de tab2
with tab2:
    
    st.subheader('Análisis por Distrito')

    # columnas 

    c, d, e = st.columns(3, border= True)

    with c:    
        st.subheader(" 🏥 Total de Hospitales Públicos por Distrito")

        st.image(str(OUTPUT_DIR / 'hops_pub_distri.png'), width= 500)

    with d: 
        st.subheader(' 🏥 Distritos sin hospitales')

        st.image(str(OUTPUT_DIR / 'distrit_sin_hosp.png'), width= 500)

    with e:
        st.subheader(' 🏥 Top 10 distritos con mayor número de hospitales')
        
        st.image(str(OUTPUT_DIR / 'top10distrit.png'), width= 500)


    st.subheader('Análisis por Departamento')

    with st.container():
        # columnas
        f,g,h = st.columns(3, border= True)
        
        with f:
            st.subheader('Tabla Resumen')
            st.dataframe(hosp_dist)
            
        with g:
            st.subheader('Cantidad de Hospitales publicos operativos por Departamento')
            st.bar_chart(hosp_dist, x= 'DEPARTAMENTO', y = 'TOTAL_HOSPITALES', horizontal= True, sort= '-TOTAL_HOSPITALES')
    
    st.subheader('Análisis de Proximidad')

    with st.container():
        #columnas
        (i,) = st.columns(1, border= True)

        with i:

            with st.container():

                st.subheader('Lima')
                with open(OUTPUT_DIR / "proximidad_hospitales.html", 'r', encoding='utf-8') as f:
                    fol_1 = f.read()

                st.components.v1.html(fol_1, height = 800)

with tab3:

     k, = st.columns(3, border= True)

    with k:
        st.subheader('Lima - Loreto')

        with open(OUTPUT_DIR / "task2_proximity_lima_loreto_pruebaindivi.html", 'r', encoding='utf-8') as f:
                    fol_4 = f.read()

        st.components.v1.html(fol_4, height = 800)

    
    
    (m, ) = st.columns(1, border= True)

    with m:
        st.markdown("""
#### Lima

* El mapa muestra un un aréa concentrada en Lima, en La Victoria con cerca de 28 hospitales. Al contrario, Rigopampa se ve aislado, con 0.


#### Loreto

* En Loreto observamos que la mayor cantidad de hospitales corresponde a San Antonio de Gallito, con 6. Mientras que Pueblo Nuevo, apenas cuenta con 1.
""")
