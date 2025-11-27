from typing import List, Optional
from pydantic import BaseModel, Field

# Esquema para representar la información de un ticket histórico recuperado por RAG
class RAGDocument(BaseModel):
    """Estructura de la evidencia histórica usada para la justificación."""
    ticket_id: str
    titulo: str
    categoria: str
    solucion_resumen: str
    similitud_score: float = Field(..., ge=0.0, le=1.0)

class TicketClassification(BaseModel):
    """
    Define el esquema de la clasificación automática de tickets (RF2, RF5).
    Este es el contrato de respuesta JSON del LLM.
    """
    prioridad: str = Field(..., description="Prioridad del ticket (P1, P2, P3, P4).")
    urgencia: str = Field(..., description="Nivel de urgencia (Crítica, Alta, Media, Baja).")

    sla_primera_respuesta: str = Field(..., description="Tiempo máximo para la primera respuesta.")
    sla_asistencia: str = Field(..., description="Tiempo máximo para iniciar el trabajo.")
    sla_solucion: str = Field(..., description="Tiempo objetivo para la solución final.")

    categoria_sugerida: str = Field(..., description="Categoría técnica sugerida.")
    tiempo_estimado_resolucion: str = Field(..., description="Tiempo estimado de resolución.")
    nivel_confianza: float = Field(..., ge=0.0, le=100.0, description="Nivel de confianza del modelo.")

    justificacion_modelo: str = Field(..., description="Justificación del modelo.")
    
    # Justificacion y evidencias de acuerdo a los documentos historicos usados por RAG
    documentos_rag_usados: Optional[List[RAGDocument]] = Field(
        default=None,
        description="Documentos históricos utilizados por RAG."
    )
