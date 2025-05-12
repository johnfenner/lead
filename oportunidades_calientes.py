# componentes/oportunidades_calientes.py
import streamlit as st
import pandas as pd
from utils.limpieza import limpiar_valor_kpi


def mostrar_oportunidades_calientes(df_prospectos):
    st.markdown("---")
    st.markdown("## 🚀 Oportunidades Clave para Agendar")
    st.caption(
        "Prospectos que aceptaron la invitación y respondieron al primer mensaje, pero aún no tienen sesión agendada."
    )

    # Asegurarse de que las columnas necesarias existan
    required_cols = [
        "¿Invite Aceptada?", "Respuesta Primer Mensaje", "Sesion Agendada?"
    ]
    if not all(col in df_prospectos.columns for col in required_cols):
        missing = [
            col for col in required_cols if col not in df_prospectos.columns
        ]
        st.warning(
            f"Faltan columnas ({', '.join(missing)}) para identificar oportunidades. Verifica la carga de datos."
        )
        return

    try:
        oportunidades = df_prospectos[
            (df_prospectos["¿Invite Aceptada?"].apply(limpiar_valor_kpi) ==
             "si") & (df_prospectos["Respuesta Primer Mensaje"].apply(
                 lambda x: limpiar_valor_kpi(x) not in ["no", "", "nan"])) &
            (df_prospectos["Sesion Agendada?"].apply(limpiar_valor_kpi)
             == "no")].copy()

        if oportunidades.empty:
            st.info(
                "🎉 ¡Felicidades! No tienes prospectos calientes pendientes de agendamiento según los filtros actuales, o no hay datos que cumplan estos criterios."
            )
            return

        # Definir las columnas que quieres mostrar (sin "Días Desde Respuesta")
        columnas_a_mostrar = [
            "Nombre", "Apellido", "Empresa", "Puesto", "Avatar",
            "¿Quién Prospecto?"
        ]
        # Si tienes una columna con el link de LinkedIn que quieras mostrar, añádela aquí:
        # if "LinkedIn" in oportunidades.columns:
        #     columnas_a_mostrar.append("LinkedIn")

        # Filtrar para mostrar solo columnas existentes en el DataFrame 'oportunidades'
        columnas_existentes = [
            col for col in columnas_a_mostrar if col in oportunidades.columns
        ]

        # Añadir una columna simple que indique la fecha del primer mensaje si existe, sin calcular días
        if "Fecha Primer Mensaje" in oportunidades.columns:
            if "Fecha Primer Mensaje" not in columnas_existentes:  # Evitar duplicados si ya estaba
                columnas_existentes.append("Fecha Primer Mensaje")
            # Formatear la fecha si es necesario para visualización, pero no es crítico para esta versión
            # oportunidades["Fecha Primer Mensaje Display"] = pd.to_datetime(oportunidades["Fecha Primer Mensaje"], errors='coerce').dt.strftime('%d/%m/%Y')
            # st.dataframe(oportunidades[columnas_existentes_con_fecha_display], ...)

        if not columnas_existentes:
            st.warning(
                "No hay columnas de información de prospecto para mostrar en las oportunidades."
            )
            return

        st.dataframe(
            oportunidades[
                columnas_existentes],  # Mostrar sin ordenamiento específico por días
            use_container_width=True,
            height=300)
        st.caption(
            f"Encontradas **{len(oportunidades)}** oportunidades clave para seguimiento."
        )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar las oportunidades clave: {e}")
        # Opcional: st.exception(e) para más detalles en el log si estás depurando
