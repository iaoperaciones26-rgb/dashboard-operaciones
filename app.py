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

    # ───── Validaciones
    columnas_necesarias = [
        "Número Asistencia",
        "Total de Costo Global"
    ]

    for col in columnas_necesarias:
        if col not in df.columns:
            raise ValueError(f"No se encontró la columna: {col}")

    # ───── Fecha
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

    df["AÑO"] = df[fecha_col].dt.year.astype("int16")
    df["MES"] = df[fecha_col].dt.month.astype("int8")

    meses_dict = {
        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
    }

    df["MES_NOMBRE"] = df["MES"].map(meses_dict)

    # ───── Limpieza columnas clave
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

    # ───── Optimización memoria (MUY IMPORTANTE)
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
        "MES_NOMBRE"
    ]

    for col in columnas_categoricas:
        if col in df.columns:
            df[col] = df[col].astype("category")

    return df


# ─────────────────────────────
# EJECUCIÓN SEGURA
# ─────────────────────────────

try:
    df = cargar_datos()
    df = procesar_datos(df)
except Exception as e:
    st.error(f"Error procesando datos: {e}")
    st.stop()
