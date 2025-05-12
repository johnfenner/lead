import pandas as pd

def limpiar_valor_kpi(val):
    return str(val).strip().lower() if pd.notna(val) else "no"

def limpiar_nombre_completo(nombre, apellido):
    return (str(nombre).strip() + " " + str(apellido).strip()).lower()

def estandarizar_avatar(avatar):
    avatar = str(avatar).strip().title()
    equivalencias = {
        "Jonh Fenner": "John Bermúdez",
        "Jonh Bermúdez": "John Bermúdez",
        "Jonh": "John Bermúdez",
        "John Fenner": "John Bermúdez"
    }
    return equivalencias.get(avatar, avatar)

def calcular_dias_respuesta(df):
    return df


