import streamlit as st
import pandas as pd
import plotly.express as px
import gdown
import os

# ─────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────
st.set_page_config(page_title="Dashboard Operaciones GEA", layout="wide")

# ─────────────────────────────
# LOGIN
# ─────────────────────────────
PASSWORD = "OperacionesGEA"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Acceso restringido")
    password_input = st.text_input("Ingrese la contraseña", type="password")

    if st.button("Ingresar"):
        if password_input == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

# ─────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────
@st.cache_data(show_spinner=True)
def cargar_datos():

    files = {
        "2023": "1jVvFPdg5A5ySOQtKeuO1pLU6zG2cTa51",
        "2024": "1YnRJtc6_NyXmXjmOMLP8oINOmqr7e3_I",
        "2025": "1_etz-VsH66PpmnHVEo2H-wVgwkd4DKMl",
        "2026": "1oZIhTS7zPGcHFF5cpM2LdnbWuUlyK2N6"
    }

    dfs = []

    for year, file_id in files.items():
        url = f"https://drive.google.com/uc?id={file_id}"
        output = f"/tmp/{year}.csv"

        if not os.path.exists(output):
            gdown.download(url, output, quiet=True)

        df_temp = pd.read_csv(output, encoding="latin1")
        dfs.append(df_temp)

    df = pd.concat(dfs, ignore_index=True)
    df.columns = df.columns.str.replace('\ufeff', '', regex=False).str.strip()

    return df


df = cargar_datos()

# ─────────────────────────────
# PROCESAMIENTO FECHA
# ─────────────────────────────
fecha_col = [c for c in df.columns if "fecha" in c.lower() and "asistencia" in c.lower()][0]

df[fecha_col] = pd.to_datetime(df[fecha_col], dayfirst=True, errors="coerce")
df = df.dropna(subset=[fecha_col])

df["AÑO"] = df[fecha_col].dt.year
df["MES"] = df[fecha_col].dt.month

meses_dict = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
}

df["MES_NOMBRE"] = df["MES"].map(meses_dict)

df["Número Asistencia"] = df["Número Asistencia"].astype(str).str.strip()

df["Total de Costo Global"] = (
    df["Total de Costo Global"]
    .astype(str)
    .str.replace("$", "", regex=False)
    .str.replace(",", "", regex=False)
    .astype(float)
)

# ─────────────────────────────
# FILTROS (DEPURADOS)
# ─────────────────────────────
st.sidebar.header("🎛️ Filtros")

df_temp = df.copy()

def filtro(label, columna):
    opciones = sorted(df_temp[columna].dropna().unique())
    seleccion = st.sidebar.multiselect(label, opciones)
    return seleccion

# Eliminados Año, Mes y País

grupo = filtro("Grupo de Servicio", "Grupo de Servicio")
if grupo:
    df_temp = df_temp[df_temp["Grupo de Servicio"].isin(grupo)]

servicio = filtro("Nombre del Servicio", "Nombre del Servicio")
if servicio:
    df_temp = df_temp[df_temp["Nombre del Servicio"].isin(servicio)]

estado = filtro("Estado de Asistencia", "Estado de Asistencia")
if estado:
    df_temp = df_temp[df_temp["Estado de Asistencia"].isin(estado)]

canal = filtro("Canal Origen", "Canal Origen")
if canal:
    df_temp = df_temp[df_temp["Canal Origen"].isin(canal)]

proveedor = filtro("Proveedor", "Nombre del Proveedor")
if proveedor:
    df_temp = df_temp[df_temp["Nombre del Proveedor"].isin(proveedor)]

df_f = df_temp.copy()

if df_f.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# ─────────────────────────────
# KPIs
# ─────────────────────────────
st.title("📊 Dashboard Operaciones GEA")

total_asistencias = df_f["Número Asistencia"].count()
costo_total = df_f["Total de Costo Global"].sum()
costo_promedio = costo_total / total_asistencias if total_asistencias > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("🔢 Total asistencias", f"{total_asistencias:,}")
c2.metric("💲 Costo total", f"${costo_total:,.2f}")
c3.metric("💲 Costo promedio", f"${costo_promedio:,.2f}")

# ─────────────────────────────
# GRÁFICOS
# ─────────────────────────────
st.subheader("📊 Resumen Ejecutivo")

col1, col2 = st.columns(2)

# Total asistencias por año
total_anual = df_f.groupby("AÑO")["Número Asistencia"].count().reset_index(name="Total")

fig1 = px.bar(total_anual, x="AÑO", y="Total", text_auto=True, title="Total Asistencias por Año")
col1.plotly_chart(fig1, use_container_width=True)

# Asistencias por mes
orden_meses = ["Ene","Feb","Mar","Abr","May","Jun",
               "Jul","Ago","Sep","Oct","Nov","Dic"]

asist_mes = df_f.groupby(["MES_NOMBRE","MES"])["Número Asistencia"].count().reset_index(name="Total")

fig2 = px.bar(
    asist_mes,
    x="MES_NOMBRE",
    y="Total",
    category_orders={"MES_NOMBRE": orden_meses},
    title="Asistencias por Mes"
)

col2.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────
# TOP SERVICIOS
# ─────────────────────────────
st.subheader("🏆 Top Servicios")

top_servicios = (
    df_f.groupby("Nombre del Servicio")["Número Asistencia"]
    .count()
    .reset_index(name="Total")
    .sort_values("Total", ascending=False)
    .head(10)
)

st.plotly_chart(px.bar(top_servicios, x="Nombre del Servicio", y="Total"), use_container_width=True)

# ─────────────────────────────
# TABLA ESTADO
# ─────────────────────────────
st.subheader("📋 Estado de Asistencia")

tabla_estado = (
    df_f.groupby("Estado de Asistencia")["Número Asistencia"]
    .count()
    .reset_index(name="Total")
    .sort_values("Total", ascending=False)
)

st.dataframe(tabla_estado, use_container_width=True)

# ─────────────────────────────
# PIE
# ─────────────────────────────
st.subheader("🥧 Distribución por Estado")

st.plotly_chart(
    px.pie(tabla_estado, names="Estado de Asistencia", values="Total", hole=0.4),
    use_container_width=True
)
