import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import plotly.express as px
import os
import sys
import io

# --- Configuración Inicial del Proyecto y Título de la Página ---
try:
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except NameError:
    project_root = os.getcwd()
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

st.set_page_config(layout="wide", page_title="Análisis de Sesiones y SQL")
st.title("📊 Análisis de Sesiones y Calificaciones SQL")
st.markdown(
    "Métricas por LG, AE, País, Calificación SQL (SQL1 > SQL2 > MQL > NA > Sin Calificación), Puesto y Empresa."
)

# --- Constantes ---
CREDS_PATH = "credenciales.json"
SHEET_URL_SESIONES = "https://docs.google.com/spreadsheets/d/1Cejc7xfxd62qqsbzBOMRSI9HiJjHe_JSFnjf3lrXai4/edit?gid=1354854902#gid=1354854902"
SHEET_NAME_SESIONES = "Sesiones 2024-2025"

COLUMNAS_ESPERADAS = [
    "Semana", "Mes", "Fecha", "SQL", "Empresa", "País", "Nombre", "Apellido",
    "Puesto", "Email", "AE", "LG", "Siguientes Pasos", "RPA"
]
COLUMNAS_DERIVADAS = [
    'Año', 'NumSemana', 'MesNombre', 'AñoMes', 'SQL_Estandarizado'
]
SQL_ORDER_OF_IMPORTANCE = ['SQL1', 'SQL2', 'MQL', 'NA', 'SIN CALIFICACIÓN SQL']

# --- Gestión de Estado de Sesión para Filtros ---
FILTER_KEYS_PREFIX = "sesiones_sql_lg_pais_page_v1_"
SES_START_DATE_KEY = f"{FILTER_KEYS_PREFIX}start_date"
SES_END_DATE_KEY = f"{FILTER_KEYS_PREFIX}end_date"
SES_AE_FILTER_KEY = f"{FILTER_KEYS_PREFIX}ae"
SES_LG_FILTER_KEY = f"{FILTER_KEYS_PREFIX}lg"
SES_PAIS_FILTER_KEY = f"{FILTER_KEYS_PREFIX}pais"
SES_YEAR_FILTER_KEY = f"{FILTER_KEYS_PREFIX}year"
SES_WEEK_FILTER_KEY = f"{FILTER_KEYS_PREFIX}week"
SES_SQL_FILTER_KEY = f"{FILTER_KEYS_PREFIX}sql_val"

default_filters_config = {
    SES_START_DATE_KEY: None,
    SES_END_DATE_KEY: None,
    SES_AE_FILTER_KEY: ["– Todos –"],
    SES_LG_FILTER_KEY: ["– Todos –"],
    SES_PAIS_FILTER_KEY: ["– Todos –"],
    SES_YEAR_FILTER_KEY: "– Todos –",
    SES_WEEK_FILTER_KEY: ["– Todas –"],
    SES_SQL_FILTER_KEY: ["– Todos –"]
}
for key, value in default_filters_config.items():
    if key not in st.session_state: st.session_state[key] = value


# --- Funciones de Utilidad ---
def parse_date_robust(date_val):
    if pd.isna(date_val) or str(date_val).strip() == "": return None
    try:
        return pd.to_datetime(date_val, format='%d/%m/%Y', errors='raise')
    except ValueError:
        try:
            return pd.to_datetime(date_val, errors='raise')
        except Exception:
            return None
    except Exception:
        return None


@st.cache_data(ttl=300)
def load_sesiones_data():
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            CREDS_PATH, scope)
        client = gspread.authorize(creds)
        workbook = client.open_by_url(SHEET_URL_SESIONES)
        try:
            sheet = workbook.worksheet(SHEET_NAME_SESIONES)
        except gspread.exceptions.WorksheetNotFound:
            st.error(f"Pestaña '{SHEET_NAME_SESIONES}' no encontrada.")
            return pd.DataFrame(columns=COLUMNAS_ESPERADAS +
                                COLUMNAS_DERIVADAS)
        raw_data = sheet.get_all_values()
        if not raw_data:
            st.error(f"Pestaña '{SHEET_NAME_SESIONES}' vacía.")
            return pd.DataFrame(columns=COLUMNAS_ESPERADAS +
                                COLUMNAS_DERIVADAS)

        headers_cleaned = [str(h).strip() for h in raw_data[0]]
        final_df_headers = [h for h in headers_cleaned if h]
        data_rows = [row[:len(final_df_headers)] for row in raw_data[1:]]
        df = pd.DataFrame(data_rows, columns=final_df_headers)

        if "Fecha" not in df.columns:
            st.error("Columna 'Fecha' no encontrada.")
            return pd.DataFrame(columns=COLUMNAS_ESPERADAS +
                                COLUMNAS_DERIVADAS)
        df["Fecha"] = df["Fecha"].apply(parse_date_robust)
        df.dropna(subset=["Fecha"], inplace=True)
        if df.empty:
            st.warning("No hay sesiones con fechas válidas.")
            return pd.DataFrame(columns=COLUMNAS_ESPERADAS +
                                COLUMNAS_DERIVADAS)

        df['Año'] = df['Fecha'].dt.year.astype('Int64')
        df['NumSemana'] = df['Fecha'].dt.isocalendar().week.astype('Int64')
        df['MesNombre'] = df['Fecha'].dt.month_name()
        df['AñoMes'] = df['Fecha'].dt.strftime('%Y-%m')

        if "SQL" not in df.columns: df["SQL"] = ""
        df['SQL_Estandarizado'] = df['SQL'].astype(str).str.strip().str.upper()
        known_sql_values = [
            s for s in SQL_ORDER_OF_IMPORTANCE if s != 'SIN CALIFICACIÓN SQL'
        ]
        mask_empty_sql = ~df['SQL_Estandarizado'].isin(known_sql_values) & (
            df['SQL_Estandarizado'].isin(['', 'NAN', 'NONE'])
            | df['SQL_Estandarizado'].isna())
        df.loc[mask_empty_sql, 'SQL_Estandarizado'] = 'SIN CALIFICACIÓN SQL'
        df.loc[df['SQL_Estandarizado'] == '',
               'SQL_Estandarizado'] = 'SIN CALIFICACIÓN SQL'

        for col_actor, default_actor_name in [("AE", "No Asignado AE"),
                                              ("LG", "No Asignado LG")]:
            if col_actor not in df.columns: df[col_actor] = default_actor_name
            df[col_actor] = df[col_actor].astype(str).str.strip()
            df.loc[df[col_actor].isin(['', 'nan', 'none', 'NaN', 'None']),
                   col_actor] = default_actor_name

        for col_clean in ["Puesto", "Empresa", "País"]:
            if col_clean not in df.columns: df[col_clean] = "No Especificado"
            df[col_clean] = df[col_clean].astype(str).str.strip()
            df.loc[df[col_clean].isin(['', 'nan', 'none', 'NaN', 'None']),
                   col_clean] = 'No Especificado'

        df_final = pd.DataFrame()
        all_final_cols = COLUMNAS_ESPERADAS + COLUMNAS_DERIVADAS
        for col in all_final_cols:
            if col in df.columns: df_final[col] = df[col]
            else:
                if col in COLUMNAS_ESPERADAS and col not in df.columns:
                    st.warning(f"Col. original '{col}' no encontrada.")
                if col in ['Año', 'NumSemana']:
                    df_final[col] = pd.Series(dtype='Int64')
                elif col == 'Fecha':
                    df_final[col] = pd.Series(dtype='datetime64[ns]')
                else:
                    df_final[col] = pd.Series(dtype='object')
        return df_final
    except FileNotFoundError:
        st.error(f"Error Crítico: Archivo '{CREDS_PATH}' no encontrado.")
        return pd.DataFrame(columns=COLUMNAS_ESPERADAS + COLUMNAS_DERIVADAS)
    except gspread.exceptions.APIError as e:
        st.error(f"Error Crítico API Google: {e}")
        return pd.DataFrame(columns=COLUMNAS_ESPERADAS + COLUMNAS_DERIVADAS)
    except Exception as e:
        st.error(f"Error inesperado en carga: {e}")
        st.exception(e)
        return pd.DataFrame()


def clear_ses_filters_callback():
    for key, value in default_filters_config.items():
        st.session_state[key] = value
    st.toast("Filtros reiniciados ✅", icon="🧹")


def sidebar_filters_sesiones(df_options):
    st.sidebar.header("🔍 Filtros de Sesiones")
    st.sidebar.markdown("---")
    min_d, max_d = (df_options["Fecha"].min().date(), df_options["Fecha"].max(
    ).date()) if "Fecha" in df_options and not df_options["Fecha"].dropna(
    ).empty and pd.api.types.is_datetime64_any_dtype(
        df_options["Fecha"]) else (None, None)
    c1, c2 = st.sidebar.columns(2)
    c1.date_input("Desde",
                  value=st.session_state[SES_START_DATE_KEY],
                  min_value=min_d,
                  max_value=max_d,
                  format="DD/MM/YYYY",
                  key=SES_START_DATE_KEY)
    c2.date_input("Hasta",
                  value=st.session_state[SES_END_DATE_KEY],
                  min_value=min_d,
                  max_value=max_d,
                  format="DD/MM/YYYY",
                  key=SES_END_DATE_KEY)

    st.sidebar.markdown("---")
    years = ["– Todos –"
             ] + (sorted(df_options["Año"].dropna().astype(int).unique(),
                         reverse=True) if "Año" in df_options
                  and not df_options["Año"].dropna().empty else [])
    current_year_val_in_state = st.session_state[SES_YEAR_FILTER_KEY]
    if current_year_val_in_state not in years:
        st.session_state[SES_YEAR_FILTER_KEY] = "– Todos –"
    st.sidebar.selectbox("Año", years, key=SES_YEAR_FILTER_KEY)
    sel_y = int(
        st.session_state[SES_YEAR_FILTER_KEY]
    ) if st.session_state[SES_YEAR_FILTER_KEY] != "– Todos –" else None

    weeks_df = df_options[
        df_options["Año"] ==
        sel_y] if sel_y is not None and "Año" in df_options.columns else df_options
    weeks = ["– Todas –"
             ] + (sorted(weeks_df["NumSemana"].dropna().astype(int).unique())
                  if "NumSemana" in weeks_df
                  and not weeks_df["NumSemana"].dropna().empty else [])
    current_week_selection_in_state = st.session_state[SES_WEEK_FILTER_KEY]
    validated_week_selection = [
        val for val in current_week_selection_in_state if val in weeks
    ]
    if not validated_week_selection:
        st.session_state[SES_WEEK_FILTER_KEY] = [
            "– Todas –"
        ] if "– Todas –" in weeks else (
            [weeks[0]] if weeks and weeks[0] != "– Todas –" else [])
    elif len(validated_week_selection) != len(current_week_selection_in_state):
        st.session_state[SES_WEEK_FILTER_KEY] = validated_week_selection
    st.sidebar.multiselect("Semanas", weeks, key=SES_WEEK_FILTER_KEY)

    st.sidebar.markdown("---")
    st.sidebar.subheader("👥 Por Analistas, País y Calificación")

    lgs_options = ["– Todos –"] + (sorted(df_options["LG"].dropna().unique(
    )) if "LG" in df_options and not df_options["LG"].dropna().empty else [])
    current_lg_selection_in_state = st.session_state[SES_LG_FILTER_KEY]
    validated_lg_selection = [
        val for val in current_lg_selection_in_state if val in lgs_options
    ]
    if not validated_lg_selection:
        st.session_state[SES_LG_FILTER_KEY] = [
            "– Todos –"
        ] if "– Todos –" in lgs_options else (
            [lgs_options[0]]
            if lgs_options and lgs_options[0] != "– Todos –" else [])
    elif len(validated_lg_selection) != len(current_lg_selection_in_state):
        st.session_state[SES_LG_FILTER_KEY] = validated_lg_selection
    st.sidebar.multiselect("Analista LG", lgs_options, key=SES_LG_FILTER_KEY)

    ae_options = ["– Todos –"] + (sorted(df_options["AE"].dropna().unique(
    )) if "AE" in df_options and not df_options["AE"].dropna().empty else [])
    current_ae_selection_in_state = st.session_state[SES_AE_FILTER_KEY]
    validated_ae_selection = [
        val for val in current_ae_selection_in_state if val in ae_options
    ]
    if not validated_ae_selection:
        st.session_state[SES_AE_FILTER_KEY] = [
            "– Todos –"
        ] if "– Todos –" in ae_options else (
            [ae_options[0]]
            if ae_options and ae_options[0] != "– Todos –" else [])
    elif len(validated_ae_selection) != len(current_ae_selection_in_state):
        st.session_state[SES_AE_FILTER_KEY] = validated_ae_selection
    st.sidebar.multiselect("Account Executive (AE)",
                           ae_options,
                           key=SES_AE_FILTER_KEY)

    paises_opts = ["– Todos –"] + (
        sorted(df_options["País"].dropna().unique()) if "País" in df_options
        and not df_options["País"].dropna().empty else [])
    current_pais_selection_in_state = st.session_state[SES_PAIS_FILTER_KEY]
    validated_pais_selection = [
        val for val in current_pais_selection_in_state if val in paises_opts
    ]
    if not validated_pais_selection:
        st.session_state[SES_PAIS_FILTER_KEY] = [
            "– Todos –"
        ] if "– Todos –" in paises_opts else (
            [paises_opts[0]]
            if paises_opts and paises_opts[0] != "– Todos –" else [])
    elif len(validated_pais_selection) != len(current_pais_selection_in_state):
        st.session_state[SES_PAIS_FILTER_KEY] = validated_pais_selection
    st.sidebar.multiselect("País", paises_opts, key=SES_PAIS_FILTER_KEY)

    sqls_opts = ["– Todos –"] + (
        sorted(df_options["SQL_Estandarizado"].dropna().unique(),
               key=lambda x: SQL_ORDER_OF_IMPORTANCE.index(x) if x in
               SQL_ORDER_OF_IMPORTANCE else len(SQL_ORDER_OF_IMPORTANCE))
        if "SQL_Estandarizado" in df_options
        and not df_options["SQL_Estandarizado"].dropna().empty else [])
    current_sql_selection_in_state = st.session_state[SES_SQL_FILTER_KEY]
    validated_sql_selection = [
        val for val in current_sql_selection_in_state if val in sqls_opts
    ]
    if not validated_sql_selection:
        st.session_state[SES_SQL_FILTER_KEY] = [
            "– Todos –"
        ] if "– Todos –" in sqls_opts else (
            [sqls_opts[0]]
            if sqls_opts and sqls_opts[0] != "– Todos –" else [])
    elif len(validated_sql_selection) != len(current_sql_selection_in_state):
        st.session_state[SES_SQL_FILTER_KEY] = validated_sql_selection
    st.sidebar.multiselect("Calificación SQL",
                           sqls_opts,
                           key=SES_SQL_FILTER_KEY)

    st.sidebar.markdown("---")
    st.sidebar.button("🧹 Limpiar Todos los Filtros",
                      on_click=clear_ses_filters_callback,
                      use_container_width=True,
                      key=f"{FILTER_KEYS_PREFIX}btn_clear")
    return (st.session_state[SES_START_DATE_KEY],
            st.session_state[SES_END_DATE_KEY], sel_y,
            st.session_state[SES_WEEK_FILTER_KEY],
            st.session_state[SES_AE_FILTER_KEY],
            st.session_state[SES_LG_FILTER_KEY],
            st.session_state[SES_PAIS_FILTER_KEY],
            st.session_state[SES_SQL_FILTER_KEY])


def apply_sesiones_filters(df, start_date, end_date, year_f, week_f, ae_f,
                           lg_f, pais_f, sql_f):
    if df is None or df.empty: return pd.DataFrame()
    df_f = df.copy()
    if "Fecha" in df_f.columns and pd.api.types.is_datetime64_any_dtype(
            df_f["Fecha"]):
        if start_date and end_date:
            df_f = df_f[(df_f["Fecha"].dt.date >= start_date)
                        & (df_f["Fecha"].dt.date <= end_date)]
        elif start_date:
            df_f = df_f[df_f["Fecha"].dt.date >= start_date]
        elif end_date:
            df_f = df_f[df_f["Fecha"].dt.date <= end_date]
    if year_f is not None and "Año" in df_f.columns:
        df_f = df_f[df_f["Año"] == year_f]
    if week_f and "– Todas –" not in week_f and "NumSemana" in df_f.columns:
        valid_w = [
            int(w) for w in week_f
            if (isinstance(w, str) and w.isdigit()) or isinstance(w, int)
        ]
        if valid_w: df_f = df_f[df_f["NumSemana"].isin(valid_w)]
    if ae_f and "– Todos –" not in ae_f and "AE" in df_f.columns:
        df_f = df_f[df_f["AE"].isin(ae_f)]
    if lg_f and "– Todos –" not in lg_f and "LG" in df_f.columns:
        df_f = df_f[df_f["LG"].isin(lg_f)]
    if pais_f and "– Todos –" not in pais_f and "País" in df_f.columns:
        df_f = df_f[df_f["País"].isin(pais_f)]
    if sql_f and "– Todos –" not in sql_f and "SQL_Estandarizado" in df_f.columns:
        df_f = df_f[df_f["SQL_Estandarizado"].isin(sql_f)]
    return df_f


def get_sql_category_order(df_column_or_list):
    present_sqls = pd.Series(df_column_or_list).unique()
    ordered_present_sqls = [
        s for s in SQL_ORDER_OF_IMPORTANCE if s in present_sqls
    ]
    other_sqls = sorted(
        [s for s in present_sqls if s not in ordered_present_sqls])
    return ordered_present_sqls + other_sqls


def display_sesiones_summary_sql(df_filtered):
    st.markdown("### 📌 Resumen Principal de Sesiones")
    if df_filtered.empty:
        st.info("No hay sesiones para resumen.")
        return
    total_sesiones = len(df_filtered)
    st.metric("Total Sesiones (filtradas)", f"{total_sesiones:,}")
    if 'SQL_Estandarizado' in df_filtered.columns:
        st.markdown("#### Distribución por Calificación SQL")
        # CORRECCIÓN: Eliminar observed=True de value_counts si da error, o ajustar según versión de Pandas.
        # Para compatibilidad con versiones más antiguas, se elimina.
        sql_counts = df_filtered['SQL_Estandarizado'].value_counts(
        ).reset_index()
        sql_counts.columns = ['Calificación SQL', 'Número de Sesiones']

        category_order = get_sql_category_order(sql_counts['Calificación SQL'])
        sql_counts['Calificación SQL'] = pd.Categorical(
            sql_counts['Calificación SQL'],
            categories=category_order,
            ordered=True)
        sql_counts = sql_counts.sort_values('Calificación SQL')
        if not sql_counts.empty:
            fig = px.bar(sql_counts,
                         x='Calificación SQL',
                         y='Número de Sesiones',
                         title='Sesiones por Calificación SQL',
                         text_auto=True,
                         color='Calificación SQL',
                         category_orders={"Calificación SQL": category_order})
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(sql_counts.set_index('Calificación SQL').style.format(
                {"Número de Sesiones": "{:,}"}),
                         use_container_width=True)
    else:
        st.warning("Columna 'SQL_Estandarizado' no encontrada.")


def display_analisis_por_dimension(df_filtered,
                                   dimension_col,
                                   dimension_label,
                                   top_n=10):
    st.markdown(
        f"### 📊 Análisis por {dimension_label} y Calificación SQL (Top {top_n})"
    )
    if df_filtered.empty or dimension_col not in df_filtered.columns or 'SQL_Estandarizado' not in df_filtered.columns:
        st.info(f"Datos insuficientes para análisis por {dimension_label}.")
        return

    sql_category_order = get_sql_category_order(
        df_filtered['SQL_Estandarizado'])

    summary_dim_sql = df_filtered.groupby(
        [dimension_col, 'SQL_Estandarizado'], as_index=False,
        observed=True)['Fecha'].count().rename(
            columns={'Fecha': 'Cantidad_SQL'})

    dim_totals = df_filtered.groupby(dimension_col,
                                     as_index=False,
                                     observed=True)['Fecha'].count().rename(
                                         columns={'Fecha': 'Total_Sesiones'})

    top_n_dims = dim_totals.sort_values(
        by='Total_Sesiones',
        ascending=False).head(top_n)[dimension_col].tolist()
    summary_dim_sql_top_n = summary_dim_sql[
        summary_dim_sql[dimension_col].isin(top_n_dims)].copy()

    if summary_dim_sql_top_n.empty:
        st.info(f"No hay datos agregados por {dimension_label} y SQL.")
        return

    summary_dim_sql_top_n['SQL_Estandarizado'] = pd.Categorical(
        summary_dim_sql_top_n['SQL_Estandarizado'],
        categories=sql_category_order,
        ordered=True)

    if not summary_dim_sql_top_n.empty:
        fig = px.bar(summary_dim_sql_top_n,
                     x=dimension_col,
                     y='Cantidad_SQL',
                     color='SQL_Estandarizado',
                     title=f'Distribución de SQL por {dimension_label}',
                     barmode='stack',
                     category_orders={
                         dimension_col: top_n_dims,
                         "SQL_Estandarizado": sql_category_order
                     },
                     color_discrete_sequence=px.colors.qualitative.Vivid)
        fig.update_layout(xaxis_tickangle=-45,
                          yaxis_title="Número de Sesiones")
        st.plotly_chart(fig, use_container_width=True)

    pivot_table = summary_dim_sql_top_n.pivot_table(
        index=dimension_col,
        columns='SQL_Estandarizado',
        values='Cantidad_SQL',
        fill_value=0)
    for sql_cat in sql_category_order:
        if sql_cat not in pivot_table.columns: pivot_table[sql_cat] = 0
    pivot_table_cols_ordered = [col for col in sql_category_order if col in pivot_table.columns] + \
                               [col for col in pivot_table.columns if col not in sql_category_order]
    pivot_table = pivot_table.reindex(columns=pivot_table_cols_ordered,
                                      fill_value=0)
    pivot_table = pivot_table.reindex(index=top_n_dims, fill_value=0)
    pivot_table['Total_Sesiones_Dim'] = pivot_table.sum(axis=1)

    for col in pivot_table.columns:
        try:
            pivot_table[col] = pd.to_numeric(
                pivot_table[col], errors='coerce').fillna(0).astype(int)
        except ValueError:
            st.warning(
                f"Advertencia: Col '{col}' en pivot_table no pudo ser convertida a entero."
            )
            pivot_table[col] = pivot_table[col].astype(str)

    format_dict = {
        col: "{:,.0f}"
        for col in pivot_table.columns
        if pd.api.types.is_numeric_dtype(pivot_table[col])
    }
    if format_dict:
        st.dataframe(pivot_table.style.format(format_dict),
                     use_container_width=True)
    else:
        st.dataframe(pivot_table, use_container_width=True)


def display_evolucion_sql(df_filtered, time_agg_col, display_label,
                          chart_title, x_axis_label):
    st.markdown(f"### 📈 {chart_title}")
    if df_filtered.empty or 'SQL_Estandarizado' not in df_filtered.columns:
        st.info(f"Datos insuficientes.")
        return
    df_agg = df_filtered.copy()
    group_col = time_agg_col
    if time_agg_col == 'NumSemana':
        if not ('Año' in df_agg.columns and 'NumSemana' in df_agg.columns):
            st.warning("Faltan Año/NumSemana.")
            return
        df_agg.dropna(subset=['Año', 'NumSemana'], inplace=True)
        if df_agg.empty:
            st.info("No hay datos para evolución semanal.")
            return
        df_agg['Año-Semana'] = df_agg['Año'].astype(int).astype(
            str) + '-S' + df_agg['NumSemana'].astype(int).astype(
                str).str.zfill(2)
        group_col = 'Año-Semana'
        df_agg = df_agg.sort_values(by=group_col)
    elif time_agg_col == 'AñoMes':
        if 'AñoMes' not in df_agg.columns:
            st.warning("Columna 'AñoMes' faltante.")
            return
        df_agg = df_agg.sort_values(by='AñoMes')

    sql_category_order = get_sql_category_order(df_agg['SQL_Estandarizado'])
    summary_time_sql = df_agg.groupby(
        [group_col, 'SQL_Estandarizado'], as_index=False,
        observed=True)['Fecha'].count().rename(
            columns={'Fecha': 'Número de Sesiones'})

    if summary_time_sql.empty:
        st.info(f"No hay datos agregados por {x_axis_label.lower()} y SQL.")
        return
    summary_time_sql['SQL_Estandarizado'] = pd.Categorical(
        summary_time_sql['SQL_Estandarizado'],
        categories=sql_category_order,
        ordered=True)
    summary_time_sql = summary_time_sql.sort_values(
        [group_col, 'SQL_Estandarizado'])
    st.dataframe(summary_time_sql.style.format({"Número de Sesiones": "{:,}"}),
                 use_container_width=True)
    try:
        fig = px.line(
            summary_time_sql,
            x=group_col,
            y='Número de Sesiones',
            color='SQL_Estandarizado',
            title=f"Evolución por SQL ({x_axis_label})",
            markers=True,
            category_orders={"SQL_Estandarizado": sql_category_order})
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"No se pudo generar gráfico: {e}")


def display_tabla_sesiones_detalle(df_filtered):
    st.markdown("### 📝 Tabla Detallada de Sesiones")
    if df_filtered.empty:
        st.info("No hay sesiones detalladas para mostrar.")
        return
    cols_display = [
        "Fecha", "LG", "AE", "País", "SQL", "SQL_Estandarizado", "Empresa",
        "Puesto", "Nombre", "Apellido", "Siguientes Pasos"
    ]
    cols_present = [col for col in cols_display if col in df_filtered.columns]
    df_view = df_filtered[cols_present].copy()
    if "Fecha" in df_view.columns and pd.api.types.is_datetime64_any_dtype(
            df_view["Fecha"]):
        df_view["Fecha"] = pd.to_datetime(
            df_view["Fecha"]).dt.strftime('%d/%m/%Y')
    st.dataframe(df_view, height=400, use_container_width=True)
    if not df_view.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_view.to_excel(writer,
                             index=False,
                             sheet_name='Detalle_Sesiones')
        st.download_button(
            label="⬇️ Descargar Detalle (Excel)",
            data=output.getvalue(),
            file_name="detalle_sesiones_sql.xlsx",
            mime=
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{FILTER_KEYS_PREFIX}btn_download_detalle")


# --- Flujo Principal de la Página ---
df_sesiones_raw = load_sesiones_data()
if df_sesiones_raw is None or df_sesiones_raw.empty:
    st.error("Fallo Crítico al cargar datos. La página no puede continuar.")
    st.stop()

start_f, end_f, year_f, week_f, ae_f, lg_f, pais_f, sql_f_val = sidebar_filters_sesiones(
    df_sesiones_raw)
df_sesiones_filtered = apply_sesiones_filters(df_sesiones_raw, start_f, end_f,
                                              year_f, week_f, ae_f, lg_f,
                                              pais_f, sql_f_val)

display_sesiones_summary_sql(df_sesiones_filtered)
st.markdown("---")
display_analisis_por_dimension(df_filtered=df_sesiones_filtered,
                               dimension_col="LG",
                               dimension_label="Analista LG",
                               top_n=15)
st.markdown("---")
display_analisis_por_dimension(df_filtered=df_sesiones_filtered,
                               dimension_col="AE",
                               dimension_label="Account Executive",
                               top_n=15)
st.markdown("---")
display_analisis_por_dimension(df_filtered=df_sesiones_filtered,
                               dimension_col="País",
                               dimension_label="País",
                               top_n=10)
st.markdown("---")
display_analisis_por_dimension(df_filtered=df_sesiones_filtered,
                               dimension_col="Puesto",
                               dimension_label="Cargo (Puesto)",
                               top_n=10)
st.markdown("---")
display_analisis_por_dimension(df_filtered=df_sesiones_filtered,
                               dimension_col="Empresa",
                               dimension_label="Empresa",
                               top_n=10)
st.markdown("---")
display_evolucion_sql(df_sesiones_filtered, 'NumSemana', 'Año-Semana',
                      "Evolución Semanal por Calificación SQL",
                      "Semana del Año")
st.markdown("---")
display_evolucion_sql(df_sesiones_filtered, 'AñoMes', 'Año-Mes',
                      "Evolución Mensual por Calificación SQL", "Mes del Año")
st.markdown("---")
display_tabla_sesiones_detalle(df_sesiones_filtered)

# --- PIE DE PÁGINA ---
st.markdown("---")
st.info(
    "Esta maravillosa, caótica y probablemente sobrecafeinada plataforma ha sido realizada por Johnsito ✨ 😊"
)
