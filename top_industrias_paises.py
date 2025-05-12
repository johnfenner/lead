# componentes/top_industrias_paises.py
import streamlit as st
import plotly.express as px
import pandas as pd
from utils.limpieza import limpiar_valor_kpi


def mostrar_analisis_dimension_agendamiento_flexible(
        df_filtrado,
        dimension_col,
        titulo_dimension,
        top_n_grafico=10,
        mostrar_tabla_completa=False):  # Nuevos parámetros
    st.markdown("---")
    # Ajustar el título principal si solo se muestra el gráfico o ambos
    titulo_seccion = f"Análisis de {titulo_dimension}: Top {top_n_grafico} por Tasa de Agendamiento"
    if mostrar_tabla_completa:
        titulo_seccion += " y Detalle Completo"
    st.markdown(f"## 🏆 {titulo_seccion}")

    if dimension_col not in df_filtrado.columns or "Sesion Agendada?" not in df_filtrado.columns:
        st.warning(
            f"Faltan columnas '{dimension_col}' o 'Sesion Agendada?' para el análisis de {titulo_dimension.lower()}."
        )
        return

    # Calcular prospectados y sesiones agendadas por dimensión
    resumen_dimension_completo = df_filtrado.groupby(
        dimension_col, as_index=False).agg(
            Total_Prospectados=(dimension_col, 'count'),
            Sesiones_Agendadas=("Sesion Agendada?", lambda x:
                                (x.apply(limpiar_valor_kpi) == "si").sum()))
    resumen_dimension_completo.rename(
        columns={resumen_dimension_completo.columns[0]: dimension_col},
        inplace=True)

    resumen_dimension_completo["Tasa Agendamiento (%)"] = (
        (resumen_dimension_completo["Sesiones_Agendadas"] /
         resumen_dimension_completo["Total_Prospectados"]) *
        100).fillna(0).round(1)

    if resumen_dimension_completo.empty:
        st.info(
            f"No hay datos de {titulo_dimension.lower()} para mostrar con los filtros actuales."
        )
        return

    # --- GRÁFICO TOP N POR TASA DE AGENDAMIENTO ---
    # st.markdown(f"### 📊 Top {top_n_grafico} {titulo_dimension} por Mayor Tasa de Agendamiento") # Título ya está arriba

    min_prospectados_para_grafico = 3  # Umbral para que la tasa sea algo significativa
    resumen_para_grafico = resumen_dimension_completo[
        resumen_dimension_completo["Total_Prospectados"] >=
        min_prospectados_para_grafico].copy()

    if not resumen_para_grafico.empty:
        # Ordenar aquí para el gráfico
        df_grafico_ordenado = resumen_para_grafico.sort_values(
            by="Tasa Agendamiento (%)", ascending=False).head(top_n_grafico)

        if not df_grafico_ordenado.empty:
            category_order_y_grafico = df_grafico_ordenado[
                dimension_col].tolist()

            fig_tasa = px.bar(
                df_grafico_ordenado,
                x="Tasa Agendamiento (%)",
                y=dimension_col,
                orientation='h',
                title=
                f'Top {len(df_grafico_ordenado)} {titulo_dimension} por Tasa de Agendamiento (mín. {min_prospectados_para_grafico} prospectados)',
                color="Tasa Agendamiento (%)",
                text="Tasa Agendamiento (%)",
                color_continuous_scale='Greens',
                category_orders={dimension_col:
                                 category_order_y_grafico}  # Asegurar orden
            )
            fig_tasa.update_traces(texttemplate='%{text:.1f}%',
                                   textposition='outside')
            # Ya no es necesario 'total ascending' si se usa category_orders con datos pre-ordenados
            # fig_tasa.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_tasa, use_container_width=True)
        else:
            st.info(
                f"No hay {titulo_dimension.lower()} que cumplan el umbral de {min_prospectados_para_grafico} prospectados para mostrar el gráfico de top tasas."
            )
    else:
        st.info(
            f"No hay suficientes datos (con al menos {min_prospectados_para_grafico} prospectados por categoría) para generar el gráfico de Top {titulo_dimension}."
        )

    # --- TABLA PAGINADA COMPLETA (Condicional) ---
    if mostrar_tabla_completa:
        with st.expander(
                f"Ver Tabla Detallada Completa de {titulo_dimension} ({len(resumen_dimension_completo)} categorías)"
        ):
            tabla_completa_ordenada = resumen_dimension_completo.sort_values(
                by="Tasa Agendamiento (%)", ascending=False)
            tabla_completa_ordenada.reset_index(drop=True, inplace=True)

            num_total_registros_tabla = len(tabla_completa_ordenada)

            opciones_por_pagina_tabla = [
                10, 25, 50, 100, num_total_registros_tabla
            ]
            opciones_por_pagina_filtradas_tabla = [
                opt for opt in opciones_por_pagina_tabla
                if opt < num_total_registros_tabla
            ]
            if num_total_registros_tabla not in opciones_por_pagina_filtradas_tabla:
                opciones_por_pagina_filtradas_tabla.append(
                    num_total_registros_tabla)
            opciones_por_pagina_filtradas_tabla = sorted(
                list(set(opciones_por_pagina_filtradas_tabla)))

            key_registros_por_pagina_tabla = f"tabla_registros_por_pagina_{dimension_col}"
            key_pagina_actual_tabla = f"tabla_pagina_actual_{dimension_col}"

            if key_registros_por_pagina_tabla not in st.session_state:
                st.session_state[
                    key_registros_por_pagina_tabla] = opciones_por_pagina_filtradas_tabla[
                        0] if opciones_por_pagina_filtradas_tabla else 10
            if key_pagina_actual_tabla not in st.session_state:
                st.session_state[key_pagina_actual_tabla] = 1

            col_control_tabla1, col_control_tabla2 = st.columns([1, 3])

            with col_control_tabla1:
                default_rpp_tabla = st.session_state[
                    key_registros_por_pagina_tabla]
                if default_rpp_tabla not in opciones_por_pagina_filtradas_tabla:  #Si el valor en session_state no es una opcion valida
                    default_rpp_tabla = opciones_por_pagina_filtradas_tabla[
                        0] if opciones_por_pagina_filtradas_tabla else 10
                    st.session_state[
                        key_registros_por_pagina_tabla] = default_rpp_tabla

                registros_por_pagina_tabla_sel = st.selectbox(
                    f"Registros por página (Tabla):",
                    options=opciones_por_pagina_filtradas_tabla,
                    index=opciones_por_pagina_filtradas_tabla.index(
                        default_rpp_tabla),
                    key=f"sb_tabla_{key_registros_por_pagina_tabla}")
                if registros_por_pagina_tabla_sel != st.session_state[
                        key_registros_por_pagina_tabla]:
                    st.session_state[
                        key_registros_por_pagina_tabla] = registros_por_pagina_tabla_sel
                    st.session_state[key_pagina_actual_tabla] = 1
                    st.rerun()

            registros_por_pagina_actual_tabla = st.session_state[
                key_registros_por_pagina_tabla]
            num_paginas_total_tabla = (
                num_total_registros_tabla + registros_por_pagina_actual_tabla -
                1
            ) // registros_por_pagina_actual_tabla if registros_por_pagina_actual_tabla > 0 else 1

            with col_control_tabla2:
                if num_paginas_total_tabla > 1:
                    st.session_state[key_pagina_actual_tabla] = st.number_input(
                        f"Página (Tabla - de 1 a {num_paginas_total_tabla}):",
                        min_value=1,
                        max_value=num_paginas_total_tabla,
                        value=min(st.session_state[key_pagina_actual_tabla],
                                  num_paginas_total_tabla
                                  ),  # Asegurar que el valor no exceda el max
                        step=1,
                        key=f"ni_tabla_{key_pagina_actual_tabla}")
                elif num_total_registros_tabla > 0:
                    st.markdown(
                        f"Mostrando **{num_total_registros_tabla}** de **{num_total_registros_tabla}** {titulo_dimension.lower()} en la tabla."
                    )

            pagina_seleccionada_tabla = st.session_state[
                key_pagina_actual_tabla]
            inicio_idx_tabla = (pagina_seleccionada_tabla -
                                1) * registros_por_pagina_actual_tabla
            fin_idx_tabla = inicio_idx_tabla + registros_por_pagina_actual_tabla
            df_pagina_tabla = tabla_completa_ordenada.iloc[
                inicio_idx_tabla:fin_idx_tabla]

            columnas_tabla_display = [
                dimension_col, "Total_Prospectados", "Sesiones_Agendadas",
                "Tasa Agendamiento (%)"
            ]
            st.dataframe(df_pagina_tabla[columnas_tabla_display].style.format(
                {"Tasa Agendamiento (%)": "{:.1f}%"}),
                         use_container_width=True)

            if num_paginas_total_tabla > 1:
                st.caption(
                    f"Mostrando registros del {inicio_idx_tabla + 1} al {min(fin_idx_tabla, num_total_registros_tabla)} de un total de {num_total_registros_tabla} {titulo_dimension.lower()} en la tabla."
                )
