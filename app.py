# app.py
import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium

# ================================
# 📂 Carga de datos desde GitHub
# ================================
# ⚠️ Reemplaza "TU_USUARIO" y "TU_REPO" con tu usuario y repositorio de GitHub
URL_BASE = "https://github.com/riegagabriel/Hospitals-Access-Peru/tree/main/code/data"

hospitales = gpd.read_file(URL_BASE + "hospitales.shp").to_crs(32718)
distritos = gpd.read_file(URL_BASE + "distritos.shp").to_crs(32718)
departamentos = gpd.read_file(URL_BASE + "departamentos.shp").to_crs(32718)
centros = gpd.read_file(URL_BASE + "centros_poblados.shp").to_crs(32718)

# ================================
# 📌 Task 1: Análisis Distrital
# ================================
def task1_distritos():
    st.subheader("Task 1: Hospitales por Distrito")

    hospitales_por_distrito = gpd.sjoin(hospitales, distritos, how="left").groupby("distrito").size().reset_index(name="n_hospitales")
    distritos_local = distritos.merge(hospitales_por_distrito, on="distrito", how="left").fillna({"n_hospitales": 0})

    distritos_sin = distritos_local[distritos_local["n_hospitales"] == 0]

    st.markdown("**Distritos sin hospitales**")
    st.write(distritos_sin[["distrito"]])

    top10 = distritos_local.sort_values("n_hospitales", ascending=False).head(10)
    st.markdown("**Top 10 distritos con más hospitales**")
    st.write(top10[["distrito", "n_hospitales"]])

    fig, ax = plt.subplots(figsize=(8, 8))
    distritos_local.plot(ax=ax, color="lightgrey", edgecolor="black")
    hospitales.plot(ax=ax, color="red", markersize=5, label="Hospitales")
    distritos_sin.boundary.plot(ax=ax, color="blue", linewidth=2, label="Distritos sin hospitales")
    plt.legend()
    st.pyplot(fig)

# ================================
# 📌 Task 2: Análisis Departamental
# ================================
def task2_departamentos():
    st.subheader("Task 2: Análisis Departamental")

    hospitales_por_dep = gpd.sjoin(hospitales, departamentos, how="left").groupby("departamento").size().reset_index(name="n_hospitales")
    departamentos_local = departamentos.merge(hospitales_por_dep, on="departamento", how="left").fillna({"n_hospitales": 0})

    st.write(hospitales_por_dep.sort_values("n_hospitales", ascending=False))

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(data=hospitales_por_dep.sort_values("n_hospitales", ascending=False), 
                x="n_hospitales", y="departamento", ax=ax, palette="viridis")
    st.pyplot(fig)

    fig, ax = plt.subplots(figsize=(8, 8))
    departamentos_local.plot(column="n_hospitales", cmap="OrRd", legend=True, ax=ax, edgecolor="black")
    plt.title("Número de Hospitales por Departamento")
    st.pyplot(fig)

# ================================
# 📌 Task 3: Proximidad (Centros Poblados)
# ================================
def task3_proximidad():
    st.subheader("Task 3: Análisis de Proximidad (10 km)")

    centros["buffer_10km"] = centros.geometry.buffer(10000)
    conteo_hosp = centros.buffer_10km.apply(lambda buf: hospitales.within(buf).sum())
    centros["n_hospitales_10km"] = conteo_hosp

    aislado = centros.loc[centros["n_hospitales_10km"].idxmin()]
    concentrado = centros.loc[centros["n_hospitales_10km"].idxmax()]

    st.write("📍 Centro más aislado:", aislado["nombre"], "(", aislado["n_hospitales_10km"], "hospitales en 10 km )")
    st.write("📍 Centro más concentrado:", concentrado["nombre"], "(", concentrado["n_hospitales_10km"], "hospitales en 10 km )")

    m = folium.Map(location=[-9.2, -75.0], zoom_start=6)
    folium.Circle(location=[aislado.geometry.y, aislado.geometry.x], radius=10000, color="red", 
                  tooltip=f"{aislado['nombre']} ({aislado['n_hospitales_10km']} hospitales)").add_to(m)
    folium.Circle(location=[concentrado.geometry.y, concentrado.geometry.x], radius=10000, color="green", 
                  tooltip=f"{concentrado['nombre']} ({concentrado['n_hospitales_10km']} hospitales)").add_to(m)
    st_folium(m, width=700, height=500)

# ================================
# 📌 Task 4: Streamlit App
# ================================
def main():
    st.title("🩺 Análisis de Hospitales en el Perú")

    tabs = st.tabs(["Task 1: Distritos", "Task 2: Departamentos", "Task 3: Proximidad"])

    with tabs[0]:
        task1_distritos()

    with tabs[1]:
        task2_departamentos()

    with tabs[2]:
        task3_proximidad()

if __name__ == "__main__":
    main()

