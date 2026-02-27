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

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

PASSWORD = "OperacionesGEA"

# ─────────────────────────────
# FUNCIÓN DE AUTENTICACIÓN
# ─────────────────────────────
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

# ─────────────────────────────
# CARGA DE ARCHIVOS
# ─────────────────────────────
st.sidebar.header("📤 Actualizar información 2026")
uploaded_file = st.sidebar.file_uploader("Subir CSV 2026", type="csv")

st.sidebar.markdown("---")
st.sidebar.header("📦 Cargar histórico 2023–2025")
uploaded_hist = st.sidebar.file_uploader(
    "Subir un CSV histórico (uno a la vez)",
    type="csv",
    key="historico"
)

# Guardar histórico incremental
if uploaded_hist:
    df_temp = pd.read_csv(uploaded_hist, encoding="latin1")
    historico_path = f"{DATA_DIR}/historico_2023_2025.csv"

    if os.path.exists(historico_path):
        df_existente = pd.read_csv(historico_path, encoding="latin1")
        df_final = pd.concat([df_existente, df_temp], ignore_index=True)
    else:
        df_final = df_temp

    df_final.to_csv(historico_path, index=False)
    st.sidebar.success("Archivo agregado al histórico correctamente ✅")

# Guardar archivo 2026 (reemplazo)
if uploaded_file:
    df_new = pd.read_csv(uploaded_file, encoding="latin1")
    df_new.to_csv(f"{DATA_DIR}/asistencias_2026.csv", index=False)
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
# LIMPIEZA Y TRANSFORMACIÓN
# ─────────────────────────────
df["Fecha creación de asistencia"] = pd.to_datetime(
    df["Fecha creación de asistencia"],
    errors="coerce"
)

df["AÑO"] = df["Fecha creación de asistencia"].dt.year
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

filtros = {
    "AÑO": multiselect_filter("Año", "AÑO"),
    "MES": multiselect_filter("Mes", "MES"),
    "Estado de Asistencia": multiselect_filter("Estado de Asistencia", "Estado de Asistencia"),
    "Canal Origen": multiselect_filter("Canal de Origen", "Canal Origen"),
    "Grupo de Servicio": multiselect_filter("Grupo de Servicio", "Grupo de Servicio"),
    "Nombre del Servicio": multiselect_filter("Nombre del Servicio", "Nombre del Servicio"),
    "Nombre del Subservicio": multiselect_filter("Subservicio", "Nombre del Subservicio"),
    "ESPECIALIDAD MEDICA (CITAS)": multiselect_filter("Especialidad Médica", "ESPECIALIDAD MEDICA (CITAS)"),
    "Nombre del Proveedor": multiselect_filter("Proveedor", "Nombre del Proveedor"),
    "País": multiselect_filter("País", "País"),
    "Provincia": multiselect_filter("Provincia", "Provincia"),
    "Ciudad": multiselect_filter("Ciudad", "Ciudad"),
    "Local_Foráneo": multiselect_filter("Local / Foráneo", "Local_Foráneo"),
    "TIPO DE CLIENTE": multiselect_filter("Tipo de Cliente", "TIPO DE CLIENTE"),
    "Cliente Institucional": multiselect_filter("Cliente Institucional", "Cliente Institucional"),
    "Nombre de la cuenta": multiselect_filter("Nombre de la cuenta", "Nombre de la cuenta"),
    "Nombre del plan": multiselect_filter("Nombre del plan", "Nombre del plan"),
    "Tipo de Evento": multiselect_filter("Tipo de Evento", "Tipo de Evento"),
}

df_f = df.copy()

for columna, valores in filtros.items():
    if valores:
        df_f = df_f[df_f[columna].isin(valores)]

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
st.subheader("🏆 Top 10 Servicios")

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
    title="Top 10 Servicios"
)

st.plotly_chart(fig_serv, use_container_width=True)

# ─────────────────────────────
# ESTADO DE ASISTENCIA
# ─────────────────────────────
st.subheader("📋 Estado de Asistencia por Mes")

tabla_estado = (
    df_f.groupby(["Estado de Asistencia", "MES"])["Número Asistencia"]
    .count()
    .reset_index()
    .pivot(index="Estado de Asistencia", columns="MES", values="Número Asistencia")
    .fillna(0)
    .astype(int)
)

tabla_estado["Total general"] = tabla_estado.sum(axis=1)
tabla_estado = tabla_estado.sort_values(by="Total general", ascending=False)

total_fila = tabla_estado.sum().to_frame().T
total_fila.index = ["Total general"]

tabla_estado = pd.concat([tabla_estado, total_fila])

st.dataframe(tabla_estado, use_container_width=True)

# ─────────────────────────────
# PIE ESTADO
# ─────────────────────────────
st.subheader("🥧 % Estado de Asistencia")

estado_totales = (
    df_f.groupby("Estado de Asistencia")["Número Asistencia"]
    .count()
    .reset_index()
    .sort_values(by="Número Asistencia", ascending=False)
)

fig_pie = px.pie(
    estado_totales,
    names="Estado de Asistencia",
    values="Número Asistencia",
    hole=0.4
)

st.plotly_chart(fig_pie, use_container_width=True)
