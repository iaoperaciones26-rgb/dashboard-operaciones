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

df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")
df = df.dropna(subset=[fecha_col])

df["AÑO"] = df[fecha_col].dt.year
df["MES"] = df[fecha_col].dt.month

# Diccionario meses abreviados
meses_dict = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
}

df["MES_NOMBRE"] = df["MES"].map(meses_dict)

# Limpiar Número Asistencia
df["Número Asistencia"] = df["Número Asistencia"].astype(str).str.strip()

# Limpiar Costo
df["Total de Costo Global"] = (
    df["Total de Costo Global"]
    .astype(str)
    .str.replace("$", "", regex=False)
    .str.replace(",", "", regex=False)
    .astype(float)
)

# ─────────────────────────────
# FILTROS COMPLETOS
# ─────────────────────────────
st.sidebar.header("🎛️ Filtros")

def multiselect_filter(label, column):
    if column in df.columns:
        return st.sidebar.multiselect(
            label,
            sorted(df[column].dropna().unique())
        )
    return []

anio = multiselect_filter("Año", "AÑO")

# 🔵 FILTRO MES CON NOMBRE
mes_nombre = multiselect_filter("Mes", "MES_NOMBRE")

estado = multiselect_filter("Estado de Asistencia", "Estado de Asistencia")
canal = multiselect_filter("Canal Origen", "Canal Origen")
grupo = multiselect_filter("Grupo de Servicio", "Grupo de Servicio")
servicio = multiselect_filter("Nombre del Servicio", "Nombre del Servicio")
subservicio = multiselect_filter("Subservicio", "Nombre del Subservicio")
especialidad = multiselect_filter("Especialidad Médica", "ESPECIALIDAD MEDICA (CITAS)")
proveedor = multiselect_filter("Proveedor", "Nombre del Proveedor")
pais = multiselect_filter("País", "País")
provincia = multiselect_filter("Provincia", "Provincia")
ciudad = multiselect_filter("Ciudad", "Ciudad")
local_foraneo = multiselect_filter("Local / Foráneo", "Local_Foráneo")
tipo_cliente = multiselect_filter("Tipo de Cliente", "TIPO DE CLIENTE")
cliente = multiselect_filter("Cliente Institucional", "Cliente Institucional")
cuenta = multiselect_filter("Nombre de la cuenta", "Nombre de la cuenta")
plan = multiselect_filter("Nombre del plan", "Nombre del plan")
evento = multiselect_filter("Tipo de Evento", "Tipo de Evento")

df_f = df.copy()

if anio: df_f = df_f[df_f["AÑO"].isin(anio)]
if mes_nombre: df_f = df_f[df_f["MES_NOMBRE"].isin(mes_nombre)]
if estado: df_f = df_f[df_f["Estado de Asistencia"].isin(estado)]
if canal: df_f = df_f[df_f["Canal Origen"].isin(canal)]
if grupo: df_f = df_f[df_f["Grupo de Servicio"].isin(grupo)]
if servicio: df_f = df_f[df_f["Nombre del Servicio"].isin(servicio)]
if subservicio: df_f = df_f[df_f["Nombre del Subservicio"].isin(subservicio)]
if especialidad: df_f = df_f[df_f["ESPECIALIDAD MEDICA (CITAS)"].isin(especialidad)]
if proveedor: df_f = df_f[df_f["Nombre del Proveedor"].isin(proveedor)]
if pais: df_f = df_f[df_f["País"].isin(pais)]
if provincia: df_f = df_f[df_f["Provincia"].isin(provincia)]
if ciudad: df_f = df_f[df_f["Ciudad"].isin(ciudad)]
if local_foraneo: df_f = df_f[df_f["Local_Foráneo"].isin(local_foraneo)]
if tipo_cliente: df_f = df_f[df_f["TIPO DE CLIENTE"].isin(tipo_cliente)]
if cliente: df_f = df_f[df_f["Cliente Institucional"].isin(cliente)]
if cuenta: df_f = df_f[df_f["Nombre de la cuenta"].isin(cuenta)]
if plan: df_f = df_f[df_f["Nombre del plan"].isin(plan)]
if evento: df_f = df_f[df_f["Tipo de Evento"].isin(evento)]

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
# TENDENCIAS
# ─────────────────────────────
st.subheader("📈 Tendencias")

asist_mes = (
    df_f.groupby(["AÑO", "MES_NOMBRE", "MES"])["Número Asistencia"]
    .count()
    .reset_index(name="Total asistencias")
    .sort_values("MES")
)

fig1 = px.line(
    asist_mes,
    x="MES_NOMBRE",
    y="Total asistencias",
    color="AÑO",
    title="Asistencias por mes"
)

st.plotly_chart(fig1, use_container_width=True)

costo_mes = (
    df_f.groupby(["AÑO", "MES_NOMBRE", "MES"])["Total de Costo Global"]
    .sum()
    .reset_index()
    .sort_values("MES")
)

fig2 = px.line(
    costo_mes,
    x="MES_NOMBRE",
    y="Total de Costo Global",
    color="AÑO",
    title="Costo mensual"
)

st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────
# TOPS
# ─────────────────────────────
st.subheader("🏆 Top servicios y especialidades")

col_a, col_b = st.columns(2)

top_servicios = (
    df_f.groupby("Nombre del Servicio")["Número Asistencia"]
    .count()
    .reset_index(name="Total asistencias")
    .sort_values("Total asistencias", ascending=False)
    .head(10)
)

fig_serv = px.bar(top_servicios, x="Nombre del Servicio", y="Total asistencias")
col_a.plotly_chart(fig_serv, use_container_width=True)

top_especialidad = (
    df_f.groupby("ESPECIALIDAD MEDICA (CITAS)")["Número Asistencia"]
    .count()
    .reset_index(name="Total asistencias")
    .sort_values("Total asistencias", ascending=False)
    .head(10)
)

fig_esp = px.bar(top_especialidad, x="ESPECIALIDAD MEDICA (CITAS)", y="Total asistencias")
col_b.plotly_chart(fig_esp, use_container_width=True)
