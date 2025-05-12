# Proyecto/pages/mensajes_personalizados.py

import streamlit as st
import pandas as pd
import sys
import os
# Eliminamos la importación de AgGrid ya que usamos st.dataframe
# from st_aggrid import AgGrid, GridOptionsBuilder

# Añadir la raíz del proyecto al path para poder importar módulos
# Esto es importante para que los imports como 'from datos.carga_datos import ...' funcionen
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, project_root)

# --- IMPORTS DE TU PROYECTO EXISTENTE ---
# Asegúrate de que estas importaciones coincidan con la ubicación real de tus archivos
from datos.carga_datos import cargar_y_limpiar_datos  # Para cargar los datos base
from filtros.aplicar_filtros import aplicar_filtros  # Para aplicar filtros (adaptaremos su uso)
from mensajes.mensajes import (  # Tus plantillas de mensajes
    mensaje_1_h2r, mensaje_2_h2r, mensaje_3_h2r, mensaje_1_p2p, mensaje_2_p2p,
    mensaje_1_o2c, mensaje_2_o2c, mensaje_1_general, mensaje_2_general)
from mensajes.mensajes_streamlit import clasificar_por_proceso  # Función para categorizar
from utils.limpieza import limpiar_valor_kpi, estandarizar_avatar, limpiar_nombre_completo  # Funciones de utilidad


# --- FUNCIÓN PARA LIMPIAR FILTROS DE ESTA PÁGINA ---
def reset_mensaje_filtros_state():
    """Resets all message filter keys and hides the results table."""
    st.session_state.mensaje_filtros = {
        "invite_aceptada": "si",  # Default mandatory filter (estandarizado)
        "fuente_lista": ["– Todos –"],
        "proceso": ["– Todos –"],
        "avatar": ["– Todos –"],
        "pais": ["– Todos –"],
        "industria": ["– Todos –"],
        "prospectador": ["– Todos –"],
        "sesion_agendada":
        "– Todos –",  # Estado para el filtro de Sesión Agendada
        "fecha_ini": None,
        "fecha_fin": None,
        "busqueda": ""
    }
    # Ocultar la tabla de resultados al limpiar los filtros
    st.session_state.mostrar_tabla_mensajes = False
    st.toast("Filtros de mensajes reiniciados ✅")  # Notificación opcional


# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Mensajes Personalizados", layout="wide")
st.title("💌 Generador de Mensajes Personalizados")
st.markdown(
    "Aquí puedes filtrar a los prospectos que aceptaron tu invitación y generar mensajes personalizados basados en plantillas."
)


# --- CARGA DE DATOS BASE ---
# Cargar el DataFrame base (todo el conjunto de datos inicial)
# Utilizamos st.cache_data para evitar recargar los datos en cada interacción
@st.cache_data
def get_base_data():
    # Reutilizamos la función existente
    df_base = cargar_y_limpiar_datos()
    # Opcional: Si tienes procesamiento adicional en cargar_y_procesar_datos
    # que no sea dependiente de filtros y sea útil para el dataframe base, agrégalo aquí.
    # Por ejemplo, si calcular_dias_respuesta se aplica al DF base:
    # from datos.carga_datos import cargar_y_procesar_datos # Asegúrate de importar si es necesario
    # df_base = cargar_y_procesar_datos(df_base.copy()) # Aplica procesamiento si es relevante aquí

    # Asegúrate de que la columna 'Fecha de Invite' sea datetime para posibles filtros futuros
    if "Fecha de Invite" in df_base.columns:
        # Convertir solo si la columna no es ya datetime
        if not pd.api.types.is_datetime64_any_dtype(
                df_base["Fecha de Invite"]):
            df_base["Fecha de Invite"] = pd.to_datetime(
                df_base["Fecha de Invite"], errors='coerce')

    return df_base


df = get_base_data()

# Manejar el caso de que no se carguen datos
if df is None or df.empty:
    st.warning(
        "No se pudieron cargar los datos o el DataFrame base está vacío.")
    st.stop()  # Detiene la ejecución del resto del script de la página

# --- ESTADO DE LA PÁGINA ---
# Usamos st.session_state para mantener el estado de los filtros y si mostrar la tabla
if 'mensaje_filtros' not in st.session_state:
    st.session_state.mensaje_filtros = {
        "invite_aceptada": "si",  # Default mandatory filter (estandarizado)
        "fuente_lista": ["– Todos –"],
        "proceso": ["– Todos –"],
        "avatar": ["– Todos –"],
        "pais": ["– Todos –"],
        "industria": ["– Todos –"],
        "prospectador": ["– Todos –"],
        "sesion_agendada":
        "– Todos –",  # Estado para el filtro de Sesión Agendada
        "fecha_ini": None,
        "fecha_fin": None,
        "busqueda": ""
    }

# Estado para controlar la visualización de la tabla y generador
if 'mostrar_tabla_mensajes' not in st.session_state:
    st.session_state.mostrar_tabla_mensajes = False

# --- SECCIÓN DE FILTROS ESPECÍFICOS PARA MENSAJES ---
st.subheader("⚙️ Configura los Filtros para tus Mensajes")

# Aseguramos que 'Invite Aceptada' sea 'Si' ya que los mensajes son para ellos
st.write(
    "**1. Invite Aceptada:** Los mensajes solo se generan para prospectos que han aceptado la invitación."
)
# Puedes hacer esto un selectbox no modificable o simplemente informarlo.
# Si quieres permitir que el usuario lo vea pero no cambiarlo:
st.selectbox(
    "Filtro Obligatorio",
    ["Si"],  # Solo permitimos "Si"
    index=0,
    label_visibility=
    "collapsed",  # Oculta la etiqueta principal si no quieres que se vea "Filtro Obligatorio"
    disabled=True,  # Deshabilita el selector para que no se pueda cambiar
    key=
    'mensaje_invite_aceptada_display'  # Clave diferente para no interferir si hubiese otro widget similar
)
# Aseguramos que el estado interno del filtro sea "si" (valor estandarizado para la función limpiar_valor_kpi)
st.session_state.mensaje_filtros["invite_aceptada"] = "si"

st.write(
    "**2. Filtros Adicionales (Opcional):** Afina tu selección de prospectos.")

# Contenedor para los filtros opcionales para mantenerlos juntos
with st.expander("Filtros Opcionales"):
    # Primera fila de 2 columnas
    col1, col2 = st.columns(2)
    with col1:
        # Replicamos la lógica de crear_multiselect pero para esta página y con keys únicas
        opciones_fuente = ["– Todos –"] + sorted(
            df["Fuente de la Lista"].dropna().astype(str).unique().tolist(
            )) if "Fuente de la Lista" in df.columns and not df[
                "Fuente de la Lista"].empty else ["– Todos –"]
        st.session_state.mensaje_filtros["fuente_lista"] = st.multiselect(
            "Fuente de la Lista",
            opciones_fuente,
            default=st.session_state.mensaje_filtros.get(
                "fuente_lista",
                ["– Todos –"]),  # Usar .get con default por seguridad
            key="mensaje_filtro_fuente_lista"  # Clave única para este widget
        )

        opciones_proceso = ["– Todos –"] + sorted(
            df["Proceso"].dropna().astype(str).unique().tolist(
            )) if "Proceso" in df.columns and not df["Proceso"].empty else [
                "– Todos –"
            ]
        st.session_state.mensaje_filtros["proceso"] = st.multiselect(
            "Proceso",
            opciones_proceso,
            default=st.session_state.mensaje_filtros.get(
                "proceso", ["– Todos –"]),
            key="mensaje_filtro_proceso"  # Clave única
        )

        opciones_avatar = ["– Todos –"] + sorted(df["Avatar"].dropna().astype(
            str).str.strip().str.title().unique().tolist(
            )) if "Avatar" in df.columns and not df["Avatar"].empty else [
                "– Todos –"
            ]
        st.session_state.mensaje_filtros["avatar"] = st.multiselect(
            "Avatar",
            opciones_avatar,
            default=st.session_state.mensaje_filtros.get(
                "avatar", ["– Todos –"]),
            key="mensaje_filtro_avatar"  # Clave única
        )

    with col2:
        opciones_pais = ["– Todos –"] + sorted(
            df["Pais"].dropna().astype(str).unique().tolist()
        ) if "Pais" in df.columns and not df["Pais"].empty else ["– Todos –"]
        st.session_state.mensaje_filtros["pais"] = st.multiselect(
            "País",
            opciones_pais,
            default=st.session_state.mensaje_filtros.get(
                "pais", ["– Todos –"]),
            key="mensaje_filtro_pais"  # Clave única
        )

        opciones_industria = ["– Todos –"] + sorted(
            df["Industria"].dropna().astype(str).unique().tolist()
        ) if "Industria" in df.columns and not df["Industria"].empty else [
            "– Todos –"
        ]
        st.session_state.mensaje_filtros["industria"] = st.multiselect(
            "Industria",
            opciones_industria,
            default=st.session_state.mensaje_filtros.get(
                "industria", ["– Todos –"]),
            key="mensaje_filtro_industria"  # Clave única
        )

        opciones_prospectador = ["– Todos –"] + sorted(
            df["¿Quién Prospecto?"].dropna().astype(str).unique().tolist(
            )) if "¿Quién Prospecto?" in df.columns and not df[
                "¿Quién Prospecto?"].empty else ["– Todos –"]
        st.session_state.mensaje_filtros["prospectador"] = st.multiselect(
            "¿Quién Prospectó?",
            opciones_prospectador,
            default=st.session_state.mensaje_filtros.get(
                "prospectador", ["– Todos –"]),
            key="mensaje_filtro_prospectador"  # Clave única
        )

    # --- Usamos un st.container para forzar que la siguiente sección vaya debajo ---
    # Este container contiene el separador y la fila de filtros de Sesión/Fecha
    with st.container():
        st.markdown("---")  # Separador visual

        # Obtener el rango de fechas de los datos para restringir la selección en el date_input
        fecha_min_data = None
        fecha_max_data = None
        if "Fecha de Invite" in df.columns and pd.api.types.is_datetime64_any_dtype(
                df["Fecha de Invite"]):
            valid_dates = df["Fecha de Invite"].dropna()
            if not valid_dates.empty:
                fecha_min_data = valid_dates.min().date()
                fecha_max_data = valid_dates.max().date()

        # Usamos 3 columnas para Sesión Agendada, Fecha Desde, Fecha Hasta
        col_sesion, col_f1, col_f2 = st.columns(3)

        with col_sesion:
            # Selector para Sesión Agendada
            opciones_sesion = ["– Todos –", "Si", "No"]
            st.session_state.mensaje_filtros["sesion_agendada"] = st.selectbox(
                "¿Sesión Agendada?",
                opciones_sesion,
                index=opciones_sesion.index(
                    st.session_state.mensaje_filtros.get(
                        "sesion_agendada", "– Todos –")),
                key="mensaje_filtro_sesion_agendada"  # Clave única
            )

        with col_f1:
            st.session_state.mensaje_filtros["fecha_ini"] = st.date_input(
                "Desde (Fecha de Invite)",
                value=st.session_state.mensaje_filtros.get("fecha_ini", None),
                format='DD/MM/YYYY',
                key="mensaje_fecha_ini",  # Clave única
                min_value=fecha_min_data,
                max_value=fecha_max_data)
        with col_f2:
            st.session_state.mensaje_filtros["fecha_fin"] = st.date_input(
                "Hasta (Fecha de Invite)",
                value=st.session_state.mensaje_filtros.get("fecha_fin", None),
                format='DD/MM/YYYY',
                key="mensaje_fecha_fin",  # Clave única
                min_value=fecha_min_data,
                max_value=fecha_max_data)

# Campo de búsqueda global (fuera del expander)
st.session_state.mensaje_filtros["busqueda"] = st.text_input(
    "🔎 Buscar en Nombre, Apellido, Empresa, Puesto (aplica después del filtro Invite Aceptada)",
    value=st.session_state.mensaje_filtros.get("busqueda", ""),
    placeholder="Ingrese término y presione Enter",
    key="mensaje_busqueda"  # Clave única
)

# --- Botones de Acción (Cargar y Limpiar) ---
col_buttons1, col_buttons2 = st.columns(2)
with col_buttons1:
    if st.button("Cargar y Filtrar Prospectos para Mensaje"):
        st.session_state.mostrar_tabla_mensajes = True  # Activamos la visualización
        # st.rerun() # Dejamos que Streamlit maneje el rerun

with col_buttons2:
    # BOTÓN LIMPIAR FILTROS DE MENSAJES
    # Usamos key para asegurar que Streamlit maneje el estado del botón correctamente
    st.button("🧹 Limpiar Filtros de Mensajes",
              on_click=reset_mensaje_filtros_state,
              key="mensaje_limpiar_filtros_btn")

# --- SECCIÓN DE RESULTADOS Y GENERADOR (Condicional) ---
# Solo mostramos esta sección si el botón fue presionado (o si el estado ya está activo)
if st.session_state.mostrar_tabla_mensajes:
    st.markdown("---")
    st.subheader("Resultado de los Filtros y Generador de Mensajes")

    # Aplicar los filtros a los datos base
    df_mensajes_filtrado = df.copy()  # Partimos del dataframe base

    # --- Aplicar Filtro Obligatorio "Invite Aceptada" = "Si" ---
    if "¿Invite Aceptada?" in df_mensajes_filtrado.columns:
        df_mensajes_filtrado = df_mensajes_filtrado[
            df_mensajes_filtrado["¿Invite Aceptada?"].apply(
                lambda x: limpiar_valor_kpi(
                    x) == st.session_state.mensaje_filtros["invite_aceptada"]
            )  # Usamos el valor estandarizado 'si'
        ]
    else:
        st.warning(
            "La columna '¿Invite Aceptada?' no se encontró. No se pueden filtrar prospectos que aceptaron la invite."
        )
        df_mensajes_filtrado = df_mensajes_filtrado[
            0:0]  # Aseguramos que el DF esté vacío si falta la columna

    # Si después del filtro obligatorio el DF ya está vacío, no apliques más filtros
    if not df_mensajes_filtrado.empty:
        # --- Aplicar Filtros Adicionales Seleccionados (reutilizando aplicar_filtros) ---
        # Pasamos los valores de los filtros de esta página a los parámetros correctos
        # Pasamos "– Todos –" para el filtro Invite Aceptada porque ya la filtramos arriba.
        try:
            df_mensajes_filtrado = aplicar_filtros(
                df_mensajes_filtrado,  # Usamos el DF ya filtrado por Invite Aceptada
                st.session_state.mensaje_filtros.get(
                    "fuente_lista", ["– Todos –"]),  # filtro_fuente_lista
                st.session_state.mensaje_filtros.get(
                    "proceso", ["– Todos –"]),  # filtro_proceso
                st.session_state.mensaje_filtros.get(
                    "pais", ["– Todos –"]),  # filtro_pais
                st.session_state.mensaje_filtros.get(
                    "industria", ["– Todos –"]),  # filtro_industria
                st.session_state.mensaje_filtros.get(
                    "avatar", ["– Todos –"]),  # filtro_avatar
                st.session_state.mensaje_filtros.get(
                    "prospectador", ["– Todos –"]),  # filtro_prospectador
                "– Todos –",  # filtro_invite_aceptada_simple (ya filtrado)
                st.session_state.mensaje_filtros.get(
                    "sesion_agendada", "– Todos –"
                ),  # <-- Pasamos el valor del nuevo filtro de Sesión Agendada
                st.session_state.mensaje_filtros.get("fecha_ini",
                                                     None),  # fecha_ini
                st.session_state.mensaje_filtros.get("fecha_fin",
                                                     None)  # fecha_fin
            )
        except TypeError as e:
            st.error(
                f"Error al aplicar filtros. Verifica que la función 'aplicar_filtros' en 'filtros/aplicar_filtros.py' reciba exactamente 10 argumentos: df, filtro_fuente_lista, filtro_proceso, filtro_pais, filtro_industria, filtro_avatar, filtro_prospectador, filtro_invite_aceptada_simple, filtro_sesion_agendada, fecha_ini, fecha_fin. Error: {e}"
            )
            df_mensajes_filtrado = df_mensajes_filtrado[
                0:0]  # Vaciar DF si hay un error en el filtro
            # No usar st.stop() aquí para que el usuario vea el mensaje de error y los filtros
            # st.stop() # Detener ejecución si el filtro falla críticamente

        # --- Aplicar Búsqueda Global ---
        busqueda_term = st.session_state.mensaje_filtros.get(
            "busqueda", "").lower().strip()
        if busqueda_term and not df_mensajes_filtrado.empty:
            mask = pd.Series([False] * len(df_mensajes_filtrado),
                             index=df_mensajes_filtrado.index)
            columnas_busqueda = ["Empresa", "Puesto"]
            for col in columnas_busqueda:
                if col in df_mensajes_filtrado.columns:
                    mask |= df_mensajes_filtrado[col].astype(
                        str).str.lower().str.contains(busqueda_term, na=False)

            # Manejo específico para Nombre y Apellido combinados o separados
            if "Nombre" in df_mensajes_filtrado.columns and "Apellido" in df_mensajes_filtrado.columns:
                # Crear una columna temporal con el nombre completo en minúsculas
                nombre_completo = (
                    df_mensajes_filtrado["Nombre"].fillna('') + ' ' +
                    df_mensajes_filtrado["Apellido"].fillna('')).str.lower()
                mask |= nombre_completo.str.contains(
                    busqueda_term, na=False)  # Corregido: usar 'busqueda_term'
            else:  # Si no existen ambas, buscamos en las que sí existan
                if "Nombre" in df_mensajes_filtrado.columns:
                    mask |= df_mensajes_filtrado["Nombre"].astype(
                        str).str.lower().str.contains(busqueda_term, na=False)
                if "Apellido" in df_mensajes_filtrado.columns:
                    mask |= df_mensajes_filtrado["Apellido"].astype(
                        str).str.lower().str.contains(busqueda_term, na=False)

            # Aplicar la máscara para obtener el DataFrame resultante de la búsqueda
            df_mensajes_filtrado = df_mensajes_filtrado[mask]

    # --- Preparar DataFrame Final para la Tabla y Generador ---
    df_mensajes_final = df_mensajes_filtrado.copy()

    if df_mensajes_final.empty:
        st.warning("No se encontraron prospectos que cumplan los criterios.")
    else:
        # **Nombre esperado de la columna del link de LinkedIn**
        linkedin_col_name = "LinkedIn"  # <--- ¡Verifica que sea este nombre exacto!
        # Eliminamos la columna HTML y la lógica asociada

        # Añadir columnas necesarias si existen (esto asegura que el código posterior no falle si una columna falta)
        # Incluimos el nombre de la columna ORIGINAL del link
        columnas_necesarias = [
            "Nombre", "Apellido", "Empresa", "Puesto", "Proceso", "Avatar",
            "Fecha de Invite", "¿Invite Aceptada?", "¿Quién Prospecto?",
            linkedin_col_name, "Sesion Agendada?"
        ]
        for col in columnas_necesarias:
            # Si la columna no existe en el DF actual (después de filtros), la añadimos con pd.NA
            # Si ya existe, no hacemos nada, manteniendo el valor original de la carga base
            if col not in df_mensajes_final.columns:
                df_mensajes_final[
                    col] = pd.NA  # Usar pd.NA es estándar para representar datos faltantes

        # --- LIMPIAR COLUMNA DE LINKEDIN (NINGUNA LIMPIEZA ESPECÍFICA) ---
        # Eliminamos cualquier limpieza adicional. La columna se muestra tal cual viene de la carga base.
        # La responsabilidad de cómo se muestra recae completamente en st.dataframe y el tipo de dato cargado.

        # Categorizar por Proceso (usando la función de tu proyecto)
        df_mensajes_final["Categoría"] = df_mensajes_final["Proceso"].apply(
            clasificar_por_proceso)

        # Estandarizar Avatar (usando la función de tu proyecto)
        if "Avatar" in df_mensajes_final.columns:  # Asegurarse de que la columna exista
            df_mensajes_final["Avatar"] = df_mensajes_final["Avatar"].apply(
                estandarizar_avatar)
        else:
            df_mensajes_final[
                "Avatar"] = "Desconocido"  # Valor por defecto si la columna no existe

        # Crear Nombre Completo para visualización y plantillas (usando la función de tu proyecto)
        # Asegurarse de que las columnas Nombre y Apellido existan o manejar su ausencia
        nombre_col = "Nombre" if "Nombre" in df_mensajes_final.columns else None
        apellido_col = "Apellido" if "Apellido" in df_mensajes_final.columns else None

        if nombre_col or apellido_col:
            df_mensajes_final["Nombre_Completo"] = df_mensajes_final.apply(
                lambda row: limpiar_nombre_completo(row.get(
                    nombre_col, ""), row.get(apellido_col, "")).title()
                if nombre_col or apellido_col else "Desconocido",
                axis=1)
        else:
            df_mensajes_final["Nombre_Completo"] = "Desconocido"

        # --- TABLA DE PROSPECTOS FILTRADOS PARA MENSAJE (USANDO st.dataframe) ---
        st.markdown("### 📋 Prospectos Encontrados para Mensajes")
        st.write(
            f"Mostrando **{len(df_mensajes_final)}** prospectos que cumplen los criterios."
        )
        # Eliminamos la nota de seguridad del HTML ya que no lo usamos

        # **Columnas a mostrar en st.dataframe**
        # Usamos el nombre de la columna ORIGINAL del link
        columnas_st_dataframe_tabla = [
            "Nombre_Completo", "Empresa", "Puesto", "Categoría", "Avatar",
            "Fecha de Invite", "¿Quién Prospecto?", "Sesion Agendada?",
            linkedin_col_name
        ]  # <-- Usamos la columna ORIGINAL

        # Nos aseguramos de pasar solo las columnas que existen para evitar errores
        cols_to_display_tabla = [
            col for col in columnas_st_dataframe_tabla
            if col in df_mensajes_final.columns
        ]

        # Mostrar la tabla usando st.dataframe (sin unsafe_allow_html)
        st.dataframe(df_mensajes_final[cols_to_display_tabla],
                     use_container_width=True
                     # Eliminamos unsafe_allow_html=True
                     )

        # --- GENERADOR DE MENSAJES ---
        st.markdown("---")
        st.markdown("### 📬️ Generador de Mensajes")
        st.write(
            "Selecciona una categoría y plantilla para generar mensajes personalizados."
        )

        # Definir opciones de mensajes (reutilizando mensajes.py)
        opciones = {
            "H2R": {
                "Mensaje 1 H2R": mensaje_1_h2r,
                "Mensaje 2 H2R": mensaje_2_h2r,
                "Mensaje 3 H2R": mensaje_3_h2r
            },
            "P2P": {
                "Mensaje 1 P2P": mensaje_1_p2p,
                "Mensaje 2 P2P": mensaje_2_p2p
            },
            "O2C": {
                "Mensaje 1 O2C": mensaje_1_o2c,
                "Mensaje 2 O2C": mensaje_2_o2c
            },
            "General": {
                "Mensaje 1 General": mensaje_1_general,
                "Mensaje 2 General": mensaje_2_general
            },
        }

        # Obtener categorías disponibles en el DataFrame filtrado final
        categorias_disponibles = sorted(
            df_mensajes_final["Categoría"].unique().tolist())
        # Mostrar solo categorías para las que tenemos plantillas definidas
        categorias_con_plantillas = [
            cat for cat in categorias_disponibles if cat in opciones
        ]

        if not categorias_con_plantillas:
            st.warning(
                "No hay prospectos con categorías de Proceso definidas en los datos filtrados para las que tengamos plantillas de mensajes."
            )
        else:
            categoria_seleccionada = st.selectbox(
                "Selecciona una categoría de mensaje",
                categorias_con_plantillas,
                key="mensaje_categoria_selector"  # Clave única
            )

            plantillas_disponibles = opciones.get(categoria_seleccionada, {})
            nombres_plantillas = list(plantillas_disponibles.keys())

            if not nombres_plantillas:
                st.warning(
                    f"No hay plantillas definidas para la categoría '{categoria_seleccionada}'."
                )
                mensaje_seleccionado = ""
            else:
                nombre_plantilla_seleccionada = st.selectbox(
                    "Escoge una versión del mensaje",
                    nombres_plantillas,
                    key="mensaje_plantilla_selector"  # Clave única
                )
                mensaje_seleccionado = plantillas_disponibles.get(
                    nombre_plantilla_seleccionada, "")

            st.markdown("### 📟 Vista Previa y Descarga de Mensajes")
            # Eliminamos la nota de seguridad del HTML

            if mensaje_seleccionado:
                # Filtrar el DF final por la categoría seleccionada para la vista previa
                df_vista_previa = df_mensajes_final[
                    df_mensajes_final["Categoría"] ==
                    categoria_seleccionada].copy()

                # Generar el mensaje personalizado
                df_vista_previa[
                    "Mensaje_Personalizado"] = df_vista_previa.apply(
                        lambda row: mensaje_seleccionado.replace(
                            "{nombre}",
                            str(row.get("Nombre", "")).split()[0] if pd.notna(
                                row.get("Nombre")) and str(row.get("Nombre")).
                            strip() else "[Nombre]").replace(
                                "{avatar}",
                                str(row.get("Avatar", "John Bermúdez"))
                                if pd.notna(row.get("Avatar")) and str(
                                    row.get("Avatar")).strip() else
                                "John Bermúdez"),
                        axis=1)

                # **Columnas a mostrar en st.dataframe para la vista previa**
                # Usamos el nombre de la columna ORIGINAL del link
                columnas_st_dataframe_generador = [
                    "Nombre_Completo", "Empresa", "Puesto", "Avatar",
                    "Sesion Agendada?", linkedin_col_name,
                    "Mensaje_Personalizado"
                ]  # <-- Usamos la columna ORIGINAL

                # Nos aseguramos de pasar solo las columnas que existen para evitar errores
                cols_to_display_generador = [
                    col for col in columnas_st_dataframe_generador
                    if col in df_vista_previa.columns
                ]

                # Mostrar la tabla con los mensajes generados usando st.dataframe (sin unsafe_allow_html)
                st.dataframe(df_vista_previa[cols_to_display_generador],
                             use_container_width=True
                             # Eliminamos unsafe_allow_html=True
                             )

                # Botón de descarga
                @st.cache_data
                def convert_df_to_csv(
                        df_to_convert):  # Cambiado el nombre del argumento
                    # **Columnas para la descarga**
                    # Usamos el nombre de la columna ORIGINAL del link
                    cols_descarga = [
                        "Nombre_Completo", "Empresa", "Puesto",
                        "Sesion Agendada?", linkedin_col_name,
                        "Mensaje_Personalizado"
                    ]  # <-- Usamos la columna ORIGINAL
                    # Asegurar que las columnas existan antes de intentar seleccionarlas
                    cols_existentes_descarga = [
                        col for col in cols_descarga
                        if col in df_to_convert.columns
                    ]
                    if not cols_existentes_descarga:
                        st.warning(
                            "No hay columnas disponibles para descargar.")
                        return None  # Retorna None si no hay columnas válidas

                    # Asegurarse de que los valores pd.NA o None no se conviertan a la cadena "NA" en el CSV
                    # Usamos fillna('') para reemplazar NaNs/Nones/pd.NA con string vacío en el CSV
                    df_for_csv = df_to_convert[
                        cols_existentes_descarga].fillna('')

                    return df_for_csv.to_csv(index=False).encode('utf-8')

                csv_mensajes = convert_df_to_csv(
                    df_vista_previa
                )  # Usamos el DF de vista previa para descargar

                if csv_mensajes is not None:
                    st.download_button(
                        label="⬇️ Descargar Mensajes Generados (CSV)",
                        data=csv_mensajes,
                        file_name=
                        f'mensajes_{categoria_seleccionada.replace(" ", "_").lower()}_{nombre_plantilla_seleccionada.replace(" ", "_").lower()}.csv',
                        mime='text/csv',
                    )
            else:
                st.info(
                    "Selecciona una categoría y plantilla para generar la vista previa."
                )

# --- PIE DE PÁGINA ---
st.markdown("---")
st.info(
    "Esta maravillosa, caótica y probablemente sobrecafeinada plataforma ha sido realizada por Johnsito ✨ 😊"
)
