from typing import Optional
from pydantic import BaseModel, Field, field_validator

class TicketInput(BaseModel):
    """
    Esquema oficial para radicación de tickets.
    Valida tipos y asegura consistencia para LLM y RAG.
    """

    titulo: str = Field(..., min_length=3, description="Título corto del incidente.")
    descripcion: str = Field(..., min_length=5, description="Descripción detallada del problema o solicitud.")
    cliente_afectado: str = Field(..., description="Nombre del cliente afectado.")
    porcentaje_afectado: int = Field(..., ge=0, le=100, description="Porcentaje de usuarios afectados (0-100).")

    tipo_incidente: str = Field(
        ...,
        description="Tipo de incidente (Disponibilidad, Cambio funcional, Performance, Seguridad, UI, Reportes, etc.)."
    )

    # Ahora opcional — no fuerza un string vacío
    informacion_contextual: Optional[str] = Field(
        default=None,
        description="Información adicional relevante del ticket (opcional)."
    )

    # Validación extra para evitar textos vacíos o absurdos
    @field_validator("titulo", "descripcion")
    def validate_non_empty(cls, v):
        if not v.strip():
            raise ValueError("El campo no puede estar vacío.")
        return v
