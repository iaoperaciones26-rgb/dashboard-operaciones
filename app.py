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
        font=dict(family="Arial", size=12, color="#2C2C2C"),
        title=dict(font=dict(size=16, color="#1F2E6D")),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(gridcolor="#E5E7EB"),
        yaxis=dict(gridcolor="#E5E7EB"),
        colorway=["#1F2E6D", "#1565A6", "#2E7D32", "#8B1E1E"]
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
# FILTROS (MISMO ORDEN ORIGINAL)
# ─────────────────────────────
st.sidebar.header("🎛️ Filtros")

# Reset global
if st.sidebar.button("🔄 Reset filtros"):
    st.session_state.clear()
    st.session_state.authenticated = True
    st.rerun()

# Formulario para evitar múltiples ejecuciones
with st.sidebar.form("filtros_form"):

    df_temp = df.copy()

    def filtro(label, columna):
        opciones = sorted(df[columna].dropna().unique())
        return st.multiselect(label, opciones)

    anio = filtro("Año", "AÑO")
    mes_nombre = filtro("Mes", "MES_NOMBRE")
    grupo = filtro("Grupo de Servicio", "Grupo de Servicio")
    servicio = filtro("Nombre del Servicio", "Nombre del Servicio")
    subservicio = filtro("Subservicio", "Nombre del Subservicio")
    estado = filtro("Estado de Asistencia", "Estado de Asistencia")
    canal = filtro("Canal Origen", "Canal Origen")
    especialidad = filtro("Especialidad Médica", "ESPECIALIDAD MEDICA (CITAS)")
    proveedor = filtro("Proveedor", "Nombre del Proveedor")
    pais = filtro("País", "País")
    provincia = filtro("Provincia", "Provincia")
    ciudad = filtro("Ciudad", "Ciudad")
    local_foraneo = filtro("Local / Foráneo", "Local_Foráneo")
    tipo_cliente = filtro("Tipo de Cliente", "TIPO DE CLIENTE")
    cliente = filtro("Cliente Institucional", "Cliente Institucional")
    cuenta = filtro("Nombre de la cuenta", "Nombre de la cuenta")
    plan = filtro("Nombre del plan", "Nombre del plan")
    evento = filtro("Tipo de Evento", "Tipo de Evento")

    aplicar = st.form_submit_button("Aplicar filtros")

# Solo aplicar filtros cuando se presiona el botón
if aplicar:

    if anio:
        df_temp = df_temp[df_temp["AÑO"].isin(anio)]

    if mes_nombre:
        df_temp = df_temp[df_temp["MES_NOMBRE"].isin(mes_nombre)]

    if grupo:
        df_temp = df_temp[df_temp["Grupo de Servicio"].isin(grupo)]

    if servicio:
        df_temp = df_temp[df_temp["Nombre del Servicio"].isin(servicio)]

    if subservicio:
        df_temp = df_temp[df_temp["Nombre del Subservicio"].isin(subservicio)]

    if estado:
        df_temp = df_temp[df_temp["Estado de Asistencia"].isin(estado)]

    if canal:
        df_temp = df_temp[df_temp["Canal Origen"].isin(canal)]

    if especialidad:
        df_temp = df_temp[df_temp["ESPECIALIDAD MEDICA (CITAS)"].isin(especialidad)]

    if proveedor:
        df_temp = df_temp[df_temp["Nombre del Proveedor"].isin(proveedor)]

    if pais:
        df_temp = df_temp[df_temp["País"].isin(pais)]

    if provincia:
        df_temp = df_temp[df_temp["Provincia"].isin(provincia)]

    if ciudad:
        df_temp = df_temp[df_temp["Ciudad"].isin(ciudad)]

    if local_foraneo:
        df_temp = df_temp[df_temp["Local_Foráneo"].isin(local_foraneo)]

    if tipo_cliente:
        df_temp = df_temp[df_temp["TIPO DE CLIENTE"].isin(tipo_cliente)]

    if cliente:
        df_temp = df_temp[df_temp["Cliente Institucional"].isin(cliente)]

    if cuenta:
        df_temp = df_temp[df_temp["Nombre de la cuenta"].isin(cuenta)]

    if plan:
        df_temp = df_temp[df_temp["Nombre del plan"].isin(plan)]

    if evento:
        df_temp = df_temp[df_temp["Tipo de Evento"].isin(evento)]

df_f = df_temp.copy()

if df_f.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()
# ─────────────────────────────
# KPIs
# ─────────────────────────────
st.markdown("<h1>Dashboard Operaciones GEA</h1>", unsafe_allow_html=True)

total_asistencias = df_f["Número Asistencia"].count()
costo_total = df_f["Total de Costo Global"].sum()
costo_promedio = costo_total / total_asistencias if total_asistencias > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("Total asistencias", f"{total_asistencias:,}")
c2.metric("Costo total", f"${costo_total:,.2f}")
c3.metric("Costo promedio", f"${costo_promedio:,.2f}")
# ─────────────────────────────
# RESUMEN EJECUTIVO
# ─────────────────────────────

st.subheader("📊 Resumen Ejecutivo")

col1, col2 = st.columns(2)

orden_meses = ["Ene","Feb","Mar","Abr","May","Jun",
               "Jul","Ago","Sep","Oct","Nov","Dic"]

# Total asistencias por año
total_anual = (
    df_f.groupby("AÑO")["Número Asistencia"]
    .count()
    .reset_index(name="Total Asistencias")
)

fig_total_asist = px.bar(
    total_anual,
    x="AÑO",
    y="Total Asistencias",
    text_auto=True
)

fig_total_asist.update_layout(
    xaxis_type="category",
    height=400
)

col1.plotly_chart(fig_total_asist, use_container_width=True)

# Asistencias por mes
asist_mes = (
    df_f.groupby(["AÑO","MES_NOMBRE"])["Número Asistencia"]
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
        "AÑO": sorted(df_f["AÑO"].unique())
    }
)

fig_asist_mes.update_layout(height=400)

col2.plotly_chart(fig_asist_mes, use_container_width=True)

# ─────────────────────────────
# TOP SERVICIOS Y ESPECIALIDADES
# ─────────────────────────────

st.subheader("🏆 Top servicios y especialidades")

col_a, col_b = st.columns(2)

top_servicios = (
    df_f.groupby("Nombre del Servicio")["Número Asistencia"]
    .count()
    .reset_index(name="Total")
    .sort_values("Total", ascending=False)
    .head(10)
)

fig_top_serv = px.bar(
    top_servicios.sort_values("Total"),
    x="Total",
    y="Nombre del Servicio",
    orientation="h",
    text_auto=True
)

fig_top_serv.update_layout(height=400)

col_a.plotly_chart(fig_top_serv, use_container_width=True)

top_especialidad = (
    df_f.groupby("ESPECIALIDAD MEDICA (CITAS)")["Número Asistencia"]
    .count()
    .reset_index(name="Total")
    .sort_values("Total", ascending=False)
    .head(10)
)

fig_top_esp = px.bar(
    top_especialidad.sort_values("Total"),
    x="Total",
    y="ESPECIALIDAD MEDICA (CITAS)",
    orientation="h",
    text_auto=True
)

fig_top_esp.update_layout(height=400)

col_b.plotly_chart(fig_top_esp, use_container_width=True)

# ─────────────────────────────
# TABLA
# ─────────────────────────────

st.subheader("📋 Estado de Asistencia por Mes")

tabla_estado = (
    df_f.groupby(["Estado de Asistencia", "MES_NOMBRE"])["Número Asistencia"]
    .count()
    .reset_index()
)

tabla_estado = tabla_estado.pivot(
    index="Estado de Asistencia",
    columns="MES_NOMBRE",
    values="Número Asistencia"
)

tabla_estado = tabla_estado.reindex(columns=orden_meses)
tabla_estado = tabla_estado.fillna(0).astype(int)

tabla_estado["Total general"] = tabla_estado.sum(axis=1)
tabla_estado = tabla_estado.sort_values("Total general", ascending=False)

# Altura dinámica según número de filas
filas = len(tabla_estado)
altura_tabla = 70 + (filas * 35)

st.dataframe(
    tabla_estado.style.format("{:,.0f}"),
    use_container_width=True,
    height=altura_tabla
)

# ─────────────────────────────
# ESTADOS Y MOTIVOS DE CANCELACIONES
# ─────────────────────────────

st.subheader("Estados y Motivos de Cancelaciones")

col_pie, col_cancel = st.columns([1, 1.4])

# PIE INSTITUCIONAL
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

# ───── CANCELACIONES

df_cancelados = df_f[
    df_f["Estado de Asistencia"].isin(
        ["Cancelado posterior", "Cancelado al momento"]
    )
].copy()

if not df_cancelados.empty and \
   "Motivo Cancelacion" in df_cancelados.columns and \
   "Submotivo Cancelacion" in df_cancelados.columns:

    df_cancelados["Motivo_Completo"] = (
        df_cancelados["Motivo Cancelacion"].fillna("").astype(str)
        + " - "
        + df_cancelados["Submotivo Cancelacion"].fillna("").astype(str)
    )

    df_cancelados["Motivo_Completo"] = (
        df_cancelados["Motivo_Completo"]
        .str.replace(" - $", "", regex=True)
    )

    top_cancelaciones = (
        df_cancelados.groupby("Motivo_Completo")["Número Asistencia"]
        .count()
        .reset_index(name="Total")
        .sort_values("Total", ascending=False)
        .head(10)
    )

    fig_cancel = px.bar(
        top_cancelaciones.sort_values("Total"),
        x="Total",
        y="Motivo_Completo",
        orientation="h",
        text_auto=True,
        color_discrete_sequence=["#8B1E1E"]
    )

    fig_cancel.update_layout(
        height=400,
        yaxis_title="",
        xaxis_title="Cantidad"
    )

    col_cancel.plotly_chart(fig_cancel, use_container_width=True)

else:
    col_cancel.info("No existen cancelaciones para los filtros seleccionados.")
