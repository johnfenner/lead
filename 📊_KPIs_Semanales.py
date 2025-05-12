import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import plotly.express as px
import os
import sys

# --- Configuración Inicial del Proyecto y Título de la Página ---
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, project_root)

st.set_page_config(layout="wide")

st.title("📊 Dashboard de KPIs y Tasas de Conversión")
st.markdown(
    "Análisis de métricas absolutas y tasas de conversión por analista, región, y periodo."
)

# --- Funciones de Procesamiento de Datos ---


def parse_kpi_value(value_str, column_name=""):
    cleaned_val = str(value_str).strip().lower()
    if not cleaned_val: return 0.0
    try:
        num_val = pd.to_numeric(cleaned_val, errors='raise')
        return 0.0 if pd.isna(num_val) else float(num_val)
    except ValueError:
        pass
    if column_name == "Sesiones agendadas":
        affirmative_session_texts = ['vc', 'si', 'sí', 'yes', 'true']
        if cleaned_val in affirmative_session_texts: return 1.0
        return 0.0
    else:
        first_part = cleaned_val.split('-')[0].strip()
        if not first_part: return 0.0
        try:
            num_val_from_part = pd.to_numeric(first_part, errors='raise')
            return 0.0 if pd.isna(num_val_from_part) else float(
                num_val_from_part)
        except ValueError:
            return 0.0


@st.cache_data
def load_weekly_kpis_data():
    creds_path = "credenciales.json"
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            creds_path, scope)
        client = gspread.authorize(creds)
    except FileNotFoundError:
        st.error(
            f"Error: El archivo de credenciales '{creds_path}' no se encontró."
        )
        st.info(
            f"Por favor, asegúrate de que el archivo 'credenciales.json' esté en la ubicación correcta: {os.path.abspath(creds_path)}"
        )
        st.stop()
    except Exception as e:
        st.error(f"Error al autenticar con Google Sheets: {e}")
        st.stop()

    sheet_url = "https://docs.google.com/spreadsheets/d/1vaJ2lPK7hbWsuikjmycPePKRrFXiOrlwXMXOdoXRY60/edit?gid=0#gid=0"
    try:
        sheet = client.open_by_url(sheet_url).sheet1
        raw_data = sheet.get_all_values()
        if not raw_data or len(raw_data) <= 1:
            st.error(
                "No se pudieron obtener datos suficientes de Google Sheets. La hoja podría estar vacía o solo tener encabezados."
            )
            st.stop()
        headers = raw_data[0]
        rows = raw_data[1:]
    except Exception as e:
        st.error(f"Error al leer la hoja de Google Sheets: {e}")
        st.stop()

    cleaned_headers = [h.strip() for h in headers]
    df = pd.DataFrame(rows, columns=cleaned_headers)

    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"],
                                     format='%d/%m/%Y',
                                     errors='coerce')
        df.dropna(subset=["Fecha"], inplace=True)
        if not df.empty:
            df['Año'] = df['Fecha'].dt.year
            df['NumSemana'] = df['Fecha'].dt.isocalendar().week.astype(int)
            df['MesNum'] = df['Fecha'].dt.month
            df['AñoMes'] = df['Fecha'].dt.strftime('%Y-%m')
        else:
            st.warning(
                "No hay datos con fechas válidas después de la conversión.")
            for col in ['Año', 'NumSemana', 'MesNum']:
                df[col] = pd.Series(dtype='int')
            df['AñoMes'] = pd.Series(dtype='str')
    else:
        st.warning(
            "Columna 'Fecha' no encontrada. No se podrán aplicar filtros de fecha, año, semana o mes."
        )
        for col in ['Año', 'NumSemana', 'MesNum']:
            df[col] = pd.Series(dtype='int')
        df['AñoMes'] = pd.Series(dtype='str')

    # CORRECCIÓN: Procesar TODAS las columnas de KPI esperadas para asegurar que sean numéricas.
    numeric_kpi_columns = [
        "Mensajes Enviados", "Respuestas", "Invites enviadas",
        "Sesiones agendadas"
    ]
    for col_name in numeric_kpi_columns:
        if col_name not in df.columns:
            st.warning(
                f"Columna KPI '{col_name}' no encontrada. Se creará con ceros."
            )
            df[col_name] = 0  # Crear con ceros int si no existe
        else:
            # Aplicar siempre el parseo y conversión a int para asegurar consistencia,
            # ya que los datos de Google Sheets vienen como strings vía get_all_values().
            df[col_name] = df[col_name].apply(
                lambda x: parse_kpi_value(x, column_name=col_name)).astype(int)

    string_cols = ["Mes", "Semana", "Analista", "Región"]
    for col in string_cols:
        if col not in df.columns:
            df[col] = pd.Series(dtype='str')
        else:
            df[col] = df[col].astype(str).str.strip()

    return df


# --- Función para calcular tasas de forma segura ---
def calculate_rate(numerator, denominator, round_to=1):
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, round_to)


# --- Carga de Datos ---
df_kpis_semanales_raw = load_weekly_kpis_data()
if df_kpis_semanales_raw.empty:
    st.error(
        "El DataFrame está vacío después de la carga y el procesamiento inicial. No se puede continuar."
    )
    st.stop()

# --- Estado de Sesión para Filtros ---
START_DATE_KEY = "kpis_page_fecha_inicio_v6"
END_DATE_KEY = "kpis_page_fecha_fin_v6"
ANALISTA_FILTER_KEY = "kpis_page_filtro_Analista_v6"
REGION_FILTER_KEY = "kpis_page_filtro_Región_v6"
YEAR_FILTER_KEY = "kpis_page_filtro_Año_v6"
WEEK_FILTER_KEY = "kpis_page_filtro_Semana_v6"

default_filters = {
    START_DATE_KEY: None,
    END_DATE_KEY: None,
    ANALISTA_FILTER_KEY: ["– Todos –"],
    REGION_FILTER_KEY: ["– Todos –"],
    YEAR_FILTER_KEY: "– Todos –",
    WEEK_FILTER_KEY: ["– Todas –"]
}
for key, default_val in default_filters.items():
    if key not in st.session_state: st.session_state[key] = default_val


# --- Funciones de la Interfaz de Usuario ---
def clear_kpis_filters_callback():
    for key, default_val in default_filters.items():
        st.session_state[key] = default_val
    st.toast("Filtros reiniciados ✅", icon="🧹")


def sidebar_filters(df_options):
    st.sidebar.header("🔍 Filtros de KPIs")
    st.sidebar.markdown("---")
    st.sidebar.subheader("🗓️ Por Fecha")
    min_date_data, max_date_data = None, None
    if "Fecha" in df_options.columns and pd.api.types.is_datetime64_any_dtype(
            df_options["Fecha"]) and not df_options["Fecha"].dropna().empty:
        min_date_data, max_date_data = df_options["Fecha"].dropna().min().date(
        ), df_options["Fecha"].dropna().max().date()
    col1_date, col2_date = st.sidebar.columns(2)
    with col1_date:
        st.date_input("Desde",
                      value=st.session_state.get(START_DATE_KEY),
                      min_value=min_date_data,
                      max_value=max_date_data,
                      format='DD/MM/YYYY',
                      key=START_DATE_KEY)
    with col2_date:
        st.date_input("Hasta",
                      value=st.session_state.get(END_DATE_KEY),
                      min_value=min_date_data,
                      max_value=max_date_data,
                      format='DD/MM/YYYY',
                      key=END_DATE_KEY)
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 Por Año y Semana")
    year_options = ["– Todos –"] + (
        sorted(df_options["Año"].dropna().astype(int).unique(), reverse=True)
        if "Año" in df_options.columns and not df_options["Año"].dropna().empty
        else [])
    current_year_selection = st.session_state.get(YEAR_FILTER_KEY, "– Todos –")
    if current_year_selection not in year_options:
        st.session_state[YEAR_FILTER_KEY] = "– Todos –"
    selected_year_str = st.sidebar.selectbox("Año",
                                             year_options,
                                             key=YEAR_FILTER_KEY)
    selected_year_int = int(
        selected_year_str) if selected_year_str != "– Todos –" else None
    week_options = ["– Todas –"]
    df_for_week = df_options[
        df_options["Año"] ==
        selected_year_int] if selected_year_int is not None and "NumSemana" in df_options.columns and "Año" in df_options.columns else df_options
    if "NumSemana" in df_for_week.columns and not df_for_week[
            "NumSemana"].dropna().empty:
        week_options.extend([
            str(w) for w in sorted(df_for_week["NumSemana"].dropna().astype(
                int).unique())
        ])
    current_week_selection = st.session_state.get(WEEK_FILTER_KEY,
                                                  ["– Todas –"])
    valid_week_selection = [
        s for s in current_week_selection if s in week_options
    ] or (["– Todas –"] if "– Todas –" in week_options else [])
    if valid_week_selection != current_week_selection:
        st.session_state[WEEK_FILTER_KEY] = valid_week_selection
    st.sidebar.multiselect("Semanas del Año",
                           week_options,
                           key=WEEK_FILTER_KEY)
    st.sidebar.markdown("---")
    st.sidebar.subheader("👥 Por Analista y Región")

    def get_multiselect_val(col_name, label, key, df_opt):
        options = ["– Todos –"]
        if col_name in df_opt.columns and not df_opt[col_name].dropna().empty:
            unique_vals = df_opt[col_name].astype(str).str.strip().replace(
                '', 'N/D').unique()
            options.extend(
                sorted([val for val in unique_vals if val and val != 'N/D']))
            if 'N/D' in unique_vals and 'N/D' not in options:
                options.append('N/D')
        current_selection = st.session_state.get(key, ["– Todos –"])
        if not isinstance(current_selection, list):
            current_selection = ["– Todos –"]
        valid_selection = [
            s for s in current_selection if s in options
        ] or (["– Todos –"] if "– Todos –" in options else [])
        if valid_selection != current_selection:
            st.session_state[key] = valid_selection
        return st.sidebar.multiselect(label, options, key=key)

    analista_filter_val = get_multiselect_val("Analista", "Analista",
                                              ANALISTA_FILTER_KEY, df_options)
    region_filter_val = get_multiselect_val("Región", "Región",
                                            REGION_FILTER_KEY, df_options)
    st.sidebar.markdown("---")
    st.sidebar.button("🧹 Limpiar Todos los Filtros",
                      on_click=clear_kpis_filters_callback,
                      use_container_width=True)
    return (st.session_state[START_DATE_KEY], st.session_state[END_DATE_KEY],
            selected_year_int, st.session_state[WEEK_FILTER_KEY],
            analista_filter_val, region_filter_val)


def apply_kpis_filters(df, start_dt, end_dt, year_val, week_list,
                       analista_list, region_list):
    df_f = df.copy()
    if "Fecha" in df_f.columns and pd.api.types.is_datetime64_any_dtype(
            df_f["Fecha"]):
        start_dt_date = start_dt.date() if isinstance(
            start_dt, datetime.datetime) else start_dt
        end_dt_date = end_dt.date() if isinstance(
            end_dt, datetime.datetime) else end_dt
        if start_dt_date and end_dt_date:
            df_f = df_f[(df_f["Fecha"].dt.date >= start_dt_date)
                        & (df_f["Fecha"].dt.date <= end_dt_date)]
        elif start_dt_date:
            df_f = df_f[df_f["Fecha"].dt.date >= start_dt_date]
        elif end_dt_date:
            df_f = df_f[df_f["Fecha"].dt.date <= end_dt_date]
    if year_val is not None and "Año" in df_f.columns:
        df_f = df_f[df_f["Año"] == year_val]
    if week_list and "– Todas –" not in week_list and "NumSemana" in df_f.columns:
        selected_weeks_int = [int(w) for w in week_list if w.isdigit()]
        if selected_weeks_int:
            df_f = df_f[df_f["NumSemana"].isin(selected_weeks_int)]
    if "Analista" in df_f.columns:
        df_f["Analista"] = df_f["Analista"].astype(str).str.strip().replace(
            '', 'N/D')
    if "Región" in df_f.columns:
        df_f["Región"] = df_f["Región"].astype(str).str.strip().replace(
            '', 'N/D')
    if analista_list and "– Todos –" not in analista_list and "Analista" in df_f.columns:
        df_f = df_f[df_f["Analista"].isin(analista_list)]
    if region_list and "– Todos –" not in region_list and "Región" in df_f.columns:
        df_f = df_f[df_f["Región"].isin(region_list)]
    return df_f


def display_filtered_kpis_table(df_filtered):
    st.markdown("### 📝 Datos Detallados Filtrados")
    if df_filtered.empty:
        st.info("No se encontraron datos que cumplan los criterios de filtro.")
        return
    st.write(f"Mostrando **{len(df_filtered)}** filas.")
    cols_display = [
        "Fecha", "Año", "NumSemana", "AñoMes", "Analista", "Región",
        "Mensajes Enviados", "Respuestas", "Invites enviadas",
        "Sesiones agendadas"
    ]
    if "Semana" in df_filtered.columns: cols_display.insert(3, "Semana")
    cols_present = [col for col in cols_display if col in df_filtered.columns]
    df_display_table = df_filtered[cols_present].copy()
    if "Fecha" in df_display_table.columns:
        df_display_table["Fecha"] = df_display_table["Fecha"].dt.strftime(
            '%d/%m/%Y')
    st.dataframe(df_display_table, use_container_width=True, height=300)


def display_kpi_summary(df_filtered):
    st.markdown(
        "### 🧮 Resumen de KPIs Totales y Tasas Globales (Periodo Filtrado)")
    kpi_cols = [
        "Mensajes Enviados", "Respuestas", "Invites enviadas",
        "Sesiones agendadas"
    ]
    icons = ["📤", "💬", "📧", "🤝"]

    metrics = {}
    if df_filtered.empty:
        for col_name in kpi_cols:
            metrics[col_name] = 0
    else:
        for col_name in kpi_cols:
            # Asegurarse que la columna exista y sea numérica antes de sumar
            if col_name in df_filtered.columns and pd.api.types.is_numeric_dtype(
                    df_filtered[col_name]):
                metrics[col_name] = df_filtered[col_name].sum()
            else:
                metrics[
                    col_name] = 0  # Default a 0 si la columna no es numérica o no existe

    col_metrics_abs = st.columns(len(kpi_cols))
    for i, col_name in enumerate(kpi_cols):
        col_metrics_abs[i].metric(f"{icons[i]} Total {col_name.split(' ')[0]}",
                                  f"{metrics.get(col_name, 0):,}")

    st.markdown("---")
    total_mensajes = metrics.get("Mensajes Enviados", 0)
    total_respuestas = metrics.get("Respuestas", 0)
    total_sesiones = metrics.get("Sesiones agendadas", 0)

    tasa_resp_global = calculate_rate(total_respuestas, total_mensajes)
    tasa_agen_vs_env_global = calculate_rate(total_sesiones, total_mensajes)
    tasa_agen_vs_resp_global = calculate_rate(total_sesiones, total_respuestas)

    rate_icons = ["📈", "🎯", "✨"]
    col_metrics_rates = st.columns(3)
    col_metrics_rates[0].metric(f"{rate_icons[0]} Tasa Respuesta Global",
                                f"{tasa_resp_global}%")
    col_metrics_rates[1].metric(f"{rate_icons[1]} Tasa Agend. (vs Env.)",
                                f"{tasa_agen_vs_env_global}%")
    col_metrics_rates[2].metric(f"{rate_icons[2]} Tasa Agend. (vs Resp.)",
                                f"{tasa_agen_vs_resp_global}%")


def display_grouped_breakdown(df_filtered,
                              group_by_col,
                              title_prefix,
                              chart_icon="📊"):
    st.markdown(f"### {chart_icon} {title_prefix} - KPIs Absolutos y Tasas")
    if group_by_col not in df_filtered.columns:
        st.warning(f"Columna '{group_by_col}' no encontrada.")
        return

    kpi_cols = [
        "Mensajes Enviados", "Respuestas", "Invites enviadas",
        "Sesiones agendadas"
    ]
    rate_col_names = {
        'tasa_resp': 'Tasa Respuesta (%)',
        'tasa_ag_env': 'Tasa Ag. (vs Env.) (%)',
        'tasa_ag_resp': 'Tasa Ag. (vs Resp.) (%)'
    }
    actual_kpi_cols = [
        col for col in kpi_cols if col in df_filtered.columns
        and pd.api.types.is_numeric_dtype(df_filtered[col])
    ]  # Asegurar que sean numéricas
    if not actual_kpi_cols:
        st.warning(
            f"No hay columnas de KPI numéricas para desglose por {group_by_col}."
        )
        return

    df_to_group = df_filtered.copy()
    if df_to_group[group_by_col].isnull().any() or (
            df_to_group[group_by_col].astype(str).str.strip() == "").any():
        df_to_group[group_by_col] = df_to_group[group_by_col].astype(
            str).str.strip().replace('', 'N/D')

    if df_to_group.empty or df_to_group[group_by_col].nunique() == 0:
        st.info(
            f"No hay datos con '{group_by_col}' definido para el desglose en el periodo filtrado."
        )
        return

    summary_df = df_to_group.groupby(group_by_col,
                                     as_index=False)[actual_kpi_cols].sum()

    # Calcular tasas
    mensajes_col, respuestas_col, sesiones_col = "Mensajes Enviados", "Respuestas", "Sesiones agendadas"
    summary_df[rate_col_names['tasa_resp']] = summary_df.apply(
        lambda r: calculate_rate(r.get(respuestas_col, 0),
                                 r.get(mensajes_col, 0)),
        axis=1
    ) if mensajes_col in summary_df and respuestas_col in summary_df else 0.0
    summary_df[rate_col_names['tasa_ag_env']] = summary_df.apply(
        lambda r: calculate_rate(r.get(sesiones_col, 0), r.get(
            mensajes_col, 0)),
        axis=1
    ) if mensajes_col in summary_df and sesiones_col in summary_df else 0.0
    summary_df[rate_col_names['tasa_ag_resp']] = summary_df.apply(
        lambda r: calculate_rate(r.get(sesiones_col, 0),
                                 r.get(respuestas_col, 0)),
        axis=1
    ) if respuestas_col in summary_df and sesiones_col in summary_df else 0.0

    if not summary_df.empty:
        cols_for_display_table = [group_by_col] + actual_kpi_cols + list(
            rate_col_names.values())
        summary_df_display = summary_df[cols_for_display_table].copy()
        for kpi_col in actual_kpi_cols:
            summary_df_display[kpi_col] = summary_df_display[kpi_col].map(
                '{:,}'.format)
        for rate_col_key in rate_col_names:
            summary_df_display[
                rate_col_names[rate_col_key]] = summary_df_display[
                    rate_col_names[rate_col_key]].map('{:.1f}%'.format)

        st.markdown("##### Tabla Resumen (Absolutos y Tasas)")
        st.dataframe(summary_df_display, use_container_width=True)
        st.markdown("---")

        if sesiones_col in summary_df.columns and summary_df[sesiones_col].sum(
        ) > 0:
            st.markdown("##### Gráfico: Sesiones Agendadas (Absoluto)")
            fig_abs = px.bar(summary_df,
                             x=group_by_col,
                             y=sesiones_col,
                             title=f"Sesiones Agendadas por {group_by_col}",
                             color=sesiones_col,
                             text=summary_df[sesiones_col],
                             color_continuous_scale=px.colors.sequential.Teal)
            fig_abs.update_traces(textposition='outside',
                                  texttemplate='%{text:,}')
            fig_abs.update_layout(title_x=0.5,
                                  xaxis_tickangle=-45,
                                  yaxis_title="Total Sesiones Agendadas",
                                  xaxis_title=group_by_col,
                                  margin=dict(b=150))
            st.plotly_chart(fig_abs, use_container_width=True)

        rate_to_plot = rate_col_names['tasa_ag_resp']
        if rate_to_plot in summary_df.columns and summary_df[rate_to_plot].sum(
        ) > 0:
            st.markdown(f"##### Gráfico: {rate_to_plot}")
            summary_df_sorted_rate = summary_df.sort_values(by=rate_to_plot,
                                                            ascending=False)
            fig_rate = px.bar(
                summary_df_sorted_rate,
                x=group_by_col,
                y=rate_to_plot,
                title=f"{rate_to_plot} por {group_by_col}",
                color=rate_to_plot,
                text=summary_df_sorted_rate[rate_to_plot].map(
                    '{:.1f}'.format),  # Solo el número, el % se añade al eje
                color_continuous_scale=px.colors.sequential.Mint)
            fig_rate.update_traces(textposition='outside')
            fig_rate.update_layout(title_x=0.5,
                                   xaxis_tickangle=-45,
                                   yaxis_title=rate_to_plot,
                                   xaxis_title=group_by_col,
                                   margin=dict(b=150),
                                   yaxis_ticksuffix="%")
            st.plotly_chart(fig_rate, use_container_width=True)


def display_time_evolution(df_filtered,
                           time_col_agg,
                           time_col_label,
                           chart_title,
                           x_axis_label,
                           chart_icon="📈"):
    st.markdown(f"### {chart_icon} {chart_title}")
    st.caption(
        f"KPIs sumados por {x_axis_label.lower()} dentro del período filtrado."
    )
    required_cols = ['Fecha', time_col_agg]
    if 'NumSemana' in time_col_agg: required_cols.extend(['Año', 'NumSemana'])
    if 'AñoMes' in time_col_agg:
        required_cols.extend(['Año', 'MesNum', 'AñoMes'])
    cols_missing = [
        col for col in list(set(required_cols))
        if col not in df_filtered.columns
    ]
    fecha_col = df_filtered.get(
        'Fecha', pd.Series(dtype='object'))  # Usar .get para seguridad
    if cols_missing or not pd.api.types.is_datetime64_any_dtype(fecha_col):
        st.info(
            f"Datos insuficientes (faltan: {', '.join(cols_missing)}) o en formato incorrecto para {chart_title.lower()}."
        )
        return
    if df_filtered.empty:
        st.info(f"No hay datos filtrados para {chart_title.lower()}.")
        return
    kpi_cols_to_sum = [
        "Mensajes Enviados", "Respuestas", "Invites enviadas",
        "Sesiones agendadas"
    ]
    kpi_cols_present = [
        col for col in kpi_cols_to_sum if col in df_filtered.columns
        and pd.api.types.is_numeric_dtype(df_filtered[col])
    ]
    if not kpi_cols_present:
        st.info(
            f"No hay columnas de KPI numéricas para la agregación por {x_axis_label.lower()}."
        )
        return
    group_by_cols = [time_col_agg]
    if time_col_agg == 'NumSemana': group_by_cols = ['Año', 'NumSemana']
    df_agg = df_filtered.groupby(group_by_cols,
                                 as_index=False)[kpi_cols_present].sum()
    if df_agg.empty:
        st.info(
            f"No hay datos agregados para mostrar la evolución por {x_axis_label.lower()}."
        )
        return

    # Construir etiqueta para el eje X
    if time_col_agg == 'NumSemana':
        df_agg = df_agg.sort_values(by=['Año', 'NumSemana'])
        df_agg[time_col_label] = df_agg['Año'].astype(
            str) + '-S' + df_agg['NumSemana'].astype(str).str.zfill(2)
    elif time_col_agg == 'AñoMes':
        df_agg = df_agg.sort_values(by=['AñoMes'])
        # time_col_label ya es 'AñoMes'

    # Verificar si time_col_label se creó correctamente
    if time_col_label not in df_agg.columns and (time_col_agg == 'NumSemana'
                                                 or time_col_agg == 'AñoMes'):
        st.error(
            f"No se pudo crear la columna de etiqueta temporal '{time_col_label}'. Revise la lógica de agregación."
        )
        return

    df_display = df_agg[[time_col_label] + kpi_cols_present].copy()
    for kpi_col in kpi_cols_present:
        df_display[kpi_col] = df_display[kpi_col].map('{:,}'.format)
    st.dataframe(df_display, use_container_width=True)

    sesiones_col = "Sesiones agendadas"
    if sesiones_col in df_agg.columns and df_agg[sesiones_col].sum() > 0:
        fig = px.line(
            df_agg,
            x=time_col_label,
            y=sesiones_col,
            title=f"Evolución de Sesiones Agendadas por {x_axis_label}",
            labels={
                time_col_label: x_axis_label,
                sesiones_col: 'Total Sesiones'
            },
            markers=True,
            text=sesiones_col)
        fig.update_traces(textposition='top center', texttemplate='%{text:,}')
        fig.update_xaxes(type='category', tickangle=-45)
        fig.update_layout(title_x=0.5, margin=dict(b=120))
        st.plotly_chart(fig, use_container_width=True)


# --- Flujo Principal de la Página ---
start_date_val, end_date_val, year_val, week_val, analista_val, region_val = sidebar_filters(
    df_kpis_semanales_raw)

df_kpis_filtered = apply_kpis_filters(df_kpis_semanales_raw, start_date_val,
                                      end_date_val, year_val, week_val,
                                      analista_val, region_val)

if "Analista" in df_kpis_filtered.columns and analista_val and "– Todos –" not in analista_val:
    if "N/D" not in analista_val:
        df_kpis_filtered = df_kpis_filtered[~df_kpis_filtered["Analista"].
                                            isin(['N/D', ''])]

# --- Presentación del Dashboard ---
display_kpi_summary(df_kpis_filtered)
st.markdown("---")
col_breakdown1, col_breakdown2 = st.columns(2)
with col_breakdown1:
    display_grouped_breakdown(df_kpis_filtered,
                              "Analista",
                              "Desglose por Analista",
                              chart_icon="🧑‍💻")
with col_breakdown2:
    display_grouped_breakdown(df_kpis_filtered,
                              "Región",
                              "Desglose por Región",
                              chart_icon="🌎")
st.markdown("---")
display_filtered_kpis_table(df_kpis_filtered)
st.markdown("---")
display_time_evolution(df_kpis_filtered,
                       'NumSemana',
                       'Año-Semana',
                       "Evolución Semanal de KPIs",
                       "Semana",
                       chart_icon="🗓️")
st.markdown("---")
display_time_evolution(df_kpis_filtered,
                       'AñoMes',
                       'AñoMes',
                       "Evolución Mensual de KPIs",
                       "Mes (Año-Mes)",
                       chart_icon="📈")

# --- PIE DE PÁGINA ---
st.markdown("---")
st.info(
    "Esta maravillosa, caótica y probablemente sobrecafeinada plataforma ha sido realizada por Johnsito ✨ 😊"
)
