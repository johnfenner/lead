# ------------------ mensajes_streamlit.py ------------------
# mensajes_streamlit.py

def clasificar_por_proceso(proceso):
    if not isinstance(proceso, str):
        return "General"
    proceso = proceso.strip().lower()
    if "hire" in proceso or "h2r" in proceso or "reclutamiento" in proceso or "rh" in proceso:
        return "H2R"
    elif "procure" in proceso or "p2p" in proceso or "compras" in proceso:
        return "P2P"
    elif "order" in proceso or "cobranza" in proceso or "o2c" in proceso:
        return "O2C"
    else:
        return "General"
