import streamlit as st
import datetime
import pandas as pd


# Función para resetear el estado de los filtros a sus valores por defecto
def reset_filters_state():
    """Resets all filter keys in st.session_state to their default values."""
    st.session_state["filtro_fuente_lista"] = ["– Todos –"]
    st.session_state["filtro_proceso"] = ["– Todos –"]
    st.session_state["filtro_pais"] = ["– Todos –"]
    st.session_state["filtro_industria"] = ["– Todos –"]
    st.session_state["filtro_avatar"] = ["– Todos –"]
    st.session_state["filtro_prospectador"] = ["– Todos –"]
    st.session_state["filtro_invite_aceptada_simple"] = "– Todos –"
    st.session_state["filtro_sesion_agendada"] = "– Todos –"
    st.session_state["busqueda"] = ""
    st.session_state["fecha_ini"] = None
    st.session_state["fecha_fin"] = None
    st.toast("Filtros reiniciados ✅")


# Función genérica para crear selectores múltiples (Multiselect) - Usa st.multiselect
def crear_multiselect(df, columna, etiqueta, key):
    """Creates a multiselect widget for a given column, managing state with key."""
    if key not in st.session_state:
        st.session_state[key] = ["– Todos –"]

    options = ["– Todos –"]
    if columna in df.columns and not df[columna].empty:
        valores_data = sorted(df[columna].dropna().astype(str).unique())
        options = ["– Todos –"] + valores_data

    current_value = st.session_state[key]
    valid_value = [val for val in current_value if val in options]

    if len(valid_value) != len(current_value):
        st.session_state[key] = ["– Todos –"]

    selected_value = st.multiselect(  # Usar st.multiselect
        etiqueta, options, key=key)
    return st.session_state[key]


# Función genérica para crear selectores simples (Selectbox) - Usa st.selectbox
def crear_selectbox(df, columna, etiqueta, key):
    """Creates a selectbox widget for a given column, normalizing options and managing state with key."""
    if key not in st.session_state:
        st.session_state[key] = "– Todos –"

    options = ["– Todos –"]
    if columna in df.columns and not df[columna].empty:
        valores_unicos_normalizados = df[columna].dropna().astype(
            str).str.strip().str.title().unique()
        valores_ordenados_para_filtro = sorted(
            valores_unicos_normalizados.tolist())
        options = ["– Todos –"] + valores_ordenados_para_filtro

    widget_value = st.session_state[key]

    if widget_value not in options:
        st.session_state[key] = "– Todos –"
        widget_value = st.session_state[key]

    index_valor = options.index(widget_value) if widget_value in options else 0

    return st.selectbox(  # Usar st.selectbox
        etiqueta, options, index=index_valor, key=key)


# --- FUNCIÓN PRINCIPAL PARA MOSTRAR FILTROS ---


def mostrar_filtros_sidebar(df):
    """Displays all filter widgets in the sidebar using columns for horizontal grouping."""
    st.sidebar.header("🎯 Filtros de Búsqueda")

    # Inicializar estado si no existe (esto ya estaba, lo mantenemos)
    if "filtro_fuente_lista" not in st.session_state:
        st.session_state["filtro_fuente_lista"] = ["– Todos –"]
    if "filtro_proceso" not in st.session_state:
        st.session_state["filtro_proceso"] = ["– Todos –"]
    if "filtro_pais" not in st.session_state:
        st.session_state["filtro_pais"] = ["– Todos –"]
    if "filtro_industria" not in st.session_state:
        st.session_state["filtro_industria"] = ["– Todos –"]
    if "filtro_avatar" not in st.session_state:
        st.session_state["filtro_avatar"] = ["– Todos –"]
    if "filtro_prospectador" not in st.session_state:
        st.session_state["filtro_prospectador"] = ["– Todos –"]
    if "filtro_invite_aceptada_simple" not in st.session_state:
        st.session_state["filtro_invite_aceptada_simple"] = "– Todos –"
    if "filtro_sesion_agendada" not in st.session_state:
        st.session_state["filtro_sesion_agendada"] = "– Todos –"
    if "busqueda" not in st.session_state: st.session_state["busqueda"] = ""
    if "fecha_ini" not in st.session_state:
        st.session_state["fecha_ini"] = None
    if "fecha_fin" not in st.session_state:
        st.session_state["fecha_fin"] = None

    st.sidebar.subheader("Filtros de Origen")
    # Agrupar filtros de origen en columnas (sin botones individuales de reset)
    # Dividimos los 6 filtros en 3 filas de 2 columnas cada una
    col1_1, col1_2 = st.sidebar.columns(2)
    with col1_1:
        filtro_fuente_lista = crear_multiselect(df, "Fuente de la Lista",
                                                "Fuente de la Lista",
                                                "filtro_fuente_lista")
    with col1_2:
        filtro_proceso = crear_multiselect(df, "Proceso", "Proceso",
                                           "filtro_proceso")

    col2_1, col2_2 = st.sidebar.columns(2)
    with col2_1:
        filtro_pais = crear_multiselect(df, "Pais", "País", "filtro_pais")
    with col2_2:
        filtro_industria = crear_multiselect(df, "Industria", "Industria",
                                             "filtro_industria")

    col3_1, col3_2 = st.sidebar.columns(2)
    with col3_1:
        filtro_avatar = crear_multiselect(df, "Avatar", "Avatar",
                                          "filtro_avatar")
    with col3_2:
        filtro_prospectador = crear_multiselect(df, "¿Quién Prospecto?",
                                                "¿Quién Prospectó?",
                                                "filtro_prospectador")

    st.sidebar.subheader("Filtros de Interacción")
    # Agrupar filtros de interacción en columnas (2 columnas)
    col_invite, col_sesion = st.sidebar.columns(2)
    with col_invite:
        filtro_invite_aceptada_simple = crear_selectbox(
            df, "¿Invite Aceptada?", "¿Invite Aceptada?",
            "filtro_invite_aceptada_simple")
    with col_sesion:
        filtro_sesion_agendada = crear_selectbox(df, "Sesion Agendada?",
                                                 "¿Sesión Agendada?",
                                                 "filtro_sesion_agendada")

    st.sidebar.subheader("Filtro de Fechas")
    # Agrupar filtros de fecha en columnas (2 columnas)
    col_f1, col_f2 = st.sidebar.columns(2)

    fecha_min_data = None
    fecha_max_data = None
    if "Fecha de Invite" in df.columns and pd.api.types.is_datetime64_any_dtype(
            df["Fecha de Invite"]):
        valid_dates = df["Fecha de Invite"].dropna()
        if not valid_dates.empty:
            fecha_min_data = valid_dates.min().date()
            fecha_max_data = valid_dates.max().date()

    with col_f1:
        fecha_ini = st.date_input(  # Usar st.date_input
            "Desde",
            value=st.session_state.get("fecha_ini", None),
            format='DD/MM/YYYY',
            key="fecha_ini",
            min_value=fecha_min_data,
            max_value=fecha_max_data)
    with col_f2:
        fecha_fin = st.date_input(  # Usar st.date_input
            "Hasta",
            value=st.session_state.get("fecha_fin", None),
            format='DD/MM/YYYY',
            key="fecha_fin",
            min_value=fecha_min_data,
            max_value=fecha_max_data)

    st.sidebar.subheader("Búsqueda")
    # El campo de búsqueda puede ir solo debajo de los filtros agrupados
    busqueda = st.sidebar.text_input(
        "🔎 Buscar (Nombre, Apellido, Empresa, Puesto)",
        value=st.session_state.get("busqueda", ""),
        placeholder="Ingrese término y presione Enter",
        key="busqueda")

    # El botón principal "Limpiar Todos los Filtros" para resetear todo se mantiene
    st.sidebar.button("🧹 Limpiar Todos los Filtros",
                      on_click=reset_filters_state)

    # La sentencia de retorno permanece sin cambios
    return (st.session_state.get("filtro_fuente_lista", ["– Todos –"]),
            st.session_state.get("filtro_proceso", ["– Todos –"]),
            st.session_state.get("filtro_pais", ["– Todos –"]),
            st.session_state.get("filtro_industria", ["– Todos –"]),
            st.session_state.get("filtro_avatar", ["– Todos –"]),
            st.session_state.get("filtro_prospectador", ["– Todos –"]),
            st.session_state.get("filtro_invite_aceptada_simple", "– Todos –"),
            st.session_state.get("filtro_sesion_agendada", "– Todos –"),
            st.session_state.get("fecha_ini", None),
            st.session_state.get("fecha_fin",
                                 None), st.session_state.get("busqueda", ""))
