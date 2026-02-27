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
        password_input = st.text_input("Ingrese la contraseña", type="password")

        if st.button("Ingresar"):
            if password_input == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        st.stop()

check_password()

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ─────────────────────────────
# CARGA HISTÓRICO 2023–2025
# ─────────────────────────────
st.sidebar.markdown("---")
st.sidebar.header("📦 Cargar histórico 2023–2025 (uno por uno)")

uploaded_hist = st.sidebar.file_uploader(
    "Subir un CSV histórico",
    type="csv",
    key="historico"
)

if uploaded_hist:

    df_temp = pd.read_csv(uploaded_hist, encoding="latin1")

    nombre_archivo = uploaded_hist.name

    if "2023" in nombre_archivo:
        df_temp["AÑO"] = 2023
    elif "2024" in nombre_archivo:
        df_temp["AÑO"] = 2024
    elif "2025" in nombre_archivo:
        df_temp["AÑO"] = 2025

    historico_path = f"{DATA_DIR}/historico_2023_2025.csv"

    if os.path.exists(historico_path):
        df_existente = pd.read_csv(historico_path, encoding="latin1")
        df_final = pd.concat([df_existente, df_temp], ignore_index=True)
    else:
        df_final = df_temp

    df_final.to_csv(historico_path, index=False)
    st.sidebar.success("Archivo agregado correctamente ✅")

# ─────────────────────────────
# CARGA 2026
# ─────────────────────────────
st.sidebar.markdown("---")
st.sidebar.header("📤 Actualizar información 2026")

uploaded_2026 = st.sidebar.file_uploader(
    "Subir CSV 2026",
    type="csv",
    key="2026"
)

if uploaded_2026:
    df_2026 = pd.read_csv(uploaded_2026, encoding="latin1")
    df_2026["AÑO"] = 2026
    df_2026.to_csv(f"{DATA_DIR}/asistencias_2026.csv", index=False)
    st.sidebar.success("CSV 2026 actualizado correctamente ✅")

# ─────────────────────────────
# LECTURA DE DATOS
# ─────────────────────────────
dfs = []

if os.path.exists(f"{DATA_DIR}/historico_2023_2025.csv"):
    dfs.append(pd.read_csv(f"{DATA_DIR}/historico_2023_2025.csv", encoding="latin1"))

if os.path.exists(f"{DATA_DIR}/asistencias_2026.csv"):
    dfs.append(pd.read_csv(f"{DATA_DIR}/asistencias_2026.csv", encoding="latin1"))

if not dfs:
    st.warning("No hay datos cargados.")
    st.stop()

df = pd.concat(dfs, ignore_index=True)

# ─────────────────────────────
# LIMPIEZA Y FECHAS
# ─────────────────────────────
df["Fecha creación de asistencia"] = (
    df["Fecha creación de asistencia"]
    .astype(str)
    .str.strip()
)

df["Fecha creación de asistencia"] = pd.to_datetime(
    df["Fecha creación de asistencia"],
    format="%d/%m/%Y",
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
estado = multiselect_filter("Estado de Asistencia", "Estado de Asistencia")
servicio = multiselect_filter("Nombre del Servicio", "Nombre del Servicio")
especialidad = multiselect_filter("Especialidad Médica", "ESPECIALIDAD MEDICA (CITAS)")

df_f = df.copy()

if anio:
    df_f = df_f[df_f["AÑO"].isin(anio)]
if mes:
    df_f = df_f[df_f["MES"].isin(mes)]
if estado:
    df_f = df_f[df_f["Estado de Asistencia"].isin(estado)]
if servicio:
    df_f = df_f[df_f["Nombre del Servicio"].isin(servicio)]
if especialidad:
    df_f = df_f[df_f["ESPECIALIDAD MEDICA (CITAS)"].isin(especialidad)]

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
# TENDENCIAS
# ─────────────────────────────
st.subheader("📈 Tendencias")

asist_mes = df_f.groupby("MES")["Número Asistencia"].count().reset_index(name="Total asistencias")
fig1 = px.line(asist_mes, x="MES", y="Total asistencias", title="Asistencias por mes")
st.plotly_chart(fig1, use_container_width=True)

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

fig_serv = px.bar(top_servicios, x="Nombre del Servicio", y="Total asistencias",
                  title="Top 10 Servicios")
col_a.plotly_chart(fig_serv, use_container_width=True)

top_especialidad = (
    df_f.groupby("ESPECIALIDAD MEDICA (CITAS)")["Número Asistencia"]
    .count()
    .reset_index(name="Total asistencias")
    .sort_values("Total asistencias", ascending=False)
    .head(10)
)

fig_esp = px.bar(top_especialidad,
                 x="ESPECIALIDAD MEDICA (CITAS)",
                 y="Total asistencias",
                 title="Top 10 Especialidades Médicas")
col_b.plotly_chart(fig_esp, use_container_width=True)
