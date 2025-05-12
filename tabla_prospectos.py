import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import io

def mostrar_tabla_filtrada(df_tabla):
    st.markdown("### 📄 Prospectos Filtrados")

    columnas_excel = df_tabla.columns.tolist()
    columnas_presentes = [col for col in columnas_excel if col in df_tabla.columns]
    tabla_final = df_tabla[columnas_presentes].copy()

    gb = GridOptionsBuilder.from_dataframe(tabla_final)
    gb.configure_default_column(resizable=True, sortable=True, filter='agTextColumnFilter')

    if "Fecha Primer Mensaje" in columnas_presentes:
        gb.configure_column("Fecha Primer Mensaje", cellRenderer=f"""
            function(params) {{
                if (params.value == null || params.value == '' || params.value.toLowerCase() == 'no') {{
                    return '<span style="color: red;">Sin Respuesta Inicial</span>';
                }} else {{
                    return params.value;
                }}
            }}
        """)

    if "Sesion Agendada?" in columnas_presentes:
        gb.configure_column("Sesion Agendada?", cellRenderer=f"""
            function(params) {{
                if (params.value == null || params.value.toLowerCase() == 'no') {{
                    return '<span style="color: orange;">Sesión No Agendada</span>';
                }} else {{
                    return params.value;
                }}
            }}
        """)

    gridOptions = gb.build()

    AgGrid(
        tabla_final,
        gridOptions=gridOptions,
        height=400,
        theme="alpine",
        enable_enterprise_modules=False,
    )

    output = io.BytesIO()
    tabla_final.to_excel(output, index=False, engine='openpyxl')
    st.download_button("⬇️ Descargar Excel", output.getvalue(), "prospectos_filtrados.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
