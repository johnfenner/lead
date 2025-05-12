import streamlit as st
import pandas as pd
from utils.limpieza import limpiar_valor_kpi


def mostrar_kpis(df_kpis, base_kpis_counts, limpiar_valor_kpi):
    st.markdown("---")
    st.markdown("## 📊 Indicadores Clave de Rendimiento (KPIs)")

    total_filtered = len(df_kpis)
    base_total = base_kpis_counts["total_base"]

    inv_acept = 0
    if "¿Invite Aceptada?" in df_kpis.columns:
        inv_acept = sum(
            limpiar_valor_kpi(x) == "si" for x in df_kpis["¿Invite Aceptada?"])

    primeros_mensajes_enviados_count = 0
    if "Fecha Primer Mensaje" in df_kpis.columns:
        primeros_mensajes_enviados_count = sum(
            limpiar_valor_kpi(x) not in ["no", "", "nan"]
            for x in df_kpis["Fecha Primer Mensaje"])

    resp_primer = 0
    if "Respuesta Primer Mensaje" in df_kpis.columns:
        resp_primer = sum(
            limpiar_valor_kpi(x) not in ["no", "", "nan"]
            for x in df_kpis["Respuesta Primer Mensaje"])

    sesiones = 0
    if "Sesion Agendada?" in df_kpis.columns:
        sesiones = sum(
            limpiar_valor_kpi(x) == "si" for x in df_kpis["Sesion Agendada?"])

    # Nuevo KPI: Oportunidades para Agendar
    oportunidades_para_agendar = 0
    if all(
            col in df_kpis.columns for col in
        ["¿Invite Aceptada?", "Respuesta Primer Mensaje", "Sesion Agendada?"]):
        oportunidades_para_agendar = len(df_kpis[
            (df_kpis["¿Invite Aceptada?"].apply(limpiar_valor_kpi) == "si")
            & (df_kpis["Respuesta Primer Mensaje"].apply(
                lambda x: limpiar_valor_kpi(x) not in ["no", "", "nan"])) &
            (df_kpis["Sesion Agendada?"].apply(limpiar_valor_kpi) == "no")])

    # Tasas del conjunto FILTRADO
    tasa_aceptacion_filtrado_vs_base = (inv_acept / base_total *
                                        100) if base_total > 0 else 0
    tasa_respuesta_filtrado_vs_aceptados_filtrado = (
        resp_primer / inv_acept * 100) if inv_acept > 0 else 0
    tasa_sesion_filtrado_vs_respuestas_filtrado = (
        sesiones / resp_primer * 100) if resp_primer > 0 else 0
    tasa_sesion_filtrado_vs_aceptados_filtrado = (
        sesiones / inv_acept * 100) if inv_acept > 0 else 0  # Nueva tasa

    # Conteos base
    base_inv_acept_count = base_kpis_counts["inv_acept"]
    base_primeros_mensajes_enviados_count = base_kpis_counts[
        "primeros_mensajes_enviados_count"]
    base_resp_primer_count = base_kpis_counts["resp_primer"]
    base_sesiones_count = base_kpis_counts["sesiones"]

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Prospectos (Filtro)",
            total_filtered,
            help=
            f"Total de prospectos que cumplen los filtros. Base total: {base_total}."
        )
    with col2:
        st.metric(
            "Invites Aceptadas ✅",
            inv_acept,
            help=
            f"Prospectos (filtrados) que aceptaron. Base: {base_inv_acept_count}."
        )
        st.caption(f"{tasa_aceptacion_filtrado_vs_base:.1f}% de la Base Total")
    with col3:
        st.metric(
            "Respuestas 1er Msj 💬",
            resp_primer,
            help=
            f"Prospectos (filtrados) que respondieron. Base: {base_resp_primer_count}."
        )
        st.caption(
            f"{tasa_respuesta_filtrado_vs_aceptados_filtrado:.1f}% de Aceptadas (Filtro)"
        )
    with col4:
        st.metric(
            "Sesiones Agendadas 🗓️",
            sesiones,
            help=
            f"Prospectos (filtrados) con sesión. Base: {base_sesiones_count}.")
        # Destacar estas tasas
        st.markdown(
            f"**{tasa_sesion_filtrado_vs_respuestas_filtrado:.1f}%** de Respuestas (Filtro)"
        )
        st.caption(
            f"({tasa_sesion_filtrado_vs_aceptados_filtrado:.1f}% de Aceptadas (Filtro))"
        )

    with col5:
        st.metric(
            "🔥 Oportunidades Agendar",  # Nuevo KPI
            oportunidades_para_agendar,
            help="Aceptaron y Respondieron, pero SIN sesión agendada (Filtro)."
        )
        # Podrías añadir un delta si este número sube o baja mucho respecto a un periodo anterior

    return (
        total_filtered,
        primeros_mensajes_enviados_count,  # Se mantiene por si se usa en el embudo
        inv_acept,
        resp_primer,
        sesiones,
        base_kpis_counts  # Retornamos los conteos base también
    )
