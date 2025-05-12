# componentes/analisis_procesos.py
import streamlit as st
import plotly.express as px
import pandas as pd
from utils.limpieza import limpiar_valor_kpi

# Reutilizamos la función flexible, adaptando el nombre para claridad si se desea
# O simplemente llamamos a la función de top_industrias_paises directamente.
# Aquí la copiamos y renombramos para mantener la lógica separada si evoluciona diferente.


def mostrar_analisis_procesos_con_prospectador(df_filtrado,
                                               top_n_grafico_proceso=10,
                                               mostrar_tabla_proceso=True):
    dimension_col_proceso = "Proceso"  # Columna de Proceso
    titulo_dimension_proceso = "Procesos"

    st.markdown("---")
    titulo_seccion_proceso = f"Análisis de {titulo_dimension_proceso}: Top {top_n_grafico_proceso} por Tasa de Agendamiento"
    if mostrar_tabla_proceso:
        titulo_seccion_proceso += " y Detalle Completo"
    st.markdown(f"## 🎯 {titulo_seccion_proceso}")

    if dimension_col_proceso not in df_filtrado.columns or "Sesion Agendada?" not in df_filtrado.columns:
        st.warning(
            f"Faltan columnas '{dimension_col_proceso}' o 'Sesion Agendada?' para el análisis de procesos."
        )
        return

    # --- Análisis General de Procesos (Gráfico y Tabla Opcional) ---
    resumen_proceso_completo = df_filtrado.groupby(
        dimension_col_proceso, as_index=False).agg(
            Total_Prospectados=(dimension_col_proceso, 'count'),
            Sesiones_Agendadas=("Sesion Agendada?", lambda x:
                                (x.apply(limpiar_valor_kpi) == "si").sum()))
    resumen_proceso_completo.rename(
        columns={resumen_proceso_completo.columns[0]: dimension_col_proceso},
        inplace=True)
    resumen_proceso_completo["Tasa Agendamiento (%)"] = (
        (resumen_proceso_completo["Sesiones_Agendadas"] /
         resumen_proceso_completo["Total_Prospectados"]) *
        100).fillna(0).round(1)

    if resumen_proceso_completo.empty:
        st.info(
            "No hay datos de Procesos para mostrar con los filtros actuales.")
        return

    # Gráfico Top N Procesos
    min_prospectados_para_grafico_proc = 3
    resumen_para_grafico_proc = resumen_proceso_completo[
        resumen_proceso_completo["Total_Prospectados"] >=
        min_prospectados_para_grafico_proc].copy()
    if not resumen_para_grafico_proc.empty:
        df_grafico_proc_ordenado = resumen_para_grafico_proc.sort_values(
            by="Tasa Agendamiento (%)",
            ascending=False).head(top_n_grafico_proceso)
        if not df_grafico_proc_ordenado.empty:
            category_order_y_proc = df_grafico_proc_ordenado[
                dimension_col_proceso].tolist()
            fig_proc_tasa = px.bar(
                df_grafico_proc_ordenado,
                x="Tasa Agendamiento (%)",
                y=dimension_col_proceso,
                orientation='h',
                title=
                f'Top {len(df_grafico_proc_ordenado)} {titulo_dimension_proceso} por Tasa de Agendamiento',
                color="Tasa Agendamiento (%)",
                text="Tasa Agendamiento (%)",
                color_continuous_scale='Plasma',
                category_orders={dimension_col_proceso: category_order_y_proc})
            fig_proc_tasa.update_traces(texttemplate='%{text:.1f}%',
                                        textposition='outside')
            st.plotly_chart(fig_proc_tasa, use_container_width=True)
        else:
            st.info(
                f"No hay Procesos que cumplan el umbral para mostrar el gráfico de top tasas."
            )
    else:
        st.info(
            f"No hay suficientes datos para generar el gráfico de Top {titulo_dimension_proceso}."
        )

    # Tabla Paginada Procesos (si mostrar_tabla_proceso es True)
    if mostrar_tabla_proceso:
        # (Aquí iría la misma lógica de paginación que en la función flexible, adaptada para 'Proceso')
        # Por brevedad, omito la repetición del código de paginación aquí, pero sería idéntico
        # cambiando 'dimension_col' por 'dimension_col_proceso', etc.
        # Puedes copiarlo de la función mostrar_analisis_dimension_agendamiento_flexible
        # y ponerlo dentro de un st.expander.
        with st.expander(
                f"Ver Tabla Detallada Completa de {titulo_dimension_proceso} ({len(resumen_proceso_completo)} categorías)"
        ):
            # ... LÓGICA DE PAGINACIÓN PARA PROCESOS AQUÍ ...
            # Asegúrate de usar claves de session_state únicas para la paginación de procesos.
            # Ejemplo: key_registros_por_pagina_tabla = f"tabla_registros_por_pagina_{dimension_col_proceso}"
            #          key_pagina_actual_tabla = f"tabla_pagina_actual_{dimension_col_proceso}"

            # --- Inicio de la lógica de paginación copiada y adaptada ---
            tabla_completa_ordenada_proc = resumen_proceso_completo.sort_values(
                by="Tasa Agendamiento (%)", ascending=False)
            tabla_completa_ordenada_proc.reset_index(drop=True, inplace=True)

            num_total_registros_tabla_proc = len(tabla_completa_ordenada_proc)

            opciones_por_pagina_tabla_proc = [
                10, 25, 50, 100, num_total_registros_tabla_proc
            ]
            opciones_por_pagina_filtradas_tabla_proc = [
                opt for opt in opciones_por_pagina_tabla_proc
                if opt < num_total_registros_tabla_proc
            ]
            if num_total_registros_tabla_proc not in opciones_por_pagina_filtradas_tabla_proc:
                opciones_por_pagina_filtradas_tabla_proc.append(
                    num_total_registros_tabla_proc)
            opciones_por_pagina_filtradas_tabla_proc = sorted(
                list(set(opciones_por_pagina_filtradas_tabla_proc)))

            key_registros_por_pagina_proc = f"tabla_registros_por_pagina_{dimension_col_proceso}"
            key_pagina_actual_proc = f"tabla_pagina_actual_{dimension_col_proceso}"

            if key_registros_por_pagina_proc not in st.session_state:
                st.session_state[
                    key_registros_por_pagina_proc] = opciones_por_pagina_filtradas_tabla_proc[
                        0] if opciones_por_pagina_filtradas_tabla_proc else 10
            if key_pagina_actual_proc not in st.session_state:
                st.session_state[key_pagina_actual_proc] = 1

            col_control_proc1, col_control_proc2 = st.columns([1, 3])
            with col_control_proc1:
                default_rpp_proc = st.session_state[
                    key_registros_por_pagina_proc]
                if default_rpp_proc not in opciones_por_pagina_filtradas_tabla_proc:
                    default_rpp_proc = opciones_por_pagina_filtradas_tabla_proc[
                        0] if opciones_por_pagina_filtradas_tabla_proc else 10
                    st.session_state[
                        key_registros_por_pagina_proc] = default_rpp_proc

                registros_por_pagina_proc_sel = st.selectbox(
                    "Registros por página (Tabla Procesos):",
                    options=opciones_por_pagina_filtradas_tabla_proc,
                    index=opciones_por_pagina_filtradas_tabla_proc.index(
                        default_rpp_proc),
                    key=f"sb_tabla_{key_registros_por_pagina_proc}")
                if registros_por_pagina_proc_sel != st.session_state[
                        key_registros_por_pagina_proc]:
                    st.session_state[
                        key_registros_por_pagina_proc] = registros_por_pagina_proc_sel
                    st.session_state[key_pagina_actual_proc] = 1
                    st.rerun()

            registros_por_pagina_actual_proc = st.session_state[
                key_registros_por_pagina_proc]
            num_paginas_total_tabla_proc = (
                num_total_registros_tabla_proc +
                registros_por_pagina_actual_proc - 1
            ) // registros_por_pagina_actual_proc if registros_por_pagina_actual_proc > 0 else 1

            with col_control_proc2:
                if num_paginas_total_tabla_proc > 1:
                    st.session_state[key_pagina_actual_proc] = st.number_input(
                        f"Página (Tabla Procesos - de 1 a {num_paginas_total_tabla_proc}):",
                        min_value=1,
                        max_value=num_paginas_total_tabla_proc,
                        value=min(st.session_state[key_pagina_actual_proc],
                                  num_paginas_total_tabla_proc),
                        step=1,
                        key=f"ni_tabla_{key_pagina_actual_proc}")
                elif num_total_registros_tabla_proc > 0:
                    st.markdown(
                        f"Mostrando **{num_total_registros_tabla_proc}** de **{num_total_registros_tabla_proc}** procesos en la tabla."
                    )

            pagina_seleccionada_proc = st.session_state[key_pagina_actual_proc]
            inicio_idx_proc = (pagina_seleccionada_proc -
                               1) * registros_por_pagina_actual_proc
            fin_idx_proc = inicio_idx_proc + registros_por_pagina_actual_proc
            df_pagina_proc = tabla_completa_ordenada_proc.iloc[
                inicio_idx_proc:fin_idx_proc]

            columnas_tabla_proc_display = [
                dimension_col_proceso, "Total_Prospectados",
                "Sesiones_Agendadas", "Tasa Agendamiento (%)"
            ]
            st.dataframe(
                df_pagina_proc[columnas_tabla_proc_display].style.format(
                    {"Tasa Agendamiento (%)": "{:.1f}%"}),
                use_container_width=True)
            if num_paginas_total_tabla_proc > 1:
                st.caption(
                    f"Mostrando registros del {inicio_idx_proc + 1} al {min(fin_idx_proc, num_total_registros_tabla_proc)} de un total de {num_total_registros_tabla_proc} procesos en la tabla."
                )
            # --- Fin de la lógica de paginación ---

    # --- Comparativa Proceso vs Quién Prospectó ---
    st.markdown(f"### 📊 Efectividad por Proceso y Prospectador")
    if "Proceso" in df_filtrado.columns and "¿Quién Prospecto?" in df_filtrado.columns:
        # Filtrar prospectadores con pocos datos para no saturar el gráfico
        prospectadores_validos = df_filtrado["¿Quién Prospecto?"].value_counts(
        )
        prospectadores_a_mostrar = prospectadores_validos[
            prospectadores_validos >=
            5].index.tolist()  # Mínimo 5 prospectos por prospectador

        if prospectadores_a_mostrar:
            df_proceso_prospectador = df_filtrado[df_filtrado[
                "¿Quién Prospecto?"].isin(prospectadores_a_mostrar)]

            resumen_proc_prosp = df_proceso_prospectador.groupby(
                ["Proceso", "¿Quién Prospecto?"], as_index=False).agg(
                    Total_Prospectados_PP=("Proceso", 'count'),
                    Sesiones_Agendadas_PP=(
                        "Sesion Agendada?", lambda x:
                        (x.apply(limpiar_valor_kpi) == "si").sum()))
            resumen_proc_prosp["Tasa Agendamiento PP (%)"] = (
                (resumen_proc_prosp["Sesiones_Agendadas_PP"] /
                 resumen_proc_prosp["Total_Prospectados_PP"]) *
                100).fillna(0).round(1)

            # Mostrar solo combinaciones con un mínimo de prospectados para que la tasa sea relevante
            resumen_proc_prosp_filtrado = resumen_proc_prosp[
                resumen_proc_prosp["Total_Prospectados_PP"]
                >= 3]  # Mínimo 3 prospectos para esta combinación

            if not resumen_proc_prosp_filtrado.empty:
                fig_proc_prosp = px.bar(
                    resumen_proc_prosp_filtrado.sort_values(
                        by=["Proceso", "Tasa Agendamiento PP (%)"],
                        ascending=[True, False]),
                    x="Proceso",
                    y="Tasa Agendamiento PP (%)",
                    color="¿Quién Prospecto?",
                    barmode="group",  # Barras agrupadas
                    title="Tasa de Agendamiento por Proceso y Prospectador",
                    text="Tasa Agendamiento PP (%)")
                fig_proc_prosp.update_traces(texttemplate='%{text:.0f}%',
                                             textposition='outside')
                fig_proc_prosp.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_proc_prosp, use_container_width=True)

                with st.expander("Ver tabla Proceso vs Prospectador"):
                    st.dataframe(resumen_proc_prosp_filtrado,
                                 use_container_width=True)
            else:
                st.info(
                    "No hay suficientes datos combinados de Proceso y Prospectador para mostrar la comparativa de tasas (se requiere mín. 3 prospectos por combinación)."
                )
        else:
            st.info(
                "No hay Prospectadores con suficientes datos (mín. 5 prospectos) para la comparativa por Proceso."
            )
    else:
        st.warning(
            "Faltan columnas 'Proceso' o '¿Quién Prospecto?' para la comparativa."
        )
