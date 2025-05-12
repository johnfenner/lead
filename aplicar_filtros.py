import pandas as pd

def aplicar_filtros(
    df,
    filtro_fuente_lista, filtro_proceso, filtro_pais, filtro_industria, filtro_avatar,
    filtro_prospectador, filtro_invite_aceptada_simple, filtro_sesion_agendada,
    fecha_ini, fecha_fin
):
    df_filtrado = df.copy()

    if "¿Quién Prospecto?" in df_filtrado.columns:
        df_filtrado["¿Quién Prospecto?"] = df_filtrado["¿Quién Prospecto?"].replace("", pd.NA)

    if filtro_fuente_lista and "– Todos –" not in filtro_fuente_lista:
        df_filtrado = df_filtrado[df_filtrado["Fuente de la Lista"].isin(filtro_fuente_lista)]

    if filtro_proceso and "– Todos –" not in filtro_proceso:
        df_filtrado = df_filtrado[df_filtrado["Proceso"].isin(filtro_proceso)]

    if filtro_pais and "– Todos –" not in filtro_pais:
        df_filtrado = df_filtrado[df_filtrado["Pais"].isin(filtro_pais)]

    if filtro_industria and "– Todos –" not in filtro_industria:
        df_filtrado = df_filtrado[df_filtrado["Industria"].isin(filtro_industria)]

    if filtro_avatar and "– Todos –" not in filtro_avatar:
        df_filtrado = df_filtrado[df_filtrado["Avatar"].isin(filtro_avatar)]

    if filtro_invite_aceptada_simple != "– Todos –":
        df_filtrado = df_filtrado[
            df_filtrado["¿Invite Aceptada?"]
            .apply(lambda x: str(x).strip().lower() == filtro_invite_aceptada_simple.strip().lower())
        ]

    if fecha_ini and fecha_fin:
        df_filtrado = df_filtrado[
            (df_filtrado["Fecha de Invite"].dt.date >= fecha_ini) &
            (df_filtrado["Fecha de Invite"].dt.date <= fecha_fin)
        ]

    if filtro_sesion_agendada != "– Todos –":
        df_filtrado = df_filtrado[
            df_filtrado["Sesion Agendada?"]
            .apply(lambda x: str(x).strip().lower() == filtro_sesion_agendada.strip().lower())
        ]

    if filtro_prospectador and "– Todos –" not in filtro_prospectador:
        df_filtrado = df_filtrado[df_filtrado["¿Quién Prospecto?"].isin(filtro_prospectador)]

    return df_filtrado
