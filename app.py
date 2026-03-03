import streamlit as st 
import pandas as pd
import plotly.express as px
import gdown
import os

# ─────────────────────────────
# CONFIGURACIÓN GENERAL
# ─────────────────────────────
st.set_page_config(
    page_title="Dashboard Operaciones GEA",
    layout="wide"
)

# ─────────────────────────────
# CONTRASEÑA ÚNICA
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
# CARGA DE DATOS DESDE GOOGLE DRIVE
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

df[fecha_col] = pd.to_datetime(
    df[fecha_col],
    dayfirst=True,
    errors="coerce"
)

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
# FILTROS DEPENDIENTES
# ─────────────────────────────

st.sidebar.header("🎛️ Filtros")

df_temp = df.copy()

def filtro_cascada(label, columna):
    opciones = sorted(df_temp[columna].dropna().unique())
    seleccion = st.sidebar.multiselect(label, opciones)
    return seleccion

anio = filtro_cascada("Año", "AÑO")
if anio:
    df_temp = df_temp[df_temp["AÑO"].isin(anio)]

mes_nombre = filtro_cascada("Mes", "MES_NOMBRE")
if mes_nombre:
    df_temp = df_temp[df_temp["MES_NOMBRE"].isin(mes_nombre)]

grupo = filtro_cascada("Grupo de Servicio", "Grupo de Servicio")
if grupo:
    df_temp = df_temp[df_temp["Grupo de Servicio"].isin(grupo)]

servicio = filtro_cascada("Nombre del Servicio", "Nombre del Servicio")
if servicio:
    df_temp = df_temp[df_temp["Nombre del Servicio"].isin(servicio)]

subservicio = filtro_cascada("Subservicio", "Nombre del Subservicio")
if subservicio:
    df_temp = df_temp[df_temp["Nombre del Subservicio"].isin(subservicio)]

estado = filtro_cascada("Estado de Asistencia", "Estado de Asistencia")
if estado:
    df_temp = df_temp[df_temp["Estado de Asistencia"].isin(estado)]

canal = filtro_cascada("Canal Origen", "Canal Origen")
if canal:
    df_temp = df_temp[df_temp["Canal Origen"].isin(canal)]

especialidad = filtro_cascada("Especialidad Médica", "ESPECIALIDAD MEDICA (CITAS)")
if especialidad:
    df_temp = df_temp[df_temp["ESPECIALIDAD MEDICA (CITAS)"].isin(especialidad)]

proveedor = filtro_cascada("Proveedor", "Nombre del Proveedor")
if proveedor:
    df_temp = df_temp[df_temp["Nombre del Proveedor"].isin(proveedor)]

df_f = df_temp.copy()

# 🔒 PROTECCIÓN ANTI-CRASH
if df_f.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# ─────────────────────────────
# KPIs
# ─────────────────────────────

st.title("📊 Dashboard Operaciones GEA")

filtros_activos = any([
    anio, mes_nombre, grupo, servicio,
    subservicio, estado, canal,
    especialidad, proveedor
])

df_kpi = df if not filtros_activos else df_f

total_asistencias = df_kpi["Número Asistencia"].count()
costo_total = df_kpi["Total de Costo Global"].sum()
costo_promedio = costo_total / total_asistencias if total_asistencias > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("🔢 Total asistencias", f"{total_asistencias:,}")
c2.metric("💲 Costo total", f"${costo_total:,.2f}")
c3.metric("💲 Costo promedio", f"${costo_promedio:,.2f}")

# ─────────────────────────────
# RESUMEN EJECUTIVO
# ─────────────────────────────

st.subheader("📊 Resumen Ejecutivo")

col1, col2 = st.columns(2)

orden_meses = ["Ene","Feb","Mar","Abr","May","Jun",
               "Jul","Ago","Sep","Oct","Nov","Dic"]
orden_anios = sorted(df_f["AÑO"].unique())

total_anual = (
    df_f.groupby("AÑO")["Número Asistencia"]
    .count()
    .reset_index(name="Total Asistencias")
)

fig_total_asist = px.bar(
    total_anual,
    x="AÑO",
    y="Total Asistencias",
    text_auto=True,
    title="Total Asistencias por Año"
)

fig_total_asist.update_layout(yaxis_title=None)
col1.plotly_chart(fig_total_asist, use_container_width=True)

asist_mes = (
    df_f.groupby(["AÑO", "MES_NOMBRE", "MES"])["Número Asistencia"]
    .count()
    .reset_index(name="Total Asistencias")
)

fig_asist_mes = px.bar(
    asist_mes,
    x="MES_NOMBRE",
    y="Total Asistencias",
    color="AÑO",
    barmode="group",
    category_orders={
        "MES_NOMBRE": orden_meses,
        "AÑO": orden_anios
    },
    title="Asistencias por Mes"
)

fig_asist_mes.update_layout(yaxis_title=None)
col2.plotly_chart(fig_asist_mes, use_container_width=True)

col3, col4 = st.columns(2)

costo_anual = (
    df_f.groupby("AÑO")["Total de Costo Global"]
    .sum()
    .reset_index(name="Total Costo")
)

fig_total_costo = px.bar(
    costo_anual,
    x="AÑO",
    y="Total Costo",
    text_auto=True,
    title="Total Costo por Año"
)

fig_total_costo.update_layout(yaxis_title=None)
fig_total_costo.update_yaxes(tickprefix="$")

col3.plotly_chart(fig_total_costo, use_container_width=True)

costo_mes = (
    df_f.groupby(["AÑO", "MES_NOMBRE", "MES"])["Total de Costo Global"]
    .sum()
    .reset_index(name="Total Costo")
)

fig_costo_mes = px.bar(
    costo_mes,
    x="MES_NOMBRE",
    y="Total Costo",
    color="AÑO",
    barmode="group",
    category_orders={
        "MES_NOMBRE": orden_meses,
        "AÑO": orden_anios
    },
    title="Costos Mensual"
)

fig_costo_mes.update_layout(yaxis_title=None)
fig_costo_mes.update_yaxes(tickprefix="$")

col4.plotly_chart(fig_costo_mes, use_container_width=True)
