import streamlit as st
import pandas as pd
import os
import plotly.express as px

# ─────────────────────────────
# CONFIGURACIÓN GENERAL
# ─────────────────────────────
st.set_page_config(
    page_title="Dashboard Operaciones GEA",
    layout="wide"
)

# ─────────────────────────────
# CONTRASEÑA
# ─────────────────────────────
PASSWORD = "OperacionesGEA"

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 Acceso restringido")
        password_input = st.text_input(
            "Ingrese la contraseña",
            type="password"
        )
        if st.button("Ingresar"):
            if password_input == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        st.stop()

check_password()

# ─────────────────────────────
# CARGA CSV 2026 (REEMPLAZO)
# ─────────────────────────────
st.sidebar.header("📤 Actualizar información 2026")

uploaded_file = st.sidebar.file_uploader(
    "Subir CSV 2026",
    type="csv"
)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

if uploaded_file:
    df_new = pd.read_csv(uploaded_file, encoding="latin1")
    df_new.to_csv(f"{DATA_DIR}/asistencias_2026.csv", index=False)
    st.sidebar.success("CSV 2026 actualizado correctamente")

# ─────────────────────────────
# LECTURA HISTÓRICA
# ─────────────────────────────
files = [
    "asistencias_2023.csv",
    "asistencias_2024.csv",
    "asistencias_2025.csv",
    "asistencias_2026.csv"
]

dfs = []
for f in files:
    path = f"{DATA_DIR}/{f}"
    if os.path.exists(path):
        temp = pd.read_csv(path, encoding="latin1")
        temp["AÑO"] = int(f.split("_")[1].replace(".csv", ""))
        dfs.append(temp)

if not dfs:
    st.warning("No hay datos cargados.")
    st.stop()

df = pd.concat(dfs, ignore_index=True)

# ─────────────────────────────
# FECHAS Y LIMPIEZA
# ─────────────────────────────
df["Fecha creación de asistencia"] = pd.to_datetime(
    df["Fecha creación de asistencia"],
    errors="coerce"
)

df["MES"] = df["Fecha creación de asistencia"].dt.month

for col in ["Total de Costo Global", "Total de importe pagado"]:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype(float)
    )

# ─────────────────────────────
# FILTROS
# ─────────────────────────────
st.sidebar.header("🎛️ Filtros")

def multiselect_filter(label, column):
    return st.sidebar.multiselect(
        label,
        sorted(df[column].dropna().unique())
    )

anio = multiselect_filter("Año", "AÑO")
mes = multiselect_filter("Mes", "MES")
canal = multiselect_filter("Canal de Origen", "Canal Origen")
estado = multiselect_filter("Estado de Asistencia", "Estado de Asistencia")
servicio = multiselect_filter("Nombre del Servicio", "Nombre del Servicio")
subservicio = multiselect_filter("Subservicio", "Nombre del Subservicio")
proveedor = multiselect_filter("Proveedor", "Nombre del Proveedor")
ciudad = multiselect_filter("Ciudad", "Ciudad")
provincia = multiselect_filter("Provincia", "Provincia")
pais = multiselect_filter("País", "País")
grupo = multiselect_filter("Grupo de Servicio", "Grupo de Servicio")
cliente = multiselect_filter("Cliente Institucional", "Cliente Institucional")
tipo_cliente = multiselect_filter("Tipo de Cliente", "TIPO DE CLIENTE")
evento = multiselect_filter("Tipo de Evento", "Tipo de Evento")
especialidad = multiselect_filter("Especialidad Médica", "ESPECIALIDAD MEDICA (CITAS)")
local_foraneo = multiselect_filter("Local / Foráneo", "Local_Foráneo")
cuenta = multiselect_filter("Nombre de la cuenta", "Nombre de la cuenta")
plan = multiselect_filter("Nombre del plan", "Nombre del plan")

df_f = df.copy()

if anio:
    df_f = df_f[df_f["AÑO"].isin(anio)]

if mes:
    df_f = df_f[df_f["MES"].isin(mes)]

if canal:
    df_f = df_f[df_f["Canal Origen"].isin(canal)]

if estado:
    df_f = df_f[df_f["Estado de Asistencia"].isin(estado)]

if servicio:
    df_f = df_f[df_f["Nombre del Servicio"].isin(servicio)]

if subservicio:
    df_f = df_f[df_f["Nombre del Subservicio"].isin(subservicio)]

if proveedor:
    df_f = df_f[df_f["Nombre del Proveedor"].isin(proveedor)]

if ciudad:
    df_f = df_f[df_f["Ciudad"].isin(ciudad)]

if provincia:
    df_f = df_f[df_f["Provincia"].isin(provincia)]

if pais:
    df_f = df_f[df_f["País"].isin(pais)]

if grupo:
    df_f = df_f[df_f["Grupo de Servicio"].isin(grupo)]

if cliente:
    df_f = df_f[df_f["Cliente Institucional"].isin(cliente)]

if tipo_cliente:
    df_f = df_f[df_f["TIPO DE CLIENTE"].isin(tipo_cliente)]

if evento:
    df_f = df_f[df_f["Tipo de Evento"].isin(evento)]

if especialidad:
    df_f = df_f[df_f["ESPECIALIDAD MEDICA (CITAS)"].isin(especialidad)]

if local_foraneo:
    df_f = df_f[df_f["Local_Foráneo"].isin(local_foraneo)]

if cuenta:
    df_f = df_f[df_f["Nombre de la cuenta"].isin(cuenta)]

if plan:
    df_f = df_f[df_f["Nombre del plan"].isin(plan)]

# ─────────────────────────────
# KPIs
# ─────────────────────────────
st.title("📊 Dashboard Operaciones GEA")

total_asistencias = df_f["Número Asistencia"].count()
costo_total = df_f["Total de Costo Global"].sum()
costo_promedio = costo_total / total_asistencias if total_asistencias > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("🔢 Total asistencias", f"{total_asistencias:,}")
col2.metric("💲 Costo total", f"${costo_total:,.2f}")
col3.metric("💲 Costo promedio", f"${costo_promedio:,.2f}")

# ─────────────────────────────
# GRÁFICOS DE TENDENCIA
# ─────────────────────────────
st.subheader("📈 Tendencias")

asist_mes = (
    df_f.groupby("MES")["Número Asistencia"]
    .count()
    .reset_index(name="Total asistencias")
)

fig1 = px.line(
    asist_mes,
    x="MES",
    y="Total asistencias",
    title="Asistencias por mes"
)
st.plotly_chart(fig1, use_container_width=True)

costo_mes = (
    df_f.groupby("MES")["Total de Costo Global"]
    .sum()
    .reset_index()
)

fig2 = px.line(
    costo_mes,
    x="MES",
    y="Total de Costo Global",
    title="Costo mensual (USD)"
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

fig_serv = px.bar(
    top_servicios,
    x="Nombre del Servicio",
    y="Total asistencias",
    title="Top 10 Servicios (por número de asistencias)"
)
col_a.plotly_chart(fig_serv, use_container_width=True)

top_especialidad = (
    df_f.groupby("ESPECIALIDAD MEDICA (CITAS)")["Número Asistencia"]
    .count()
    .reset_index(name="Total asistencias")
    .sort_values("Total asistencias", ascending=False)
    .head(10)
)

fig_esp = px.bar(
    top_especialidad,
    x="ESPECIALIDAD MEDICA (CITAS)",
    y="Total asistencias",
    title="Top 10 Especialidades Médicas (por número de asistencias)"
)
col_b.plotly_chart(fig_esp, use_container_width=True)
