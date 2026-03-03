import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
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
# ESTILO INSTITUCIONAL GEA
# ─────────────────────────────
st.markdown("""
<style>
.stApp {
    background-color: #F4F6F8;
}

h1, h2, h3 {
    color: #1F2E6D;
    font-weight: 700;
}

[data-testid="metric-container"] {
    background-color: white;
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────
# TEMPLATE CORPORATIVO PLOTLY
# ─────────────────────────────
GEA_TEMPLATE = dict(
    layout=dict(
        font=dict(
            family="Arial",
            size=12,
            color="#2C2C2C"
        ),
        title=dict(
            font=dict(size=16, color="#1F2E6D")
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(gridcolor="#E5E7EB"),
        yaxis=dict(gridcolor="#E5E7EB"),
        colorway=[
            "#1F2E6D",
            "#1565A6",
            "#2E7D32",
            "#8B1E1E"
        ]
    )
)

pio.templates["GEA"] = GEA_TEMPLATE
pio.templates.default = "GEA"

# ─────────────────────────────
# CONTRASEÑA
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

        df_temp = pd.read_csv(output, encoding="latin1", low_memory=False)
        dfs.append(df_temp)

    df = pd.concat(dfs, ignore_index=True)
    df.columns = df.columns.str.replace('\ufeff', '', regex=False).str.strip()

    return df


@st.cache_data(show_spinner=False)
def procesar_datos(df):

    fecha_col = [c for c in df.columns if "fecha" in c.lower() and "asistencia" in c.lower()][0]

    df[fecha_col] = pd.to_datetime(df[fecha_col], dayfirst=True, errors="coerce")
    df = df.dropna(subset=[fecha_col])

    df["AÑO"] = df[fecha_col].dt.year.astype(str)
    df["MES"] = df[fecha_col].dt.month

    meses_dict = {
        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
    }

    df["MES_NOMBRE"] = df["MES"].map(meses_dict)

    df["Número Asistencia"] = df["Número Asistencia"].astype(str)

    df["Total de Costo Global"] = (
        df["Total de Costo Global"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype(float)
    )

    return df


df = procesar_datos(cargar_datos())

# ─────────────────────────────
# FILTROS
# ─────────────────────────────
st.sidebar.header("🎛️ Filtros")

if st.sidebar.button("🔄 Reset filtros"):
    for key in st.session_state.keys():
        if key.startswith("filtro_"):
            st.session_state[key] = []
    st.rerun()

df_temp = df.copy()

def filtro_cascada(label, columna):
    opciones = sorted(df_temp[columna].dropna().unique())
    return st.sidebar.multiselect(label, opciones, key=f"filtro_{columna}")

anio = filtro_cascada("Año", "AÑO")
if anio:
    df_temp = df_temp[df_temp["AÑO"].isin(anio)]

mes_nombre = filtro_cascada("Mes", "MES_NOMBRE")
if mes_nombre:
    df_temp = df_temp[df_temp["MES_NOMBRE"].isin(mes_nombre)]

estado = filtro_cascada("Estado de Asistencia", "Estado de Asistencia")
if estado:
    df_temp = df_temp[df_temp["Estado de Asistencia"].isin(estado)]

df_f = df_temp.copy()

# ─────────────────────────────
# KPIs
# ─────────────────────────────
st.markdown("<h1>Dashboard Operaciones GEA</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#6B7280;'>Indicadores Institucionales</p>", unsafe_allow_html=True)

total_asistencias = df_f["Número Asistencia"].count()
costo_total = df_f["Total de Costo Global"].sum()
costo_promedio = costo_total / total_asistencias if total_asistencias > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("Total asistencias", f"{total_asistencias:,}")
c2.metric("Costo total", f"${costo_total:,.2f}")
c3.metric("Costo promedio", f"${costo_promedio:,.2f}")

# ─────────────────────────────
# TABLA
# ─────────────────────────────
st.subheader("📋 Estado de Asistencia por Mes")

tabla_estado = (
    df_f.groupby(["Estado de Asistencia", "MES_NOMBRE"])["Número Asistencia"]
    .count()
    .reset_index()
    .pivot(index="Estado de Asistencia", columns="MES_NOMBRE", values="Número Asistencia")
    .fillna(0)
)

tabla_estado["Total general"] = tabla_estado.sum(axis=1)

st.dataframe(tabla_estado, use_container_width=True, height=400)

# ─────────────────────────────
# ESTADOS Y MOTIVOS DE CANCELACIONES
# ─────────────────────────────
st.subheader("Estados y Motivos de Cancelaciones")

col_pie, col_cancel = st.columns([1, 1.4])

estado_totales = (
    df_f.groupby("Estado de Asistencia")["Número Asistencia"]
    .count()
    .reset_index()
)

fig_pie = px.pie(
    estado_totales,
    names="Estado de Asistencia",
    values="Número Asistencia",
    hole=0.55,
    color="Estado de Asistencia",
    color_discrete_map={
        "Concluido": "#2E7D32",
        "Cancelado posterior": "#8B1E1E",
        "Cancelado al momento": "#8B1E1E",
        "En proceso": "#1565A6"
    }
)

fig_pie.update_layout(height=400)
col_pie.plotly_chart(fig_pie, use_container_width=True)

df_cancelados = df_f[df_f["Estado de Asistencia"].isin(["Cancelado posterior", "Cancelado al momento"])]

if not df_cancelados.empty:
    df_cancelados["Motivo_Completo"] = (
        df_cancelados["Motivo Cancelacion"].fillna("") + " - " +
        df_cancelados["Submotivo Cancelacion"].fillna("")
    )

    top_cancel = (
        df_cancelados.groupby("Motivo_Completo")["Número Asistencia"]
        .count()
        .reset_index(name="Total")
        .sort_values("Total", ascending=False)
        .head(10)
    )

    fig_cancel = px.bar(
        top_cancel.sort_values("Total"),
        x="Total",
        y="Motivo_Completo",
        orientation="h",
        text_auto=True,
        color_discrete_sequence=["#8B1E1E"]
    )

    fig_cancel.update_layout(height=400)
    col_cancel.plotly_chart(fig_cancel, use_container_width=True)

else:
    col_cancel.info("No existen cancelaciones para los filtros seleccionados.")
