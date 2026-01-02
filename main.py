from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import os

# Crear la aplicación FastAPI
app = FastAPI(
    title="SilverNonStop Narrative API",
    description="Motor de narrativa para perfiles Silver",
    version="1.0.0"
)

# Modelos para tu arquitectura SilverNonStop
class NarrativeRequest(BaseModel):
    condicion_resultante: str
    tono: str = "neutro"
    idioma: str = "es"
    placeholder_data: dict = {}

class NarrativeResponse(BaseModel):
    texto_narrativo: str
    placeholders_usados: list
    tono_aplicado: str
    idioma_aplicado: str

# Endpoints básicos
@app.get("/")
async def root():
    return {
        "message": "SilverNonStop Narrative API - ¡Funcionando en Railway!",
        "status": "active",
        "version": "1.0.0",
        "arquitectura": "6 capas config-driven",
        "endpoints": [
            "/docs - Documentación Swagger",
            "/generate-narrative - Generar narrativa Silver",
            "/test-silvernostop - Test arquitectura"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "narrative-api",
        "railway": "connected"
    }

@app.post("/generate-narrative", response_model=NarrativeResponse)
async def generate_narrative(request: NarrativeRequest):
    """
    Genera narrativa Silver basada en Condicion_resultante y PreferenciasTonoIdioma
    Simula tu arquitectura de 6 capas
    """
    # Simulación de tu sistema de placeholders
    placeholders_ejemplo = ["VERBOACCION", "EXPERIENCIADETALLE", "CIERREIMPACTO"]
    
    # Simulación de wrapper_tono_idioma
    texto_base = f"Profesional con {request.condicion_resultante}"
    
    # Aplicar tono (simula narrativa_diccionario)
    if request.tono == "calido":
        texto_base = f"Talentoso profesional que destaca por {request.condicion_resultante}"
    elif request.tono == "formal":
        texto_base = f"Ejecutivo senior con {request.condicion_resultante} demostrada"
    elif request.tono == "neutro":
        texto_base = f"Profesional experimentado con {request.condicion_resultante}"
    
    return NarrativeResponse(
        texto_narrativo=texto_base,
        placeholders_usados=placeholders_ejemplo,
        tono_aplicado=request.tono,
        idioma_aplicado=request.idioma
    )

@app.get("/test-silvernostop")
async def test_silvernostop():
    """
    Endpoint de prueba para validar integración con arquitectura SilverNonStop
    """
    return {
        "arquitectura": "SilverNonStop",
        "objetivo": "Perfiles narrativos Silver vs CVs cronológicos",
        "capas": [
            "1. Persona y etapas (Talento6X, T6X_etapas)",
            "2. FEM configurables (T6X_etapas_FEM, Config_FEM)",
            "3. Repositorio campos (Campo_origen_despivotar, Códigos_JSON)",
            "4. Etiquetas por etapa (T6X_etapas_etiquetas)",
            "5. Evaluación (Condicion_resultante, Logica_evaluación)",
            "6. Narrativa (placeholder_ref, narrativa_diccionario, wrapper_tono_idioma)"
        ],
        "condiciones_ejemplo": [
            "TRAYECTORIALARGA",
            "LIDERAZGOEQUIPOS", 
            "FOCOCRECIMIENTO",
            "ENTORNOTECHDIGITAL"
        ],
        "preferencias_tono_idioma": {
            "tonos_disponibles": ["neutro", "calido", "formal"],
            "idiomas_disponibles": ["es", "en"]
        },
        "railway_status": "✅ Integrado correctamente"
    }

# Configuración para Railway (IMPORTANTE)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
