from typing import Dict, Any, List

# Mapeo de Prioridades 
# Mapeo usado internamente para correlacionar Urgencia (Impacto) con Prioridad (P-level)
PRIORITY_MAPPING: Dict[str, str] = {
    "Crítica": "P1",
    "Alta": "P2",
    "Media": "P3",
    "Baja": "P4",
}

# Matriz de Tiempos de Respuesta (ANS/SLA) 
# Datos extraídos del documento soporte [cite: 46, 47]
SLA_MATRIX: Dict[str, Dict[str, str]] = {
    "Crítica": {
        "primera_respuesta": "15 minutos",
        "asistencia": "30 minutos",
        "solucion": "1 hora",
    },
    "Alta": {
        "primera_respuesta": "30 minutos (Horario Laboral)",
        "asistencia": "1 hora (Horario Laboral)",
        "solucion": "4 horas",
    },
    "Media": {
        "primera_respuesta": "1 hora (Horario Laboral)",
        "asistencia": "4 horas (Horario Laboral)",
        "solucion": "24 horas",
    },
    "Baja": {
        "primera_respuesta": "4 horas (Horario Laboral)",
        "asistencia": "1 día hábil",
        "solucion": "72 horas",
    },
}


# Factores de Impacto en el Negocio (Boost de Prioridad) 
# Información clave de los clientes extraída del documento [cite: 39, 40, 41, 42]
# Esto se usará en el prompt_manager para influir en la clasificación.
CLIENT_BUSINESS_IMPACT: Dict[str, Dict[str, Any]] = {
    "TechFin Solutions": {"MRR": 15000, "Estado": "En Riesgo de Churn"},
    "Retail Express": {"MRR": 5000, "Estado": "Producción", "Impacto_Critico": True}, # 100% afectados
    "LegalVerify Corp": {"MRR": 8000, "Estado": "Producción"},
    "Logística Rápida": {"MRR": 2500, "Estado": "En Riesgo de Churn", "Impacto_Critico": True}, # 100% afectados
    "Recursos Humanos S.A.": {"MRR": 1200, "Estado": "Producción"},
    "Marketing Cloud E-commerce": {"MRR": 20000, "Estado": "Producción (Alto Consumo)", "Impacto_Critico": True}, # Alto MRR, 100% afectados
    "Global": {"MRR": 7500, "Estado": "En Riesgo de Churn"},
    "HealthSecure": {"MRR": 3000, "Estado": "Integración"},
    "Banco del Mañana": {"MRR": 35000, "Estado": "Producción (Crítico)", "Impacto_Critico": True}, # Máximo MRR
    "Telecom Innova": {"MRR": 6500, "Estado": "Integración"},
}

# Lista de todos los clientes para poblar el dropdown en el frontend
CLIENT_LIST: List[str] = list(CLIENT_BUSINESS_IMPACT.keys())

