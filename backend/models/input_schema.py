from pydantic import BaseModel, Field

class TicketInput(BaseModel):
    """
    Define el esquema de datos para la radicación de un ticket (RF1).
    Utiliza Pydantic para la validación de tipos.
    """
    titulo: str = Field(..., description="Título corto del incidente.")
    descripcion: str = Field(..., description="Descripción detallada del problema o solicitud.")
    cliente_afectado: str = Field(..., description="Nombre del cliente afectado.")
    porcentaje_afectado: int = Field(..., ge=0, le=100, description="Porcentaje de usuarios afectados (0-100).")
    tipo_incidente: str = Field(..., description="Tipo de incidente (e.g., Error, Consulta, Cambio, Performance).")
    informacion_contextual: str = Field("", description="Información adicional relevante.")

