import streamlit as st
import pandas as pd
import os
import plotly.express as px
import unicodedata

# ─────────────────────────────
# CONFIGURACIÓN GENERAL
# ─────────────────────────────
st.set_page_config(
    page_title="Dashboard Operaciones GEA",
    layout="wide"
)

# ─────────────────────────────
# FUNCIÓN PARA LEER CSV ROBUSTO
# ─────────────────────────────
def read_csv_safe(file):
    try:
        df = pd.read_csv(file, sep=None, engine="python", encoding="utf-8")
    except:
        df = pd.read_csv(file, sep=None, engine="python", encoding="latin1")
    return df

# ─────────────────────────────
# NORMALIZAR COLUMNAS
# ─────────────────────────────
def normalize_columns(df):
    df.columns = [
        unicodedata.normalize('NFKD', str(col))
        .encode('ASCII', 'ignore')
        .decode('utf-8')
        .strip()
        for col in df.columns
    ]
    return df

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
# PANEL ADMIN
# ─────────────────────────────
if st.session_state.role == "admin":

    st.sidebar.markdown("## 👑 Panel Administrador")
    st.sidebar.success("Perfil: Administrador")

    uploaded_2026 = st.sidebar.file_uploader(
        "Subir CSV 2026",
        type="csv",
        key="anio2026"
    )

    if uploaded_2026:
        df_2026 = read_csv_safe(uploaded_2026)

        # Validación básica de encabezado
        if len(df_2026.columns) < 5:
            st.sidebar.error("❌ El archivo no tiene encabezados válidos.")
            st.stop()

        df_2026 = normalize_columns(df_2026)
        df_2026.to_csv(f"{DATA_DIR}/asistencias_2026.csv", index=False)
        st.sidebar.success("CSV 2026 actualizado correctamente ✅")

else:
    st.sidebar.markdown("## 🔎 Perfil Visualización")
    st.sidebar.info("Modo solo lectura")

# ─────────────────────────────
# LECTURA ARCHIVO 2026
# ─────────────────────────────
if not os.path.exists(f"{DATA_DIR}/asistencias_2026.csv"):
    st.warning("No hay datos cargados.")
    st.stop()

df = read_csv_safe(f"{DATA_DIR}/asistencias_2026.csv")
df = normalize_columns(df)

# ─────────────────────────────
# VALIDAR COLUMNA FECHA FLEXIBLE
# ─────────────────────────────
fecha_col = None

for col in df.columns:
    if "fecha" in col.lower() and "asistencia" in col.lower():
        fecha_col = col
        break

if not fecha_col:
    st.error("❌ No se encontró una columna de fecha válida.")
    st.write("Columnas detectadas:")
    st.write(df.columns.tolist())
    st.stop()

# ─────────────────────────────
# PROCESAMIENTO FECHAS
# ─────────────────────────────
df[fecha_col] = pd.to_datetime(df[fecha_col], dayfirst=True, errors="coerce")
df = df.dropna(subset=[fecha_col])

df["AÑO"] = df[fecha_col].dt.year
df["MES"] = df[fecha_col].dt.month

# ─────────────────────────────
# DASHBOARD
# ─────────────────────────────
st.title("📊 Dashboard Operaciones GEA")

total_asistencias = len(df)
st.metric("🔢 Total asistencias", f"{total_asistencias:,}")

asist_mes = df.groupby("MES").size().reset_index(name="Total")
fig = px.line(asist_mes, x="MES", y="Total", title="Asistencias por mes")
st.plotly_chart(fig, use_container_width=True)
