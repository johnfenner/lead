# Proyecto/🏠_Dashboard_Principal.py

import streamlit as st
import pandas as pd
import sys
import os

# Añadir la raíz del proyecto al path para poder importar módulos
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- IMPORTS MODULARES ---
from datos.carga_datos import cargar_y_limpiar_datos, cargar_y_procesar_datos
from filtros.filtros_sidebar import mostrar_filtros_sidebar
from filtros.aplicar_filtros import aplicar_filtros
from componentes.tabla_prospectos import mostrar_tabla_filtrada
from componentes.indicadores_kpis import mostrar_kpis
from componentes.embudo_conversion import mostrar_embudo
from componentes.resumen_ejecutivo import mostrar_resumen_ejecutivo
from componentes.top_industrias_paises import mostrar_analisis_dimension_agendamiento_flexible
from componentes.analisis_procesos import mostrar_analisis_procesos_con_prospectador
from componentes.analisis_avatars import mostrar_analisis_por_avatar
from componentes.oportunidades_calientes import mostrar_oportunidades_calientes

from utils.limpieza import limpiar_valor_kpi

# --- CONFIGURACIÓN GENERAL ---
st.set_page_config(page_title="Dashboard Prospección Lead Generation",
                   layout="wide")
st.title("📈 Dashboard — Lead Generation")  # Texto original del título

# --- INYECTAR CSS PARA AJUSTAR ANCHO DEL SIDEBAR ---
st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] {
        width: 380px !important;
    }
    section[data-testid="stSidebar"] .stSidebarContent {
        padding-top: 20px;
        padding-left: 20px;
        padding-right: 20px;
    }
    .highlight-rate { /* Si usas esta clase en kpis.py */
        font-size: 1.1em;
        font-weight: bold;
        color: #28a745;
        display: block;
        margin-top: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- CUSTOM SIDEBAR CONTENT ---
SIDEBAR_IMAGE_PATH = os.path.join(project_root,
                                  "logo.jpeg")  # Verifica esta ruta
try:
    st.sidebar.image(SIDEBAR_IMAGE_PATH, width=150)
except FileNotFoundError:
    st.sidebar.warning(
        "⚠️ Logo no encontrado. Verifica la ruta en `🏠_Dashboard_Principal.py`."
    )
except Exception as e:
    st.sidebar.warning(f"⚠️ Error al cargar el logo: {e}")

st.sidebar.markdown("""
**Plataforma de Análisis de Prospección**:
Explora métricas clave y gestiona tus leads.
""")  # Texto original de la sidebar


# --- CARGA Y FILTRADO BASE ---
@st.cache_data
def get_processed_data():
    df_base_loaded = cargar_y_limpiar_datos()
    if df_base_loaded is None or df_base_loaded.empty:
        return pd.DataFrame()
    df_processed_loaded = cargar_y_procesar_datos(df_base_loaded.copy())
    return df_processed_loaded


df_global = get_processed_data()

if df_global.empty:
    st.error(
        "No se pudieron cargar los datos base o están vacíos. El dashboard no puede continuar."
    )
    st.stop()

# --- CÁLCULO DE MÉTRICAS BASE (ANTES DE FILTROS DE SIDEBAR) ---
total_base = len(df_global)
base_inv_acept = 0
if "¿Invite Aceptada?" in df_global.columns:
    base_inv_acept = sum(
        limpiar_valor_kpi(x) == "si" for x in df_global["¿Invite Aceptada?"])

base_primeros_mensajes_enviados_count = 0
if "Fecha Primer Mensaje" in df_global.columns:
    base_primeros_mensajes_enviados_count = sum(
        pd.notna(x) and str(x).strip().lower() not in ["no", "", "nan"]
        for x in df_global["Fecha Primer Mensaje"])

base_resp_primer = 0
if "Respuesta Primer Mensaje" in df_global.columns:
    base_resp_primer = sum(
        limpiar_valor_kpi(x) not in ["no", "", "nan"]
        for x in df_global["Respuesta Primer Mensaje"])

base_sesiones = 0
if "Sesion Agendada?" in df_global.columns:
    base_sesiones = sum(
        limpiar_valor_kpi(x) == "si" for x in df_global["Sesion Agendada?"])

base_kpis_counts = {
    "total_base": total_base,
    "inv_acept": base_inv_acept,
    "primeros_mensajes_enviados_count": base_primeros_mensajes_enviados_count,
    "resp_primer": base_resp_primer,
    "sesiones": base_sesiones
}

# --- FILTROS SIDEBAR ---
(filtro_fuente_lista, filtro_proceso, filtro_pais, filtro_industria,
 filtro_avatar, filtro_prospectador, filtro_invite_aceptada_simple,
 filtro_sesion_agendada, fecha_ini, fecha_fin,
 busqueda_texto) = mostrar_filtros_sidebar(df_global.copy())

# --- APLICACIÓN DE FILTROS (de la barra lateral) ---
df_filtrado_sidebar = aplicar_filtros(
    df_global.copy(), filtro_fuente_lista, filtro_proceso, filtro_pais,
    filtro_industria, filtro_avatar, filtro_prospectador,
    filtro_invite_aceptada_simple, filtro_sesion_agendada, fecha_ini,
    fecha_fin)

# --- DataFrame para KPIs y Análisis (df_kpis) ---
df_kpis = df_filtrado_sidebar.copy()

# --- DataFrame para la Tabla Detallada (df_tabla_detalle) ---
df_tabla_detalle = df_filtrado_sidebar.copy()
if busqueda_texto:
    busq_term = busqueda_texto.lower().strip()
    if busq_term:
        mask = pd.Series([False] * len(df_tabla_detalle),
                         index=df_tabla_detalle.index)
        columnas_busqueda_texto_config = ["Empresa", "Puesto"]

        nombre_col_presente = "Nombre" in df_tabla_detalle.columns
        apellido_col_presente = "Apellido" in df_tabla_detalle.columns

        if nombre_col_presente and apellido_col_presente:
            df_tabla_detalle["_NombreCompleto_temp_search"] = (
                df_tabla_detalle["Nombre"].fillna('').astype(str) + ' ' +
                df_tabla_detalle["Apellido"].fillna('').astype(str)
            ).str.lower()
            mask |= df_tabla_detalle[
                "_NombreCompleto_temp_search"].str.contains(busq_term,
                                                            na=False)
            df_tabla_detalle.drop(columns=["_NombreCompleto_temp_search"],
                                  inplace=True)
        elif nombre_col_presente:
            mask |= df_tabla_detalle["Nombre"].astype(
                str).str.lower().str.contains(busq_term, na=False)
        elif apellido_col_presente:
            mask |= df_tabla_detalle["Apellido"].astype(
                str).str.lower().str.contains(busq_term, na=False)

        for col in columnas_busqueda_texto_config:
            if col in df_tabla_detalle.columns:
                mask |= df_tabla_detalle[col].astype(
                    str).str.lower().str.contains(busq_term, na=False)

        df_tabla_detalle = df_tabla_detalle[mask]

# --- ORDEN DE LOS COMPONENTES EN EL DASHBOARD ---

# 1. OPORTUNIDADES CLAVE PARA AGENDAR
mostrar_oportunidades_calientes(df_kpis)

st.header("🔍 Detalle y Rendimiento General")  # Título de sección enfocado
# 2. TABLA DE PROSPECTOS (Resultado de filtros sidebar + búsqueda de texto)
mostrar_tabla_filtrada(df_tabla_detalle)

# 3. INDICADORES CLAVE DE RENDIMIENTO (KPIs)
(filtered_total, filtered_primeros_mensajes_enviados_count, filtered_inv_acept,
 filtered_resp_primer, filtered_sesiones,
 _) = mostrar_kpis(df_kpis, base_kpis_counts, limpiar_valor_kpi)

# 4. EMBUDO DE CONVERSIÓN
mostrar_embudo(filtered_total, filtered_inv_acept, filtered_resp_primer,
               filtered_sesiones, filtered_primeros_mensajes_enviados_count,
               base_kpis_counts["total_base"], base_kpis_counts["inv_acept"],
               base_kpis_counts["primeros_mensajes_enviados_count"],
               base_kpis_counts["resp_primer"], base_kpis_counts["sesiones"])

st.header("💡 ¿Dónde Enfocar tus Esfuerzos de Prospección?"
          )  # Título de sección enfocado
# 5. ANÁLISIS DE DIMENSIONES
# Industrias: Solo Gráfico Top 10
if "Industria" in df_kpis.columns:
    mostrar_analisis_dimension_agendamiento_flexible(
        df_kpis,
        "Industria",
        "Industrias",
        top_n_grafico=10,
        mostrar_tabla_completa=False)
else:
    st.caption("Columna 'Industria' no encontrada para análisis.")

# Países: Gráfico Top 10 + Tabla Completa Paginada
if "Pais" in df_kpis.columns:
    mostrar_analisis_dimension_agendamiento_flexible(
        df_kpis,
        "Pais",
        "Países",
        top_n_grafico=10,
        mostrar_tabla_completa=True)
else:
    st.caption("Columna 'Pais' no encontrada para análisis.")

# Puestos: Solo Gráfico Top 10
if "Puesto" in df_kpis.columns:
    mostrar_analisis_dimension_agendamiento_flexible(
        df_kpis,
        "Puesto",
        "Puestos",
        top_n_grafico=10,
        mostrar_tabla_completa=False)
else:
    st.caption("Columna 'Puesto' no encontrada para análisis.")

# 6. ANÁLISIS DE PROCESOS (NUEVO)
if "Proceso" in df_kpis.columns:
    mostrar_analisis_procesos_con_prospectador(df_kpis,
                                               top_n_grafico_proceso=10,
                                               mostrar_tabla_proceso=True)
else:
    st.caption("Columna 'Proceso' no encontrada para análisis de procesos.")

# 7. ANÁLISIS DE RENDIMIENTO POR AVATAR (Enfoque Agendamiento)
mostrar_analisis_por_avatar(df_kpis)

# 8. RESUMEN EJECUTIVO
mostrar_resumen_ejecutivo(df_kpis, limpiar_valor_kpi, base_kpis_counts,
                          filtered_sesiones)

# --- PIE DE PÁGINA ---
st.markdown("---")
st.info(
    "Esta maravillosa, caótica y probablemente sobrecafeinada plataforma ha sido realizada por Johnsito ✨ 😊 '."
)  # Texto original del pie de página
