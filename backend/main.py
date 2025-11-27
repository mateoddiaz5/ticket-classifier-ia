from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.config import settings, DATA_DIR
from backend.models.input_schema import TicketInput
from backend.models.output_schema import TicketClassification
from backend.services.llm_classifier import LLMClassifier


app = FastAPI(
    title="Ticket Classification AI Service",
    description="API para la clasificación automática de tickets usando RAG + OpenAI.",
    version="1.0.0"
)

# CORS — permitir conexión desde Streamlit, localhost
origins = [
    "*",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar el clasificador una sola vez
try:
    classifier = LLMClassifier()
except Exception as e:
    print(f"ERROR FATAL: No se pudo inicializar LLMClassifier. Detalle: {e}")
    classifier = None

# Endpoints
@app.get("/health")
def health_check():
    if classifier is None:
        raise HTTPException(
            status_code=503,
            detail="Servicio no disponible: El clasificador no pudo inicializarse."
        )
    return {"status": "ok"}


@app.post("/classify", response_model=TicketClassification)
async def classify_ticket_endpoint(ticket_data: TicketInput):
    if classifier is None:
        raise HTTPException(status_code=503, detail="Clasificador no disponible.")

    try:
        return classifier.classify_ticket(ticket_data)

    except Exception as e:
        print(f"Error procesando ticket: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno de clasificación: {str(e)}"
        )


# Punto de entrada local
if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
