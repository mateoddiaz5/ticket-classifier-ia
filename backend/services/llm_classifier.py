import json
from typing import List

from openai import OpenAI

from backend.config import settings
from backend.models.input_schema import TicketInput
from backend.models.output_schema import TicketClassification, RAGDocument
from backend.services.rag_engine import RAGEngine
from backend.services.prompt_manager import PromptManager


class LLMClassifier:
    """
    Orquesta el flujo completo:
    RAG → Prompt → OpenAI LLM → Validación → Respuesta final
    """

    def __init__(self):
        # Inicializar motores dependientes
        self.rag_engine = RAGEngine()
        self.prompt_manager = PromptManager()

        # Inicializar cliente OpenAI
        try:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            raise Exception(f"ERROR: No se pudo inicializar OpenAI: {e}")

        # Cargar configuración del modelo
        self.llm_model = settings.LLM_MODEL

        # Asegurar que ChromaDB está indexado
        self.rag_engine.index_data()


    def classify_ticket(self, ticket_input: TicketInput) -> TicketClassification:
        """
        Proceso completo para clasificar un ticket entrante.
        """

        # 1 — Buscar RAG con query más completa
        search_query = (
            f"Título: {ticket_input.titulo}. "
            f"Descripción: {ticket_input.descripcion}. "
            f"Tipo de incidente: {ticket_input.tipo_incidente}. "
            f"Afectación: {ticket_input.porcentaje_afectado}%. "
            "Dominio técnico esperado: verificación de antecedentes, AML, módulo de antecedentes, performance, latencia, tiempo de respuesta."
        )


        rag_results: List[RAGDocument] = self.rag_engine.retrieve_documents(
            query_text=search_query,
            k=5  # mejor recall
        )

        # 2 — Obtener esquema JSON del output
        schema_dict = TicketClassification.model_json_schema()
        output_schema_json = json.dumps(schema_dict, indent=2)

        # 3 — Construir prompt
        system_prompt = self.prompt_manager.generate_prompt(
            ticket_input=ticket_input,
            rag_results=rag_results,
            output_schema_json=output_schema_json
        )

        # 4 — Llamar al modelo OpenAI
        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt}
                ],
                response_format={"type": "json_object"}
            )

            json_response = response.choices[0].message.content

            # 5 — Validación estricta con Pydantic
            try:
                classification_result = TicketClassification.model_validate_json(json_response)
            except Exception as e:
                raise Exception(f"JSON inválido recibido del modelo: {json_response}")

            # 6 — Agregar RAG al resultado
            classification_result.documentos_rag_usados = rag_results

            return classification_result

        except Exception as e:
            raise Exception(f"Error en la clasificación LLM: {e}")
