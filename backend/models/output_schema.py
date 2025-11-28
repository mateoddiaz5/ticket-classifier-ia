from typing import List, Optional
from pydantic import BaseModel, Field

# Evidencia RAG
class RAGDocument(BaseModel):
    """Estructura de cada ticket histórico usado como evidencia."""
    ticket_id: str
    titulo: str
    categoria: str
    solucion_resumen: str
    similitud_score: float = Field(..., ge=0.0, le=1.0)


class TicketClassification(BaseModel):
    """
    Esquema final de respuesta del modelo LLM.
    Este es el contrato JSON definitivo.
    """

    # Clasificación principal
    prioridad: str = Field(..., description="P1, P2, P3, P4")
    urgencia: str = Field(..., description="Crítica, Alta, Media, Baja")

    # SLA final
    sla_objetivo: str = Field(..., description="SLA final según prioridad.")

    # Categoría técnica
    categoria_sugerida: str = Field(..., description="Categoría técnica sugerida.")

    # Tiempo estimado real (basado en RAG)
    tiempo_estimado_resolucion: str = Field(
        ..., 
        description="Tiempo estimado según tickets históricos recuperados por RAG."
    )

    # Confianza
    nivel_confianza: float = Field(
        ..., 
        ge=0.0, 
        le=100.0, 
        description="Nivel de confianza porcentual."
    )

    # Justificación textual corta
    justificacion_modelo: str = Field(
        ..., 
        description="Justificación del modelo."
    )

    # Evidencias
    documentos_rag_usados: Optional[List[RAGDocument]] = Field(
        default=None,
        description="Documentos históricos relevantes usados por RAG."
    )
