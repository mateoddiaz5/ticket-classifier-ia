from typing import List

from backend.utils.constants import SLA_MATRIX, PRIORITY_MAPPING, CLIENT_BUSINESS_IMPACT
from backend.models.input_schema import TicketInput
from backend.models.output_schema import RAGDocument
from backend.config import settings, DATA_DIR


class PromptManager:
    """
    Genera el prompt del sistema incluyendo:
    - Reglas de negocio
    - Evidencia RAG
    - Ticket del usuario
    - Esquema JSON requerido
    """

    def _format_rag_documents(self, rag_docs: List[RAGDocument]) -> str:
        if not rag_docs or all(doc.similitud_score < 0.5 for doc in rag_docs):
            return (
                "No se encontraron tickets relevantes. "
                "No inventes evidencia histórica. Clasifica solo con las reglas de negocio."
            )

        formatted_str = "--- EVIDENCIA DE TICKETS HISTÓRICOS (RAG) ---\n"
        for doc in rag_docs:
            formatted_str += (
                f"- ID: {doc.ticket_id} (Similitud: {doc.similitud_score:.2f})\n"
                f"  Título: {doc.titulo}\n"
                f"  Categoría: {doc.categoria}\n"
                f"  Solución Histórica: {doc.solucion_resumen}\n"
                f"  --------------------------------------------------\n"
            )
        return formatted_str

    def _generate_business_rules(self) -> str:
        rules = "--- REGLAS DE NEGOCIO Y SLA (Matriz ANS) ---\n"

        rules += "\n## REGLAS BÁSICAS DE PRIORIDAD (ANS):\n"
        for urgency, sla_data in SLA_MATRIX.items():
            level = PRIORITY_MAPPING.get(urgency, "P4")
            rules += (
                f"- **{level} ({urgency})**: "
                f"Solución en {sla_data['solucion']}. "
                f"1ª Respuesta: {sla_data['primera_respuesta']}. "
                f"Asistencia: {sla_data['asistencia']}.\n"
            )

        rules += "\n## BOOSTS DE PRIORIDAD POR CLIENTE:\n"
        rules += "Si un cliente está en riesgo de churn o con impacto crítico, aumenta la prioridad.\n"

        for client, impact in CLIENT_BUSINESS_IMPACT.items():
            insights = []
            if impact.get("Estado") == "En Riesgo de Churn":
                insights.append("Puede subir prioridad si es P3/P4")
            if impact.get("Impacto_Critico"):
                insights.append("Impacto crítico: probabilidad de P1 o P2")

            if insights:
                rules += f"- {client} (${impact['MRR']} MRR): {', '.join(insights)}\n"

        return rules

    def generate_prompt(self, ticket_input: TicketInput, rag_results: List[RAGDocument], output_schema_json: str) -> str:

        system_prompt = (
            "ERES UN INGENIERO DE SOPORTE EXPERTO Y CLASIFICADOR DE TICKETS.\n"
            "Usa estrictamente las reglas de negocio y la evidencia histórica (RAG).\n"
            "DEVUELVE ÚNICAMENTE el JSON final, SIN texto adicional.\n\n"
        )

        system_prompt += self._generate_business_rules() + "\n"

        system_prompt += (
            "--- TICKET NUEVO ---\n"
            f"Título: {ticket_input.titulo}\n"
            f"Descripción: {ticket_input.descripcion}\n"
            f"Cliente: {ticket_input.cliente_afectado}\n"
            f"Afectación: {ticket_input.porcentaje_afectado}%\n"
            f"Tipo de Incidente: {ticket_input.tipo_incidente}\n\n"
        )

        system_prompt += self._format_rag_documents(rag_results) + "\n"

        system_prompt += (
            "IMPORTANTE:\n"
            "- El campo 'tiempo_estimado_resolucion' NO ES el SLA.\n"
            "- Debe calcularse usando EXCLUSIVAMENTE los tiempos históricos recuperados por el RAG.\n"
            "- Si los documentos históricos muestran tiempos entre 40 y 60 minutos, el estimado debe estar en ese rango.\n"
            "- Solo usar el SLA si NO existe evidencia histórica (RAG=vacío o similitud < 0.5).\n"
            "- Nunca inventes tiempos que no se basen en evidencia.\n\n"
        )

        system_prompt += (
            "--- FORMATO DE RESPUESTA (JSON) ---\n"
            "Debes cumplir EXACTAMENTE con el siguiente esquema JSON:\n"
            f"{output_schema_json}\n"
        )

        return system_prompt
