import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# Rutas base del proyecto (deben existir FUERA de la clase)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
KNOWLEDGE_DIR = os.path.join(DATA_DIR, "knowledge")


class Settings(BaseSettings):
    """
    Carga de variables de entorno usando pydantic-settings.
    Busca primero en .env y luego en variables del sistema.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    # API Keys 
    OPENAI_API_KEY: str 

    # Modelos de IA 
    LLM_MODEL: str = "gpt-4o-mini"                   # Modelo para clasificación
    EMBEDDING_MODEL: str = "text-embedding-3-small"  # Modelo para embeddings RAG

    # RAG Engine 
    CHROMA_COLLECTION_NAME: str = "ticket_history_collection"
    KNOWLEDGE_BASE_PATH: str = os.path.join(KNOWLEDGE_DIR, "Knowledge_base.json")

    # Configuración del servidor API 
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000


# Instancia única accesible en toda la aplicación
settings = Settings()
