import streamlit as st
import pandas as pd
import os
import plotly.express as px
import gdown

# ─────────────────────────────
# CONFIGURACIÓN GENERAL
# ─────────────────────────────
st.set_page_config(
    page_title="Dashboard Operaciones GEA",
    layout="wide"
)

# ─────────────────────────────
# CONTRASEÑAS Y ROLES
# ─────────────────────────────
VIEW_PASSWORD = "OperacionesGEA"
ADMIN_PASSWORD = "OperacionesGEA_admin"

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.role = None

    if not st.session_state.authenticated:
        st.title("🔐 Acceso restringido")
        password_input = st.text_input("Ingrese la contraseña", type="password")

        if st.button("Ingresar"):
            if password_input == VIEW_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.role = "viewer"
                st.rerun()

            elif password_input == ADMIN_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.role = "admin"
                st.rerun()

            else:
                st.error("Contraseña incorrecta")

        st.stop()

check_password()

# ─────────────────────────────
# DIRECTORIO DATA
# ─────────────────────────────
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ─────────────────────────────
# SOLO ACTUALIZAR 2026 (ADMIN)
# ─────────────────────────────
if st.session_state.role == "admin":

    st.sidebar.markdown("## 👑 Panel Administrador")
    st.sidebar.success("Perfil: Administrador")

    st.sidebar.header("📤 Actualizar información 2026")

    uploaded_2026 = st.sidebar.file_uploader(
        "Subir CSV 2026",
        type="csv",
        key="anio2026"
    )

    if uploaded_2026:
        df_2026_new = pd.read_csv(uploaded_2026, encoding="latin1")
        df_2026_new.to_csv(f"{DATA_DIR}/asistencias_2026.csv", index=False)
        st.sidebar.success("CSV 2026 actualizado correctamente")

else:
    st.sidebar.markdown("## 🔎 Perfil Visualización")
    st.sidebar.info("Modo solo lectura")

# ─────────────────────────────
# CARGA DE DATOS (DRIVE + LOCAL)
# ─────────────────────────────
@st.cache_data(show_spinner=True)
def cargar_datos():

    dfs = []

    files = {
        "2023": "1jVvFPdg5A5ySOQtKeuO1pLU6zG2cTa51",
        "2024": "1YnRJtc6_NyXmXjmOMLP8oINOmqr7e3_I",
        "2025": "1_etz-VsH66PpmnHVEo2H-wVgwkd4DKMl"
    }

    for year, file_id in files.items():
        try:
            url = f"https://drive.google.com/uc?id={file_id}"
            output = f"/tmp/{year}.csv"

            if not os.path.exists(output):
                gdown.download(url, output, quiet=True)

            dfs.append(pd.read_csv(output, encoding="latin1"))

        except Exception as e:
            st.warning(f"No se pudo cargar {year}: {e}")

    # 2026 local
    path_2026 = f"{DATA_DIR}/asistencias_2026.csv"
    if os.path.exists(path_2026):
        dfs.append(pd.read_csv(path_2026, encoding="latin1"))

    if not dfs:
        return None

    df = pd.concat(dfs, ignore_index=True)

    df.columns = (
        df.columns
        .str.replace('\ufeff', '', regex=False)
        .str.strip()
    )

    return df

df = cargar_datos()

# ─────────────────────────────
# DIAGNÓSTICO
# ─────────────────────────────
if df is not None:
    st.write("Total registros cargados:", len(df))

if df is None:
    st.warning("No hay datos cargados.")
    st.stop()

# ─────────────────────────────
# VALIDACIÓN COLUMNA FECHA
# ─────────────────────────────
fecha_col = None
for col in df.columns:
    if "fecha" in col.lower() and "asistencia" in col.lower():
        fecha_col = col
        break

if fecha_col is None:
    st.error("❌ No se encontró la columna de fecha")
    st.write(df.columns.tolist())
    st.stop()

# ─────────────────────────────
# PROCESAMIENTO FECHAS
# ─────────────────────────────
df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")
df = df.dropna(subset=[fecha_col])

df["AÑO"] = df[fecha_col].dt.year.astype(int)
df["MES"] = df[fecha_col].dt.month.astype(int)

st.write("Años detectados:", sorted(df["AÑO"].unique()))

# ─────────────────────────────
# LIMPIEZA MONETARIA
# ─────────────────────────────
if "Total de Costo Global" in df.columns:
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
mes = multiselect_filter("Mes", "MES")
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
if mes: df_f = df_f[df_f["MES"].isin(mes)]
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

total_asistencias = df_f["Número Asistencia"].nunique()
costo_total = df_f["Total de Costo Global"].sum()
costo_promedio = costo_total / total_asistencias if total_asistencias > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("🔢 Total asistencias", f"{total_asistencias:,}")
col2.metric("💲 Costo total", f"${costo_total:,.2f}")
col3.metric("💲 Costo promedio", f"${costo_promedio:,.2f}")
