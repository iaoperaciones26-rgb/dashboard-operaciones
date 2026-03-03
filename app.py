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
# CARGA OPTIMIZADA
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
        try:
            url = f"https://drive.google.com/uc?id={file_id}"
            output = f"/tmp/{year}.csv"

            if not os.path.exists(output):
                gdown.download(url, output, quiet=True)

            df_temp = pd.read_csv(
                output,
                encoding="latin1",
                low_memory=False
            )

            dfs.append(df_temp)

        except Exception as e:
            st.error(f"Error cargando archivo {year}: {e}")

    if not dfs:
        st.error("No se pudieron cargar los archivos.")
        st.stop()

    df = pd.concat(dfs, ignore_index=True)
    df.columns = df.columns.str.replace('\ufeff', '', regex=False).str.strip()

    return df


@st.cache_data(show_spinner=False)
def procesar_datos(df):

    columnas_necesarias = [
        "Número Asistencia",
        "Total de Costo Global"
    ]

    for col in columnas_necesarias:
        if col not in df.columns:
            raise ValueError(f"No se encontró la columna: {col}")

    fecha_cols = [c for c in df.columns if "fecha" in c.lower() and "asistencia" in c.lower()]

    if not fecha_cols:
        raise ValueError("No se encontró columna fecha asistencia")

    fecha_col = fecha_cols[0]

    df[fecha_col] = pd.to_datetime(
        df[fecha_col],
        dayfirst=True,
        errors="coerce"
    )

    df = df.dropna(subset=[fecha_col])

    # ✅ SOLUCIÓN LIMPIA: AÑO COMO STRING
    df["AÑO"] = df[fecha_col].dt.year.astype(str)

    df["MES"] = df[fecha_col].dt.month.astype("int8")

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
    )

    df["Total de Costo Global"] = pd.to_numeric(
        df["Total de Costo Global"],
        errors="coerce"
    ).fillna(0)

    columnas_categoricas = [
        "Grupo de Servicio",
        "Nombre del Servicio",
        "Nombre del Subservicio",
        "Estado de Asistencia",
        "Canal Origen",
        "Nombre del Proveedor",
        "País",
        "Provincia",
        "Ciudad",
        "Local_Foráneo",
        "TIPO DE CLIENTE",
        "Cliente Institucional",
        "Nombre de la cuenta",
        "Nombre del plan",
        "Tipo de Evento",
        "ESPECIALIDAD MEDICA (CITAS)",
        "MES_NOMBRE",
        "AÑO"
    ]

    for col in columnas_categoricas:
        if col in df.columns:
            df[col] = df[col].astype("category")

    return df


# ─────────────────────────────
# EJECUCIÓN
# ─────────────────────────────

try:
    df = cargar_datos()
    df = procesar_datos(df)
except Exception as e:
    st.error(f"Error procesando datos: {e}")
    st.stop()

# ─────────────────────────────
# FILTROS
# ─────────────────────────────

st.sidebar.header("🎛️ Filtros")

# Botón Reset Filtros
if st.sidebar.button("🔄 Reset filtros"):
    for key in st.session_state.keys():
        if key.startswith("filtro_"):
            st.session_state[key] = []
    st.rerun()

df_temp = df.copy()

def filtro_cascada(label, columna):
    if columna not in df_temp.columns:
        return []

    opciones = sorted(df_temp[columna].dropna().unique())
    key_name = f"filtro_{columna}"

    # Inicializar si no existe
    if key_name not in st.session_state:
        st.session_state[key_name] = []

    seleccion = st.sidebar.multiselect(
        label,
        opciones,
        key=key_name,
        default=st.session_state[key_name]
    )

    return seleccion
    
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

if df_f.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# ─────────────────────────────
# KPIs
# ─────────────────────────────

st.title("📊 Dashboard Operaciones GEA")

total_asistencias = df_f["Número Asistencia"].count()
costo_total = df_f["Total de Costo Global"].sum()
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

total_anual = df_f.groupby("AÑO")["Número Asistencia"].count().reset_index(name="Total Asistencias")

fig_total_asist = px.bar(
    total_anual,
    x="AÑO",
    y="Total Asistencias",
    text_auto=True
)

fig_total_asist.update_layout(xaxis_type="category")

col1.plotly_chart(fig_total_asist, use_container_width=True)

asist_mes = df_f.groupby(["AÑO","MES_NOMBRE"])["Número Asistencia"].count().reset_index(name="Total Asistencias")

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

col2.plotly_chart(fig_asist_mes, use_container_width=True)

# ─────────────────────────────
# TOPS
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

col_a.plotly_chart(
    px.bar(top_servicios, x="Nombre del Servicio", y="Total"),
    use_container_width=True
)

top_especialidad = (
    df_f.groupby("ESPECIALIDAD MEDICA (CITAS)")["Número Asistencia"]
    .count()
    .reset_index(name="Total")
    .sort_values("Total", ascending=False)
    .head(10)
)

col_b.plotly_chart(
    px.bar(top_especialidad, x="ESPECIALIDAD MEDICA (CITAS)", y="Total"),
    use_container_width=True
)

# ─────────────────────────────
# TABLA
# ─────────────────────────────

st.subheader("📋 Estado de Asistencia por Mes")

tabla_estado = (
    df_f
    .groupby(["Estado de Asistencia", "MES_NOMBRE"])["Número Asistencia"]
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

st.dataframe(tabla_estado, use_container_width=True)

# ─────────────────────────────
# PIE + CANCELACIONES
# ─────────────────────────────

st.subheader("📊 Estado y Análisis de Cancelaciones")

col_pie, col_cancel = st.columns([1, 1.4])  # Más espacio al gráfico horizontal

# ───── PIE MÁS COMPACTO
estado_totales = (
    df_f.groupby("Estado de Asistencia")["Número Asistencia"]
    .count()
    .reset_index()
)

fig_pie = px.pie(
    estado_totales,
    names="Estado de Asistencia",
    values="Número Asistencia",
    hole=0.5
)

fig_pie.update_layout(
    height=400,
    showlegend=True
)

col_pie.plotly_chart(fig_pie, use_container_width=True)

# ───── CANCELACIONES

df_cancelados = df_f[
    df_f["Estado de Asistencia"].isin(
        ["Cancelado posterior", "Cancelado al momento"]
    )
]

if not df_cancelados.empty:

    # Crear columna combinada
    df_cancelados["Motivo_Completo"] = (
        df_cancelados["Motivo Cancelacion"].fillna("").astype(str)
        + " - "
        + df_cancelados["Submotivo Cancelacion"].fillna("").astype(str)
    )

    # Limpiar casos donde submotivo sea vacío
    df_cancelados["Motivo_Completo"] = df_cancelados["Motivo_Completo"].str.replace(" - $", "", regex=True)

    top_cancelaciones = (
        df_cancelados
        .groupby("Motivo_Completo")["Número Asistencia"]
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
        text_auto=True
    )

    fig_cancel.update_layout(
        height=400,
        yaxis_title="",
        xaxis_title="Cantidad"
    )

    col_cancel.plotly_chart(fig_cancel, use_container_width=True)

else:
    col_cancel.info("No existen cancelaciones para los filtros seleccionados.")
