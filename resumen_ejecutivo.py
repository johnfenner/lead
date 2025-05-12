# componentes/resumen_ejecutivo.py

import streamlit as st
import pandas as pd
from utils.limpieza import limpiar_valor_kpi  # Asegúrate de que esta función se importe


# La firma de la función modificada para aceptar los conteos base
def mostrar_resumen_ejecutivo(df_kpis, limpiar_valor_kpi, base_kpis_counts,
                              sesiones_filtered):
    st.markdown("---")
    st.markdown("## 📝 Resumen Ejecutivo")

    # total_filtered es la cantidad de filas después de todos los filtros de la barra lateral
    total_filtered = len(df_kpis)

    # Obtenemos los conteos para el conjunto filtrado
    inv_acept_filtered = 0
    if "¿Invite Aceptada?" in df_kpis.columns:
        inv_acept_filtered = sum(
            limpiar_valor_kpi(x) == "si" for x in df_kpis["¿Invite Aceptada?"])

    primeros_mensajes_enviados_count_filtered = 0
    if "Fecha Primer Mensaje" in df_kpis.columns:
        primeros_mensajes_enviados_count_filtered = sum(
            limpiar_valor_kpi(x) not in ["no", "", "nan"]
            for x in df_kpis["Fecha Primer Mensaje"])

    resp_primer_filtered = 0
    if "Respuesta Primer Mensaje" in df_kpis.columns:
        resp_primer_filtered = sum(
            limpiar_valor_kpi(x) not in ["no", "", "nan"]
            for x in df_kpis["Respuesta Primer Mensaje"])

    # Usamos el conteo de sesiones filtrado que se pasó como argumento
    sesiones = sesiones_filtered

    # Obtenemos los conteos de la base completa
    base_total = base_kpis_counts["total_base"]
    base_inv_acept = base_kpis_counts["inv_acept"]
    base_primeros_mensajes_enviados_count = base_kpis_counts[
        "primeros_mensajes_enviados_count"]
    base_resp_primer = base_kpis_counts["resp_primer"]
    base_sesiones = base_kpis_counts["sesiones"]

    # --- Calculamos Tasas de Conversión ---

    # Tasas del conjunto FILTRADO (vs etapa anterior del conjunto FILTRADO)
    # La tasa de aceptación filtrada vs la base total sigue siendo útil
    tasa_aceptacion_filtrado_vs_base_total = (inv_acept_filtered / base_total *
                                              100) if base_total > 0 else 0
    tasa_respuesta_filtrado_vs_aceptados_filtrado = (
        resp_primer_filtered / inv_acept_filtered *
        100) if inv_acept_filtered > 0 else 0
    tasa_sesion_filtrado_vs_respuestas_filtrado = (
        sesiones / resp_primer_filtered *
        100) if resp_primer_filtered > 0 else 0

    # Tasas del conjunto BASE (vs etapa anterior del conjunto BASE)
    tasa_aceptacion_base = (base_inv_acept / base_total *
                            100) if base_total > 0 else 0
    tasa_respuesta_base = (base_resp_primer / base_inv_acept *
                           100) if base_inv_acept > 0 else 0
    tasa_sesion_base = (base_sesiones / base_resp_primer *
                        100) if base_resp_primer > 0 else 0

    # ... (dentro de mostrar_resumen_ejecutivo, después de los análisis de pérdidas) ...

    # Insight Accionable (ejemplo conceptual, necesitaría datos de análisis de avatares/industrias)
    # Para esto, necesitarías pasarle los resultados de los análisis de top_dimension o avatar,
    # o recalcular aquí una versión simplificada.

    # Ejemplo simplificado:
    if not df_kpis.empty and "Industria" in df_kpis.columns and "Sesion Agendada?" in df_kpis.columns:
        # Este es un cálculo similar al de mostrar_analisis_dimension_agendamiento
        # Deberías refactorizar para no duplicar lógica.
        # O idealmente, la función de análisis de dimensión retorna su top resultado y lo usas aquí.
        try:
            resumen_industria = df_kpis.groupby("Industria").agg(
                Total_Prospectados=("Industria", 'count'),
                Sesiones_Agendadas=(
                    "Sesion Agendada?", lambda x:
                    (x.apply(limpiar_valor_kpi) == "si").sum())).reset_index()
            resumen_industria["Tasa Agendamiento (%)"] = (
                (resumen_industria["Sesiones_Agendadas"] /
                 resumen_industria["Total_Prospectados"]) * 100).fillna(0)
            top_industria_agenda = resumen_industria[
                resumen_industria["Total_Prospectados"] >= 5].sort_values(
                    by="Tasa Agendamiento (%)", ascending=False).head(1)

            if not top_industria_agenda.empty:
                nombre_top_industria = top_industria_agenda.iloc[0][
                    "Industria"]
                tasa_top_industria = top_industria_agenda.iloc[0][
                    "Tasa Agendamiento (%)"]
                st.markdown(
                    f"💡 **Insight Rápido:** La industria **{nombre_top_industria}** está mostrando una alta tasa de agendamiento del **{tasa_top_industria:.1f}%**. ¡Considera enfocar esfuerzos allí!"
                )
        except Exception:
            pass  # Evitar que el dashboard se rompa si hay algún problema con este cálculo rápido
    # --- Mostramos el Resumen basado en si hay filtros aplicados ---

    if total_filtered > 0:  # Asegurarse de que haya datos en el conjunto filtrado
        st.markdown("### 📈 Indicadores Clave (Conjunto Filtrado)")
        col1, col2, col3 = st.columns(3)

        # Mostrar las tasas del conjunto filtrado
        with col1:
            st.metric("Tasa Aceptación ✅",
                      f"{tasa_aceptacion_filtrado_vs_base_total:.1f}%",
                      help=f"Vs Base Total ({base_total})")
        with col2:
            st.metric("Tasa Respuesta 💬",
                      f"{tasa_respuesta_filtrado_vs_aceptados_filtrado:.1f}%",
                      help=f"Vs Invites Aceptadas ({inv_acept_filtered})")
        with col3:
            st.metric("Tasa Sesión 🗓️",
                      f"{tasa_sesion_filtrado_vs_respuestas_filtrado:.1f}%",
                      help=f"Vs Respuestas 1er Msj  ({resp_primer_filtered})")

        st.markdown("### 🧠 Análisis de Conversión (Conjunto Filtrado)")
        st.markdown(f"""
        Analizando los **{total_filtered}** prospectos:
        - De los **{base_total}** prospectos base, **{inv_acept_filtered}** aceptaron la invitación  (**{tasa_aceptacion_filtrado_vs_base_total:.1f}%** de la base total).
        - De los aceptados, **{resp_primer_filtered}** respondieron (**{tasa_respuesta_filtrado_vs_aceptados_filtrado:.1f}%** de los aceptados).
        - Y finalmente, de los que respondieron, **{sesiones}** agendaron una sesión (**{tasa_sesion_filtrado_vs_respuestas_filtrado:.1f}%** de los que respondieron).
        """)

        st.markdown("### 🔎 Pérdidas Entre Etapas (Conjunto Filtrado)")
        st.markdown(f"""
        - ❌ Aproximadamente **{100 - tasa_aceptacion_filtrado_vs_base_total:.1f}%** de la base total no llega a ser un aceptado.
        - ❌ Aproximadamente **{100 - tasa_respuesta_filtrado_vs_aceptados_filtrado:.1f}%** de los aceptados no responden.
        - ❌ Aproximadamente **{100 - tasa_sesion_filtrado_vs_respuestas_filtrado:.1f}%** de los que respondieron no agendan.
        """)

        # Opcional: Añadir una pequeña referencia a las tasas base si se está filtrando
        if total_filtered != base_total:
            st.markdown("---")
            st.markdown(
                f"Comparativa Base Completa ({base_total} prospectos):")
            st.caption(
                f"Tasa Aceptación Base: {tasa_aceptacion_base:.1f}% | Tasa Respuesta Base: {tasa_respuesta_base:.1f}% | Tasa Sesión Base: {tasa_sesion_base:.1f}%"
            )

    elif base_total > 0:  # Mostrar el resumen de la base si no hay filtros y la base tiene datos
        st.markdown("### 📈 Indicadores Clave (Base Completa)")
        col1, col2, col3 = st.columns(3)

        # Mostrar las tasas de la base completa
        with col1:
            st.metric("Tasa Aceptación ✅",
                      f"{tasa_aceptacion_base:.1f}%",
                      help=f"Vs Base Total ({base_total})")
        with col2:
            st.metric("Tasa Respuesta 💬",
                      f"{tasa_respuesta_base:.1f}%",
                      help=f"Vs Invites Aceptadas Base ({base_inv_acept})")
        with col3:
            st.metric("Tasa Sesión 🗓️",
                      f"{tasa_sesion_base:.1f}%",
                      help=f"Vs Respuestas 1er Msj Base ({base_resp_primer})")

        st.markdown("### 🧠 Análisis de Conversión (Base Completa)")
        st.markdown(f"""
        Analizando los **{base_total}** prospectos base:
        - De los **{base_total}** prospectos base, **{base_inv_acept}** aceptaron la invitación (**{tasa_aceptacion_base:.1f}%**).
        - De los aceptados (base), **{base_resp_primer}** respondieron (**{tasa_respuesta_base:.1f}%**).
        - Y finalmente, de los que respondieron (base), **{base_sesiones}** agendaron una sesión (**{tasa_sesion_base:.1f}%**).
        """)

        st.markdown("### 🔎 Pérdidas Entre Etapas (Base Completa)")
        st.markdown(f"""
        - ❌ Se pierde aproximadamente **{100 - tasa_aceptacion_base:.1f}%** de la base a aceptados base.
        - ❌ Se pierde aproximadamente **{100 - tasa_respuesta_base:.1f}%** de aceptados base que no responden.
        - ❌ Se pierde aproximadamente **{100 - tasa_sesion_base:.1f}%** de los que respondieron base que no agendan.
        """)

    else:  # Si ni los datos filtrados ni la base tienen datos
        st.info(
            "⚠️ No hay datos suficientes para generar el resumen ejecutivo en el conjunto filtrado ni en la base completa."
        )
