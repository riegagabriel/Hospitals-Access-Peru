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
    
    # Renombrar columnas para consistencia - CORREGIDO
    df_departamento = df_departamento.rename(columns={'DEPARTAMEN': 'Departamento', 'Cant de Hosp': 'Cantidad_Hospitales'})
    df_distrito = df_distrito.rename(columns={'DISTRITO': 'Distrito', 'Cant de Hosp': 'Cantidad_Hospitales'})
    df_provincia = df_provincia.rename(columns={'PROVINCIA': 'Provincia', 'Cant de Hosp': 'Cantidad_Hospitales'})
    
except FileNotFoundError as e:
    st.error(f"Error al cargar los archivos Excel: {e}")
    df_departamento = pd.DataFrame()
    df_distrito = pd.DataFrame()
    df_provincia = pd.DataFrame()

# Para debug - mostrar si se cargaron los datos
st.write("Datos cargados:")
st.write(f"Departamentos: {len(df_departamento)} filas")
st.write(f"Distritos: {len(df_distrito)} filas") 
st.write(f"Provincias: {len(df_provincia)} filas")

# Resto de tu código...
