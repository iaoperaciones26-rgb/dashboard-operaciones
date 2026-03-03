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
# CARGA DE DATOS DESDE DRIVE
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

df[fecha_col] = pd.to_datetime(
    df[fecha_col],
    dayfirst=True,
    errors="coerce"
)

df = df.dropna(subset=[fecha_col])

df["AÑO"] = df[fecha_col].dt.year
df["MES"] = df[fecha_col].dt.month

meses_dict = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
}

df["MES_NOMBRE"] = df["MES"].map(meses_dict)

df["Número Asistencia"] = df["Número Asistencia"].astype(str).str.strip()

df["Total de Costo Global"] = (
    df["Total de Costo Global"]
    .astype(str)
    .str.replace("$", "", regex=False)
    .str.replace(",", "", regex=False)
    .astype(float)
)

# ─────────────────────────────
# FILTROS DEPENDIENTES
# ─────────────────────────────

st.sidebar.header("🎛️ Filtros")

df_temp = df.copy()

def filtro_cascada(label, columna):
    opciones = sorted(df_temp[columna].dropna().unique())
    seleccion = st.sidebar.multiselect(label, opciones)
    return seleccion

# Filtros completos
anio = filtro_cascada("Año", "AÑO")
if anio:
    df_temp = df_temp[df_temp["AÑO"].isin(anio)]

mes_nombre = filtro_cascada("Mes", "MES_NOMBRE")
if mes_nombre:
    df_temp = df_temp[df_temp["MES_NOMBRE"].isin(mes_nombre)]

grupo = filtro_cascada("Grupo de Servicio", "Grupo de Servicio")
if grupo:
    df_temp = df_temp[df_temp["Grupo de Servicio"].isin(grupo)]

servicio = filtro_cascada("Nombre del Servicio", "Nombre del Servicio")
if servicio:
    df_temp = df_temp[df_temp["Nombre del Servicio"].isin(servicio)]

subservicio = filtro_cascada("Subservicio", "Nombre del Subservicio")
if subservicio:
    df_temp = df_temp[df_temp["Nombre del Subservicio"].isin(subservicio)]

estado = filtro_cascada("Estado de Asistencia", "Estado de Asistencia")
if estado:
    df_temp = df_temp[df_temp["Estado de Asistencia"].isin(estado)]

canal = filtro_cascada("Canal Origen", "Canal Origen")
if canal:
    df_temp = df_temp[df_temp["Canal Origen"].isin(canal)]

especialidad = filtro_cascada("Especialidad Médica", "ESPECIALIDAD MEDICA (CITAS)")
if especialidad:
    df_temp = df_temp[df_temp["ESPECIALIDAD MEDICA (CITAS)"].isin(especialidad)]

proveedor = filtro_cascada("Proveedor", "Nombre del Proveedor")
if proveedor:
    df_temp = df_temp[df_temp["Nombre del Proveedor"].isin(proveedor)]

pais = filtro_cascada("País", "País")
if pais:
    df_temp = df_temp[df_temp["País"].isin(pais)]

provincia = filtro_cascada("Provincia", "Provincia")
if provincia:
    df_temp = df_temp[df_temp["Provincia"].isin(provincia)]

ciudad = filtro_cascada("Ciudad", "Ciudad")
if ciudad:
    df_temp = df_temp[df_temp["Ciudad"].isin(ciudad)]

local_foraneo = filtro_cascada("Local / Foráneo", "Local_Foráneo")
if local_foraneo:
    df_temp = df_temp[df_temp["Local_Foráneo"].isin(local_foraneo)]

tipo_cliente = filtro_cascada("Tipo de Cliente", "TIPO DE CLIENTE")
if tipo_cliente:
    df_temp = df_temp[df_temp["TIPO DE CLIENTE"].isin(tipo_cliente)]

cliente = filtro_cascada("Cliente Institucional", "Cliente Institucional")
if cliente:
    df_temp = df_temp[df_temp["Cliente Institucional"].isin(cliente)]

cuenta = filtro_cascada("Nombre de la cuenta", "Nombre de la cuenta")
if cuenta:
    df_temp = df_temp[df_temp["Nombre de la cuenta"].isin(cuenta)]

plan = filtro_cascada("Nombre del plan", "Nombre del plan")
if plan:
    df_temp = df_temp[df_temp["Nombre del plan"].isin(plan)]

evento = filtro_cascada("Tipo de Evento", "Tipo de Evento")
if evento:
    df_temp = df_temp[df_temp["Tipo de Evento"].isin(evento)]

df_f = df_temp.copy()

# 🔒 Protección anti-crash
if df_f.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# ─────────────────────────────
# KPIs
# ─────────────────────────────

st.title("📊 Dashboard Operaciones GEA")

filtros_activos = any([
    anio, mes_nombre, grupo, servicio, subservicio,
    estado, canal, especialidad, proveedor,
    pais, provincia, ciudad, local_foraneo,
    tipo_cliente, cliente, cuenta, plan, evento
])

df_kpi = df if not filtros_activos else df_f

total_asistencias = df_kpi["Número Asistencia"].count()
costo_total = df_kpi["Total de Costo Global"].sum()
costo_promedio = costo_total / total_asistencias if total_asistencias > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("🔢 Total asistencias", f"{total_asistencias:,}")
c2.metric("💲 Costo total", f"${costo_total:,.2f}")
c3.metric("💲 Costo promedio", f"${costo_promedio:,.2f}")

# ─────────────────────────────
# RESUMEN EJECUTIVO
# ─────────────────────────────

st.subheader("📊 Resumen Ejecutivo")

col1, col2 = st.columns(2)

orden_meses = ["Ene","Feb","Mar","Abr","May","Jun",
               "Jul","Ago","Sep","Oct","Nov","Dic"]
orden_anios = sorted(df_f["AÑO"].unique())

total_anual = df_f.groupby("AÑO")["Número Asistencia"].count().reset_index(name="Total Asistencias")

fig_total_asist = px.bar(total_anual, x="AÑO", y="Total Asistencias", text_auto=True)
col1.plotly_chart(fig_total_asist, use_container_width=True)

asist_mes = df_f.groupby(["AÑO","MES_NOMBRE","MES"])["Número Asistencia"].count().reset_index(name="Total Asistencias")

fig_asist_mes = px.bar(
    asist_mes,
    x="MES_NOMBRE",
    y="Total Asistencias",
    color="AÑO",
    barmode="group",
    category_orders={"MES_NOMBRE": orden_meses, "AÑO": orden_anios}
)

# ─────────────────────────────
# TOPS
# ─────────────────────────────

st.subheader("🏆 Top servicios y especialidades")

col_a, col_b = st.columns(2)

top_servicios = df_f.groupby("Nombre del Servicio")["Número Asistencia"].count().reset_index(name="Total").sort_values("Total", ascending=False).head(10)
col_a.plotly_chart(px.bar(top_servicios, x="Nombre del Servicio", y="Total"), use_container_width=True)

top_especialidad = df_f.groupby("ESPECIALIDAD MEDICA (CITAS)")["Número Asistencia"].count().reset_index(name="Total").sort_values("Total", ascending=False).head(10)
col_b.plotly_chart(px.bar(top_especialidad, x="ESPECIALIDAD MEDICA (CITAS)", y="Total"), use_container_width=True)

# ─────────────────────────────
# TABLA
# ─────────────────────────────

st.subheader("📋 Estado de Asistencia por Mes")

tabla_estado = df_f.groupby(["Estado de Asistencia","MES"])["Número Asistencia"].count().reset_index().pivot(index="Estado de Asistencia", columns="MES", values="Número Asistencia").fillna(0).astype(int)

tabla_estado["Total general"] = tabla_estado.sum(axis=1)

st.dataframe(tabla_estado, use_container_width=True)

# ─────────────────────────────
# PIE
# ─────────────────────────────

st.subheader("🥧 % Estado de Asistencia")

estado_totales = df_f.groupby("Estado de Asistencia")["Número Asistencia"].count().reset_index()

st.plotly_chart(
    px.pie(estado_totales, names="Estado de Asistencia", values="Número Asistencia", hole=0.4),
    use_container_width=True
)
