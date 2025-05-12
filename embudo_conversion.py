import streamlit as st
import plotly.express as px
import pandas as pd

# Modificamos la firma para aceptar todos los conteos necesarios (filtrados y base)
# para decidir qué embudo mostrar.
def mostrar_embudo(
    total_filtered, inv_acept_filtered, resp_primer_filtered, sesiones_filtered, primeros_mensajes_enviados_count_filtered,
    base_total, base_inv_acept, base_primeros_mensajes_enviados_count, base_resp_primer, base_sesiones
):
    """Displays the conversion funnel for filtered data, or base data if no filters applied."""
    st.markdown("---")
    st.markdown("## 🚀 Embudo de Conversión")

    # Decidir qué conjunto de datos usar para el embudo: filtrado o base
    # Usamos los datos filtrados si el total filtrado es diferente del total base.
    # Si son iguales, usamos los datos base.
    if total_filtered != base_total:
        # Usar datos filtrados
        display_total = total_filtered
        display_inv_acept = inv_acept_filtered
        display_primeros_mensajes = primeros_mensajes_enviados_count_filtered
        display_resp_primer = resp_primer_filtered
        display_sesiones = sesiones_filtered
        titulo_embudo = 'Embudo de Conversión (Aplicando Filtros)'
        descripcion_embudo = f"Este embudo muestra la conversión para los **{total_filtered}** prospectos que cumplen los filtros."
    else:
        # Usar datos base (cuando no hay filtros o el filtro no reduce los datos)
        display_total = base_total
        display_inv_acept = base_inv_acept
        display_primeros_mensajes = base_primeros_mensajes_enviados_count
        display_resp_primer = base_resp_primer
        display_sesiones = base_sesiones
        titulo_embudo = 'Embudo de Conversión (Base Completa)'
        descripcion_embudo = f"Este embudo muestra la conversión para los **{base_total}** prospectos base."


    # Definimos las etapas del embudo
    etapas = [
        "Prospectos (Inicio)", # Nombre más neutral para la primera etapa del embudo
        "Invites Aceptadas",
        "1er Msj Enviado",
        "Respuesta 1er Mensaje",
        "Sesiones Agendadas"
    ]

    # Creamos el DataFrame para Plotly con los datos seleccionados (filtrados o base)
    df_embudo_display = pd.DataFrame({
        "Etapa": etapas,
        "Cantidad": [
            display_total,
            display_inv_acept,
            display_primeros_mensajes,
            display_resp_primer,
            display_sesiones
        ]
    })

    # Calculamos porcentajes vs etapa ANTERIOR para el conjunto que se mostrará
    def calcular_porcentajes(df_embudo):
        df_embudo['% vs Anterior'] = [
            100.0, # La primera etapa es 100% de sí misma
            (df_embudo['Cantidad'][1] / df_embudo['Cantidad'][0] * 100) if df_embudo['Cantidad'][0] > 0 else 0, # Aceptadas vs Inicio
            (df_embudo['Cantidad'][2] / df_embudo['Cantidad'][1] * 100) if df_embudo['Cantidad'][1] > 0 else 0, # 1er Msj vs Aceptadas
            (df_embudo['Cantidad'][3] / df_embudo['Cantidad'][2] * 100) if df_embudo['Cantidad'][2] > 0 else 0, # Respuestas vs 1er Msj
            (df_embudo['Cantidad'][4] / df_embudo['Cantidad'][3] * 100) if df_embudo['Cantidad'][3] > 0 else 0, # Sesiones vs Respuestas
        ]
        # Asegurar que los porcentajes NaN o Inf sean 0 para la visualización
        df_embudo['% vs Anterior'] = df_embudo['% vs Anterior'].replace([float('inf'), -float('inf')], 0).fillna(0)

        df_embudo['Texto'] = df_embudo.apply(lambda row: f"{row['Cantidad']} ({row['% vs Anterior']:.1f}%)", axis=1)
        return df_embudo

    df_embudo_display = calcular_porcentajes(df_embudo_display)


    # Creamos el gráfico de embudo
    fig = px.funnel(
        df_embudo_display,
        y='Etapa',
        x='Cantidad',
        title=titulo_embudo,
        text='Texto',
        category_orders={"Etapa": etapas} # Forzamos el orden de las etapas
    )

    fig.update_traces(textposition='inside', textinfo='value+percent previous')

    st.plotly_chart(fig, use_container_width=True)

    # Mostrar la descripción debajo del embudo
    st.caption(descripcion_embudo)
