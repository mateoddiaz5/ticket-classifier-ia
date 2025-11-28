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
            "ERES UN SISTEMA ESTRICTO DE CLASIFICACIÓN DE TICKETS.\n"
            "DEBES ASIGNAR LA PRIORIDAD EXCLUSIVAMENTE SEGÚN EL PORCENTAJE DE AFECTACIÓN, "
            "USANDO LA SIGUIENTE TABLA, SIN EXCEPCIONES:\n\n"

            "TABLA OFICIAL DE PRIORIDAD:\n"
            "   - Si AFECTACIÓN es entre 81% y 100% → PRIORIDAD = P1\n"
            "   - Si AFECTACIÓN es entre 51% y 80%  → PRIORIDAD = P2\n"
            "   - Si AFECTACIÓN es entre 21% y 50%  → PRIORIDAD = P3\n"
            "   - Si AFECTACIÓN es entre 0%  y 20%  → PRIORIDAD = P4\n\n"

            "INTERPRETA LA AFECTACIÓN DE ESTA FORMA:\n"
            "   - 'entre X e Y' significa INCLUYENDO ambos limites.\n"
            "   - Si el porcentaje está EXACTAMENTE en un límite, usa la categoría más alta.\n\n"

            "EJEMPLOS PARA QUE NO TE EQUIVOQUES:\n"
            "   - 100%, 95%, 82% → siempre P1.\n"
            "   - 80%, 75%, 60%, 55%, 51% → siempre P2.\n"
            "   - 50%, 40%, 25%, 21% → siempre P3.\n"
            "   - 20%, 10%, 5%, 0% → siempre P4.\n\n"

            "ESTA TABLA ES OBLIGATORIA. NO PUEDES CAMBIAR LA PRIORIDAD POR NINGÚN MOTIVO.\n"
            "NO IMPORTA EL CLIENTE, EL RAG, NI LA DESCRIPCIÓN: "
            "LA PRIORIDAD SIEMPRE SE DETERMINA SÓLO CON EL PORCENTAJE DE AFECTACIÓN.\n\n"

            "DEVUELVE SOLO EL JSON FINAL.\n\n"
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
            "IMPORTANTE SOBRE TIEMPO ESTIMADO:\n"
            "- El campo 'tiempo_estimado_resolucion' NO ES el SLA.\n"
            "- Debe calcularse usando EXCLUSIVAMENTE los tiempos históricos de los tickets recuperados por RAG.\n"
            "- Lee los tiempos de resolución que aparecen en los tickets históricos (por ejemplo: '45 minutos', '3 horas', "
            "'5 horas', '2 días hábiles') y genera un tiempo estimado coherente con esos valores (misma unidad de medida y "
            "mismo orden de magnitud).\n"
            "- Si NO hay evidencia histórica relevante (RAG vacío o poco similar), recién ahí puedes usar el SLA como "
            "referencia aproximada.\n"
            "- Nunca inventes tiempos genéricos como '40-60 minutos' si los históricos hablan en horas o días.\n\n"
        )

        system_prompt += (
        "IMPORTANTE SOBRE 'sla_objetivo':\n"
        "- Debe corresponder EXACTAMENTE a la prioridad final asignada:\n"
        "    * P1 → 1 hora\n"
        "    * P2 → 4 horas\n"
        "    * P3 → 24 horas\n"
        "    * P4 → 72 horas\n"
        "- NO inventes otros valores.\n\n"
        )

        system_prompt += (
            "--- FORMATO DE RESPUESTA (JSON) ---\n"
            "Debes cumplir EXACTAMENTE con el siguiente esquema JSON:\n"
            f"{output_schema_json}\n"
        )

        return system_prompt
