import streamlit as st
import pandas as pd
import os
import plotly.express as px

# ─────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────
st.set_page_config(page_title="Dashboard Operaciones GEA", layout="wide")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ─────────────────────────────
# CONTRASEÑAS
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
# PANEL ADMIN (SOLO 2026)
# ─────────────────────────────
if st.session_state.role == "admin":
    st.sidebar.markdown("## 👑 Panel Administrador")
    st.sidebar.header("Actualizar archivo 2026")

    uploaded_2026 = st.sidebar.file_uploader(
        "Subir asistencias_2026.csv",
        type="csv"
    )

    if uploaded_2026:
        try:
            df_new = pd.read_csv(uploaded_2026, encoding="latin1")
            df_new.to_csv(f"{DATA_DIR}/asistencias_2026.csv", index=False)
            st.sidebar.success("2026 actualizado correctamente ✅")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

else:
    st.sidebar.info("Modo solo lectura")

# ─────────────────────────────
# CARGA DE DATOS (Drive + Local)
# ─────────────────────────────
import gdown

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
    path_2026 = "data/asistencias_2026.csv"
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

st.write("Total registros cargados:", len(df))
st.write("Años detectados:", df["AÑO"].unique() if "AÑO" in df.columns else "AÑO no creado")

if df is None:
    st.warning("No hay datos disponibles.")
    st.stop()

# ─────────────────────────────
# DETECTAR COLUMNA FECHA
# ─────────────────────────────
fecha_col = None
for col in df.columns:
    if "fecha" in col.lower() and "asistencia" in col.lower():
        fecha_col = col
        break

if fecha_col is None:
    st.error("No se encontró columna de fecha.")
    st.write(df.columns.tolist())
    st.stop()

# Procesar fecha
df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")
df = df.dropna(subset=[fecha_col])

df["AÑO"] = df[fecha_col].dt.year
df["MES"] = df[fecha_col].dt.month

# Limpieza monetaria
if "Total de Costo Global" in df.columns:
    df["Total de Costo Global"] = (
        df["Total de Costo Global"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype(float)
    )

# ─────────────────────────────
# FILTROS
# ─────────────────────────────
st.sidebar.header("Filtros")

anio = st.sidebar.multiselect("Año", sorted(df["AÑO"].dropna().unique()))
mes = st.sidebar.multiselect("Mes", sorted(df["MES"].dropna().unique()))

df_f = df.copy()
if anio:
    df_f = df_f[df_f["AÑO"].isin(anio)]
if mes:
    df_f = df_f[df_f["MES"].isin(mes)]

# ─────────────────────────────
# KPIs
# ─────────────────────────────
st.title("📊 Dashboard Operaciones GEA")

total = df_f["Número Asistencia"].count()
costo_total = df_f["Total de Costo Global"].sum() if "Total de Costo Global" in df_f.columns else 0
promedio = costo_total / total if total > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("Total asistencias", f"{total:,}")
c2.metric("Costo total", f"${costo_total:,.2f}")
c3.metric("Costo promedio", f"${promedio:,.2f}")

# Tendencia mensual
st.subheader("Tendencia mensual")
trend = df_f.groupby("MES")["Número Asistencia"].count().reset_index()
fig = px.line(trend, x="MES", y="Número Asistencia")
st.plotly_chart(fig, use_container_width=True)
