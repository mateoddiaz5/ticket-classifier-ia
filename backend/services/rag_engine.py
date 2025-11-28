import json
import os
from typing import List, Dict

import chromadb
from openai import OpenAI

from backend.config import settings, DATA_DIR
from backend.models.output_schema import RAGDocument


class RAGEngine:
    """
    Motor RAG funcional usando:
    - OpenAI embeddings
    - ChromaDB persistente
    """

    def __init__(self):
        # Inicializar OpenAI Client
        try:
            self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            print("ERROR: No se pudo inicializar OpenAI:", e)
            raise

        # Ruta a embeddings
        chroma_path = os.path.join(DATA_DIR, "embeddings")

        # Cliente persistente ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)

        # Colección vectorial
        self.collection = self.chroma_client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
        )

    # Cargar Knowledge Base
    def _load_data(self):
        if not os.path.exists(settings.KNOWLEDGE_BASE_PATH):
            raise FileNotFoundError(
                f"Knowledge Base no encontrada: {settings.KNOWLEDGE_BASE_PATH}"
            )

        with open(settings.KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    # Generar Embedding
    def _embed_text(self, text: str):
        """Genera embeddings usando OpenAI."""
        try:
            resp = self.openai.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text,
            )
            return resp.data[0].embedding
        except Exception as e:
            print("Error generando embedding:", e)
            return None

    # Indexación (solo 1 vez)
    def index_data(self):
        if self.collection.count() > 0:
            print("Datos ya indexados. Saltando indexación.")
            return

        print("\n--- Iniciando Indexación RAG ---")

        data = self._load_data()

        documents = []
        metadatas = []
        ids = []
        embeddings = []

        for item in data:
            text = (
                f"Título: {item['titulo']}.\n"
                f"Descripción: {item['descripcion']}.\n"
                f"Categoría: {item['categoria']}.\n"
                f"Solución: {item['solucion']}"
            )

            vector = self._embed_text(text)
            if vector is None:
                continue

            embeddings.append(vector)
            documents.append(text)
            metadatas.append({
                "ticket_id": item["ticket_id"],
                "categoria": item["categoria"],
                "solucion": f"{item['solucion']} (Tiempo de resolución histórico: {item['tiempo_resolucion']})"
            })

            ids.append(str(item["ticket_id"]))

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )

        print(f"Indexación completada. Total documentos: {self.collection.count()}")

    # Recuperación
    def retrieve_documents(self, query_text: str, k: int = 5):
        """
        Recupera documentos similares.
        Mejora: k aumentado a 5 para mejor recall.
        """

        embedding = self._embed_text(query_text)
        if embedding is None:
            return []

        try:
            result = self.collection.query(
                query_embeddings=[embedding],
                n_results=k,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            print("Error en consulta:", e)
            return []

        docs = []

        for doc, meta, dist in zip(
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0],
        ):

            # ⚡ similitud basada en distancia invertida
            score = round(1 / (1 + dist), 4)

            docs.append(
                RAGDocument(
                    ticket_id=meta.get("ticket_id", "N/A"),
                    titulo=doc.split("\n")[0].replace("Título:", "").strip(),
                    categoria=meta.get("categoria", "N/A"),
                    solucion_resumen=meta.get("solucion", "N/A"),
                    similitud_score=score,
                )
            )

        return docs
