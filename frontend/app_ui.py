import streamlit as st
import requests
import json
from typing import Dict, Any

# Importar lista de clientes desde el backend (si existe)
try:
    from backend.utils.constants import CLIENT_LIST
except ImportError:
    CLIENT_LIST = [
        "TechFin Solutions", 
        "Retail Express", 
        "LegalVerify Corp", 
        "Logística Rápida", 
        "Recursos Humanos S.A.",
        "Marketing Cloud E-commerce",
        "Global",
        "HealthSecure",
        "Banco del Mañana",
        "Telecom Innova",
        "Otro Cliente"
    ]

# Configuración general de Streamlit
st.set_page_config(
    page_title="Clasificador de Tickets por IA",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL local del backend
API_URL = "https://ticket-classifier-ia.onrender.com/classify"

# colores por prioridad
PRIORITY_COLORS = {
    "P1": "#dc3545",
    "P2": "#ffc107",
    "P3": "#007bff",
    "P4": "#28a745",
}

# FUNCIÓN: Llamado al backend
def classify_ticket_api(ticket_data: Dict[str, Any]):
    try:
        response = requests.post(API_URL, json=ticket_data)

        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", "Error desconocido.")
            except:
                detail = "El backend devolvió una respuesta no JSON."
            st.error(f"Error HTTP {response.status_code}: {detail}")
            return None

        return response.json()

    except requests.exceptions.ConnectionError:
        st.error(f"No se pudo conectar con el backend en {API_URL}. Inicia FastAPI primero.")
        return None
    except Exception as e:
        st.error(f"Error inesperado al conectar con backend: {str(e)}")
        return None


# FUNCIÓN: Mostrar los resultados
def display_classification_result(result: Dict[str, Any]):
    st.subheader("Resultados de la Clasificación")

    col1, col2, col3, col4 = st.columns(4)

    priority = result.get("prioridad", "N/A")
    urgency = result.get("urgencia", "N/A")
    sla = result.get("sla_objetivo", "N/A")
    confidence = f"{result.get('nivel_confianza', 0.0):.1f}%"

    color = PRIORITY_COLORS.get(priority, "gray")

    # Prioridad visual
    col1.markdown(
        f'''
        <div style="background-color: {color}; padding: 10px; border-radius: 8px; color: white; text-align:center;">
            <h2 style="margin:0;">{priority}</h2>
            <small>Prioridad</small>
        </div>
        ''',
        unsafe_allow_html=True
    )

    col2.metric("Urgencia", urgency)
    col3.metric("SLA Objetivo", sla)
    col4.metric("Confianza", confidence)

    st.markdown("---")

    st.info(f"**Categoría Sugerida:** {result.get('categoria_sugerida', 'N/A')}")
    st.code(
        f"Tiempo Estimado de Resolución (histórico RAG): {result.get('tiempo_estimado_resolucion', 'N/A')}",
        language='text'
    )

    with st.expander("Justificación y Evidencia RAG"):
        st.markdown("### 🧠 Justificación del Modelo")
        st.write(result.get("justificacion_modelo", "Sin justificación."))

        st.markdown("### 📚 Evidencia RAG Utilizada")
        rag_docs = result.get("documentos_rag_usados") or []

        if rag_docs:
            rag_table_data = [
                {
                    "ID": doc.get("ticket_id"),
                    "Título": doc.get("titulo"),
                    "Categoría": doc.get("categoria"),
                    "Similitud": f"{doc.get('similitud_score', 0):.2f}",
                    "Solución Histórica": doc.get("solucion_resumen", ""),
                }
                for doc in rag_docs
            ]
            st.dataframe(rag_table_data, use_container_width=True)
        else:
            st.warning("No se encontró evidencia RAG relevante.")

    st.markdown("---")

    # Feedback Loop
    st.subheader("🔄 Feedback Loop")

    colA, colB = st.columns(2)

    if colA.button("Confirmar Clasificación", use_container_width=True):
        st.session_state["feedback_status"] = "CONFIRMADO"
        st.success("Clasificación confirmada.")

    if colB.button("Corregir Clasificación", use_container_width=True):
        st.session_state["feedback_status"] = "CORREGIDO"
        st.warning("Clasificación marcada para corrección.")

    st.sidebar.metric("Estado Feedback", st.session_state.get("feedback_status", "Pendiente"))



# APLICACIÓN PRINCIPAL
def main():
    st.title("Sistema Inteligente de Clasificación de Tickets")
    st.markdown("---")

    if "classification_result" not in st.session_state:
        st.session_state["classification_result"] = None
    if "feedback_status" not in st.session_state:
        st.session_state["feedback_status"] = "Pendiente"

    # SIDEBAR: Formulario Ticket
    with st.sidebar:
        st.header("📝 Radicar Nuevo Ticket")

        with st.form(key="ticket_form"):
            titulo = st.text_input("Título del Incidente")
            descripcion = st.text_area("Descripción Detallada", height=150)
            cliente = st.selectbox("Cliente Afectado", CLIENT_LIST)

            c1, c2 = st.columns(2)
            with c1:
                porcentaje = st.slider("% Usuarios Afectados", 0, 100, 10, 5)

            with c2:
                tipo_incidente = st.selectbox(
                    "Tipo de Incidente",
                    [
                        "Disponibilidad",
                        "Performance",
                        "Cambio funcional",
                        "Integración país",
                        "Seguridad",
                        "UI",
                        "Notificaciones",
                        "Reportes",
                        "Acceso",
                        "Facturación",
                        "Personalización",
                        "Webhooks",
                        "SDK móvil",
                        "Consulta"
                    ]
                )

            info_ctx = st.text_area("Información Contextual (Opcional)", height=50)
            enviar = st.form_submit_button("🚀 Clasificar Ticket")

        if enviar:
            if not titulo or not descripcion:
                st.error("El título y la descripción son obligatorios.")
            else:
                payload = {
                    "titulo": titulo,
                    "descripcion": descripcion,
                    "cliente_afectado": cliente,
                    "porcentaje_afectado": porcentaje,
                    "tipo_incidente": tipo_incidente,
                    "informacion_contextual": info_ctx if info_ctx.strip() else None,
                }

                with st.spinner("Clasificando ticket con IA + RAG..."):
                    result = classify_ticket_api(payload)

                if result:
                    st.session_state["classification_result"] = result
                    st.session_state["feedback_status"] = "Pendiente"
                    st.rerun()

    # Mostrar resultado
    if st.session_state["classification_result"]:
        display_classification_result(st.session_state["classification_result"])
    else:
        st.info("Radica un ticket desde la barra lateral para comenzar.")


if __name__ == "__main__":
    main()
