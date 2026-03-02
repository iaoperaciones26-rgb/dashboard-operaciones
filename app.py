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
# FUNCIÓN PARA LEER CSV (auto-detecta encoding)
# ─────────────────────────────
def read_csv_safe(file):
    try:
        return pd.read_csv(file, encoding="utf-8")
    except:
        return pd.read_csv(file, encoding="latin1")

# ─────────────────────────────
# FUNCIÓN PARA NORMALIZAR COLUMNAS (quita tildes)
# ─────────────────────────────
def normalize_columns(df):
    df.columns = [
        unicodedata.normalize('NFKD', col)
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
# OPCIONES SOLO ADMIN
# ─────────────────────────────
if st.session_state.role == "admin":

    st.sidebar.markdown("## 👑 Panel Administrador")
    st.sidebar.success("Perfil: Administrador")

    # HISTÓRICO
    st.sidebar.header("📦 Cargar histórico 2023–2025")

    uploaded_hist = st.sidebar.file_uploader(
        "Subir CSV histórico",
        type="csv",
        key="historico"
    )

    if uploaded_hist:
        df_temp = read_csv_safe(uploaded_hist)
        df_temp = normalize_columns(df_temp)

        historico_path = f"{DATA_DIR}/historico_2023_2025.csv"

        if os.path.exists(historico_path):
            df_existente = read_csv_safe(historico_path)
            df_final = pd.concat([df_existente, df_temp], ignore_index=True)
        else:
            df_final = df_temp

        df_final.to_csv(historico_path, index=False)
        st.sidebar.success("Archivo agregado correctamente ✅")

    # 2026
    st.sidebar.markdown("---")
    st.sidebar.header("📤 Actualizar información 2026")

    uploaded_2026 = st.sidebar.file_uploader(
        "Subir CSV 2026",
        type="csv",
        key="anio2026"
    )

    if uploaded_2026:
        df_2026_new = read_csv_safe(uploaded_2026)
        df_2026_new = normalize_columns(df_2026_new)
        df_2026_new.to_csv(f"{DATA_DIR}/asistencias_2026.csv", index=False)
        st.sidebar.success("CSV 2026 actualizado correctamente ✅")

else:
    st.sidebar.markdown("## 🔎 Perfil Visualización")
    st.sidebar.info("Modo solo lectura")

# ─────────────────────────────
# LECTURA ARCHIVOS
# ─────────────────────────────
dfs = []

if os.path.exists(f"{DATA_DIR}/historico_2023_2025.csv"):
    df_hist = read_csv_safe(f"{DATA_DIR}/historico_2023_2025.csv")
    df_hist = normalize_columns(df_hist)
    dfs.append(df_hist)

if os.path.exists(f"{DATA_DIR}/asistencias_2026.csv"):
    df_2026 = read_csv_safe(f"{DATA_DIR}/asistencias_2026.csv")
    df_2026 = normalize_columns(df_2026)
    dfs.append(df_2026)

if not dfs:
    st.warning("No hay datos cargados.")
    st.stop()

df = pd.concat(dfs, ignore_index=True)

# ─────────────────────────────
# VALIDACIÓN COLUMNA FECHA (sin tilde)
# ─────────────────────────────
fecha_col = "Fecha creacion de asistencia"

if fecha_col not in df.columns:
    st.error(f"❌ No se encontró la columna '{fecha_col}'")
    st.write("Columnas detectadas:")
    st.write(df.columns.tolist())
    st.stop()

# ─────────────────────────────
# PROCESAMIENTO FECHAS
# ─────────────────────────────
df[fecha_col] = pd.to_datetime(
    df[fecha_col],
    dayfirst=True,
    errors="coerce"
)

df = df.dropna(subset=[fecha_col])

df["AÑO"] = df[fecha_col].dt.year
df["MES"] = df[fecha_col].dt.month

# ─────────────────────────────
# LIMPIEZA MONETARIA
# ─────────────────────────────
for col in ["Total de Costo Global", "Total de importe pagado"]:
    if col in df.columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
            .astype(float)
        )

# ─────────────────────────────
# DASHBOARD
# ─────────────────────────────
st.title("📊 Dashboard Operaciones GEA")

total_asistencias = df["Numero Asistencia"].count()
costo_total = df["Total de Costo Global"].sum()
costo_promedio = costo_total / total_asistencias if total_asistencias > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("🔢 Total asistencias", f"{total_asistencias:,}")
col2.metric("💲 Costo total", f"${costo_total:,.2f}")
col3.metric("💲 Costo promedio", f"${costo_promedio:,.2f}")
