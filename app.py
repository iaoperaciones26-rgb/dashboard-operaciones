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
        password_input = st.text_input(
            "Ingrese la contraseña",
            type="password"
        )
        if st.button("Ingresar"):
            if password_input == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        st.stop()

check_password()

# ─────────────────────────────
# CARGA CSV 2026 (REEMPLAZO)
# ─────────────────────────────
st.sidebar.header("📤 Actualizar información 2026")

uploaded_file = st.sidebar.file_uploader(
    "Subir CSV 2026",
    type="csv"
)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
# ─────────────────────────────
# CARGA HISTÓRICO INCREMENTAL 2023–2025
# ─────────────────────────────
st.sidebar.markdown("---")
st.sidebar.header("📦 Cargar histórico 2023–2025 (uno por uno)")

uploaded_hist = st.sidebar.file_uploader(
    "Subir un CSV histórico a la vez",
    type="csv",
    key="historico"
)

if uploaded_hist:

    df_temp = pd.read_csv(uploaded_hist, encoding="latin1")

    historico_path = f"{DATA_DIR}/historico_2023_2025.csv"

    # Si ya existe histórico, lo abrimos y agregamos
    if os.path.exists(historico_path):
        df_existente = pd.read_csv(historico_path, encoding="latin1")
        df_final = pd.concat([df_existente, df_temp], ignore_index=True)
    else:
        df_final = df_temp

    df_final.to_csv(historico_path, index=False)

    st.sidebar.success("Archivo agregado al histórico correctamente ✅")

if uploaded_file:
    df_new = pd.read_csv(uploaded_file, encoding="latin1")
    df_new.to_csv(f"{DATA_DIR}/asistencias_2026.csv", index=False)
    st.sidebar.success("CSV 2026 actualizado correctamente")

# ─────────────────────────────
# LECTURA HISTÓRICO + 2026
# ─────────────────────────────
dfs = []

# Histórico consolidado
if os.path.exists(f"{DATA_DIR}/historico_2023_2025.csv"):
    df_hist = pd.read_csv(f"{DATA_DIR}/historico_2023_2025.csv", encoding="latin1")
    dfs.append(df_hist)

# Año dinámico
if os.path.exists(f"{DATA_DIR}/asistencias_2026.csv"):
    df_2026 = pd.read_csv(f"{DATA_DIR}/asistencias_2026.csv", encoding="latin1")
    dfs.append(df_2026)

if not dfs:
    st.warning("No hay datos cargados.")
    st.stop()

df = pd.concat(dfs, ignore_index=True)
if not dfs:
    st.warning("No hay datos cargados.")
    st.stop()

df = pd.concat(dfs, ignore_index=True)
if not dfs:
    st.warning("No hay datos cargados.")
    st.stop()

df = pd.concat(dfs, ignore_index=True)

# ─────────────────────────────
# FECHAS Y LIMPIEZA
# ─────────────────────────────
# ─────────────────────────────
# FECHAS Y CREACIÓN DE AÑO / MES
# ─────────────────────────────
df["Fecha creación de asistencia"] = pd.to_datetime(
    df["Fecha creación de asistencia"],
    errors="coerce"
)

df["AÑO"] = df["Fecha creación de asistencia"].dt.year
df["MES"] = df["Fecha creación de asistencia"].dt.month
st.write("Años detectados:", df["AÑO"].unique())
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
canal = multiselect_filter("Canal de Origen", "Canal Origen")
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

if anio:
    df_f = df_f[df_f["AÑO"].isin(anio)]

if mes:
    df_f = df_f[df_f["MES"].isin(mes)]

if estado:
    df_f = df_f[df_f["Estado de Asistencia"].isin(estado)]

if canal:
    df_f = df_f[df_f["Canal Origen"].isin(canal)]

if grupo:
    df_f = df_f[df_f["Grupo de Servicio"].isin(grupo)]

if servicio:
    df_f = df_f[df_f["Nombre del Servicio"].isin(servicio)]

if subservicio:
    df_f = df_f[df_f["Nombre del Subservicio"].isin(subservicio)]

if especialidad:
    df_f = df_f[df_f["ESPECIALIDAD MEDICA (CITAS)"].isin(especialidad)]

if proveedor:
    df_f = df_f[df_f["Nombre del Proveedor"].isin(proveedor)]

if pais:
    df_f = df_f[df_f["País"].isin(pais)]
    
if provincia:
    df_f = df_f[df_f["Provincia"].isin(provincia)]

if ciudad:
    df_f = df_f[df_f["Ciudad"].isin(ciudad)]

if local_foraneo:
    df_f = df_f[df_f["Local_Foráneo"].isin(local_foraneo)]

if tipo_cliente:
    df_f = df_f[df_f["TIPO DE CLIENTE"].isin(tipo_cliente)]

if cliente:
    df_f = df_f[df_f["Cliente Institucional"].isin(cliente)]

if cuenta:
    df_f = df_f[df_f["Nombre de la cuenta"].isin(cuenta)]

if plan:
    df_f = df_f[df_f["Nombre del plan"].isin(plan)]

if evento:
    df_f = df_f[df_f["Tipo de Evento"].isin(evento)]

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
# GRÁFICOS DE TENDENCIA
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
st.subheader("🏆 Top servicios y especialidades")

col_a, col_b = st.columns(2)

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
    title="Top 10 Servicios (por número de asistencias)"
)
col_a.plotly_chart(fig_serv, use_container_width=True)

top_especialidad = (
    df_f.groupby("ESPECIALIDAD MEDICA (CITAS)")["Número Asistencia"]
    .count()
    .reset_index(name="Total asistencias")
    .sort_values("Total asistencias", ascending=False)
    .head(10)
)

fig_esp = px.bar(
    top_especialidad,
    x="ESPECIALIDAD MEDICA (CITAS)",
    y="Total asistencias",
    title="Top 10 Especialidades Médicas (por número de asistencias)"
)
col_b.plotly_chart(fig_esp, use_container_width=True)

# ─────────────────────────────
# ESTADO DE ASISTENCIA POR MES (TABLA ORDENADA)
# ─────────────────────────────
st.subheader("📋 Estado de Asistencia por Mes")

tabla_estado = (
    df_f
    .groupby(["Estado de Asistencia", "MES"])["Número Asistencia"]
    .count()
    .reset_index()
    .pivot(
        index="Estado de Asistencia",
        columns="MES",
        values="Número Asistencia"
    )
    .fillna(0)
    .astype(int)
)

# Agregar total por fila
tabla_estado["Total general"] = tabla_estado.sum(axis=1)

# Ordenar de mayor a menor por total
tabla_estado = tabla_estado.sort_values(
    by="Total general",
    ascending=False
)

# Agregar fila Total general al final
total_fila = tabla_estado.sum().to_frame().T
total_fila.index = ["Total general"]

tabla_estado = pd.concat([tabla_estado, total_fila])

st.dataframe(tabla_estado, use_container_width=True)

# ─────────────────────────────
# GRÁFICO PASTEL ESTADO DE ASISTENCIA (ORDENADO)
# ─────────────────────────────
st.subheader("🥧 % Estado de Asistencia")

estado_totales = (
    df_f
    .groupby("Estado de Asistencia")["Número Asistencia"]
    .count()
    .reset_index()
    .sort_values(by="Número Asistencia", ascending=False)
)

fig_pie = px.pie(
    estado_totales,
    names="Estado de Asistencia",
    values="Número Asistencia",
    title="% Estado de Asistencia",
    hole=0.4
)

st.plotly_chart(fig_pie, use_container_width=True)
