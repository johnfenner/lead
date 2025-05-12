# componentes/analisis_avatars.py
import streamlit as st
from utils.limpieza import limpiar_valor_kpi, estandarizar_avatar
import pandas as pd
import plotly.express as px


def mostrar_analisis_por_avatar(
        df):  # df aquí es df_kpis (ya filtrado por sidebar)
    st.markdown("---")
    st.markdown(
        "### 👤 Análisis de Rendimiento por Avatar (Enfoque Agendamiento)")

    # Columnas requeridas para el análisis completo
    required_cols = [
        "Avatar", "¿Invite Aceptada?", "Respuesta Primer Mensaje",
        "Sesion Agendada?"
    ]
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        st.warning(
            f"Faltan columnas necesarias para el análisis de Avatar: {', '.join(missing)}."
        )
        return

    df_analisis = df.copy()
    df_analisis["Avatar"] = df_analisis["Avatar"].apply(estandarizar_avatar)

    resumen_avatar = df_analisis.groupby("Avatar").agg(
        Prospectados=("Avatar", "count"),
        Invites_Aceptadas=("¿Invite Aceptada?", lambda col:
                           (col.apply(limpiar_valor_kpi) == "si").sum()),
        Respuestas_1er_Msj=("Respuesta Primer Mensaje", lambda col: (col.apply(
            lambda x: limpiar_valor_kpi(x) not in ["no", "", "nan"])).sum()),
        Sesiones_Agendadas=(
            "Sesion Agendada?", lambda col:
            (col.apply(limpiar_valor_kpi) == "si").sum())).reset_index()

    # Calcular Tasas Clave para Agendamiento
    resumen_avatar["Tasa Aceptación (%)"] = (
        resumen_avatar["Invites_Aceptadas"] / resumen_avatar["Prospectados"] *
        100).round(1).fillna(0)
    resumen_avatar["Tasa Respuesta (vs Acept.) (%)"] = (
        resumen_avatar["Respuestas_1er_Msj"] /
        resumen_avatar["Invites_Aceptadas"] * 100).round(1).fillna(0)
    resumen_avatar["Tasa Sesiones (vs Resp.) (%)"] = (
        resumen_avatar["Sesiones_Agendadas"] /
        resumen_avatar["Respuestas_1er_Msj"] * 100).round(1).fillna(0)
    resumen_avatar["Tasa Sesiones Global (vs Prosp.) (%)"] = (
        resumen_avatar["Sesiones_Agendadas"] / resumen_avatar["Prospectados"] *
        100).round(1).fillna(0)

    # Reemplazar Inf con 0 si alguna división fue por cero y no se manejó con fillna antes
    resumen_avatar.replace([float('inf'), -float('inf')], 0, inplace=True)

    if resumen_avatar.empty:
        st.info(
            "No hay datos de Avatar para analizar con los filtros actuales.")
        return

    st.markdown("#### Tabla de Rendimiento por Avatar:")
    st.dataframe(resumen_avatar[[
        "Avatar", "Prospectados", "Invites_Aceptadas", "Respuestas_1er_Msj",
        "Sesiones_Agendadas", "Tasa Aceptación (%)",
        "Tasa Respuesta (vs Acept.) (%)", "Tasa Sesiones (vs Resp.) (%)",
        "Tasa Sesiones Global (vs Prosp.) (%)"
    ]].style.format({
        "Tasa Aceptación (%)": "{:.1f}%",
        "Tasa Respuesta (vs Acept.) (%)": "{:.1f}%",
        "Tasa Sesiones (vs Resp.) (%)": "{:.1f}%",
        "Tasa Sesiones Global (vs Prosp.) (%)": "{:.1f}%"
    }),
                 use_container_width=True)

    # Gráfico de Tasa de Sesiones (vs Respuestas)
    if not resumen_avatar[
            resumen_avatar["Respuestas_1er_Msj"] >
            0].empty:  # Solo graficar si hay respuestas para calcular la tasa
        fig_tasa_sesion_resp = px.bar(
            resumen_avatar[resumen_avatar["Respuestas_1er_Msj"] >
                           0].sort_values(by="Tasa Sesiones (vs Resp.) (%)",
                                          ascending=False),
            x="Avatar",
            y="Tasa Sesiones (vs Resp.) (%)",
            title="Tasa de Agendamiento de Sesiones (vs Respuestas) por Avatar",
            color="Tasa Sesiones (vs Resp.) (%)",
            text="Tasa Sesiones (vs Resp.) (%)",
            color_continuous_scale=px.colors.sequential.
            Emrld  # Un verde diferente
        )
        fig_tasa_sesion_resp.update_traces(texttemplate='%{text:.1f}%',
                                           textposition='outside')
        fig_tasa_sesion_resp.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_tasa_sesion_resp, use_container_width=True)
    else:
        st.info(
            "No hay suficientes datos de respuestas para graficar la 'Tasa de Sesiones (vs Respuestas)' por Avatar."
        )

    # Gráfico de Tasa de Sesiones Global (vs Prospectados)
    if not resumen_avatar[resumen_avatar["Prospectados"] > 0].empty:
        fig_tasa_sesion_global = px.bar(
            resumen_avatar[resumen_avatar["Prospectados"] > 0].sort_values(
                by="Tasa Sesiones Global (vs Prosp.) (%)", ascending=False),
            x="Avatar",
            y="Tasa Sesiones Global (vs Prosp.) (%)",
            title=
            "Tasa de Agendamiento de Sesiones Global (vs Prospectados) por Avatar",
            color="Tasa Sesiones Global (vs Prosp.) (%)",
            text="Tasa Sesiones Global (vs Prosp.) (%)",
            color_continuous_scale=px.colors.sequential.Mint)
        fig_tasa_sesion_global.update_traces(texttemplate='%{text:.1f}%',
                                             textposition='outside')
        fig_tasa_sesion_global.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_tasa_sesion_global, use_container_width=True)
    else:
        st.info(
            "No hay suficientes datos para graficar la 'Tasa de Sesiones Global' por Avatar."
        )
