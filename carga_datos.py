import pandas as pd
import gspread
import streamlit as st # Importar streamlit para usar st.write y st.error/stop
from oauth2client.service_account import ServiceAccountCredentials
from collections import Counter
# Asegúrate de que estas funciones de limpieza estén disponibles en utils.limpieza
# Es posible que necesites importar st en utils/limpieza.py si esas funciones lo usan.
from utils.limpieza import calcular_dias_respuesta, estandarizar_avatar

def cargar_y_limpiar_datos():
    # Autenticación y conexión a Google Sheets
    # Asegúrate de tener el archivo credenciales.json en la ubicación correcta
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
        client = gspread.authorize(creds)
    except FileNotFoundError:
        st.error("Error: El archivo 'credenciales.json' no se encontró.")
        st.info("Asegúrate de tener el archivo de credenciales de Google Sheets en la misma carpeta que la aplicación.")
        st.stop() # Detenemos la ejecución si no se encuentran las credenciales
    except Exception as e:
        st.error(f"Error al autenticar con Google Sheets: {e}")
        st.stop()


    # Abrir hoja por URL
    # Asegúrate de que esta URL sea la correcta para tu hoja de cálculo
    try:
        # Abre la hoja por URL y selecciona la primera hoja (sheet1)
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1h-hNu0cH0W_CnGx4qd3JvF-Fg9Z18ZyI9lQ7wVhROkE/edit#gid=0").sheet1
        raw_data = sheet.get_all_values()
        headers = raw_data[0]
        rows = raw_data[1:]
    except Exception as e:
        st.error(f"Error al leer la hoja de cálculo de Google Sheets: {e}")
        st.info("Verifica la URL de la hoja, los permisos de la cuenta de servicio y la conexión a internet.")
        st.stop()


    def make_unique(headers):
        counts = Counter()
        new_headers = []
        for h in headers:
            h = h.strip()
            counts[h] += 1
            if counts[h] == 1:
                new_headers.append(h)
            else:
                # Añadir un sufijo si el encabezado está duplicado
                new_headers.append(f"{h}_{counts[h]-1}")
        return new_headers

    headers = make_unique(headers)
    df = pd.DataFrame(rows, columns=headers)

    # La validación del nombre de la columna ocurrirá justo después de mostrar las columnas.
    nombre_columna_fecha_invite = "Fecha de Invite" # Nombre esperado. Lo corregiremos si es necesario.

    if nombre_columna_fecha_invite in df.columns:
        # Creamos el DataFrame base manteniendo solo las filas donde la representación
        # de texto de la columna de fecha, sin espacios al inicio/fin, no está vacía.
        df_base = df[df[nombre_columna_fecha_invite].astype(str).str.strip() != ""].copy()

        # Optional: Add debugging for the size of df_base
        # st.write(f"DEBUG: Filas en df_base (después del filtro '{nombre_columna_fecha_invite}' no vacía texto): {len(df_base)}")

        # Convertimos la columna de fecha a datetime *después* del filtro de texto no vacío.
        # Los valores que no se puedan convertir resultarán en NaT.
        df_base[nombre_columna_fecha_invite] = pd.to_datetime(df_base[nombre_columna_fecha_invite], format='%d/%m/%Y', errors="coerce")


        if df_base.empty:
             st.warning(f"El DataFrame base está vacío después de filtrar por '{nombre_columna_fecha_invite}' no vacía.")

    else:
        st.error(f"¡ERROR! La columna '{nombre_columna_fecha_invite}' no se encontró al cargar los datos.")
        st.info("Por favor, verifica el nombre de la columna de la fecha de invitación en la salida de debugging.")
        st.stop()


    # --- AHORA REALIZAR LA LIMPIEZA Y CONVERSIÓN DE FECHA EN df_base ---

    # Limpieza y estandarización de 'Avatar' en el DataFrame base
    # No eliminamos filas basadas en el contenido de Avatar aquí
    if "Avatar" in df_base.columns:
         # Asegúrate de que estandarizar_avatar esté definida en utils.limpieza
         df_base["Avatar"] = df_base["Avatar"].astype(str).str.strip().str.title()
         df_base["Avatar"] = df_base["Avatar"].replace({"Jonh Fenner": "John Bermúdez", "Jonh Bermúdez": "John Bermúdez", "Jonh": "John Bermúdez", "John Fenner": "John Bermúdez"})
         # REMOVIMOS: df_base = df_base[~df_base["Avatar"].isin(["", "Nan", "None", "Sin Avatar"])]


    # Limpieza de otras columnas (excluimos la columna de fecha de este loop)
    columnas_a_limpiar = [
        "¿Invite Aceptada?", "Sesion Agendada?", "Respuesta Primer Mensaje",
        "Respuestas Subsecuentes", "Fecha Sesion",
        # Asegúrate de que el nombre de la columna de fecha NO esté en esta lista
    ]
    # Filtramos la lista columnas_a_limpiar para asegurarnos de que la columna de fecha no esté incluida
    columnas_a_limpiar_filtrada = [col for col in columnas_a_limpiar if col != nombre_columna_fecha_invite]


    for col in columnas_a_limpiar_filtrada:
        if col in df_base.columns:
            # Llenamos NaN/cadenas vacías/solo espacios con "No" para estas columnas
            df_base[col] = df_base[col].fillna("No").replace(r'^\s*$', "No", regex=True)

    # La conversión de fecha a datetime ya se hizo antes del debug de NaT

    # df_base ahora es el conjunto de datos filtrado por "Fecha de Invite" no vacía como texto,
    # con otras columnas limpiadas y la columna de fecha convertida (con NaT para errores).
    # Esta es la base que se pasará a cargar_y_procesar_datos.
    return df_base


def cargar_y_procesar_datos(df):
    # Esta función realiza procesamiento adicional en el DataFrame base.
    # df aquí es el df_base retornado por cargar_y_limpiar_datos.
    # Asegúrate de que calcular_dias_respuesta esté definida en utils.limpieza
    # Si calcular_dias_respuesta usa columnas como Fecha de Invite o Fecha Primer Mensaje,
    # operará en el df_base que ya tiene esas columnas procesadas.
    try:
        # Asegúrate de que calcular_dias_respuesta no espere la columna con el nombre exacto "Fecha de Invite"
        # Si usa el nombre literal, también deberás corregirlo allí.
        df = calcular_dias_respuesta(df) # Esta función necesita implementación si no la tiene
    except Exception as e:
         st.warning(f"Error al ejecutar calcular_dias_respuesta: {e}")
         # Si esta función falla, retornamos el df como está hasta ahora
         pass # Si calcular_dias_respuesta no está implementada o falla, simplemente seguimos

    return df