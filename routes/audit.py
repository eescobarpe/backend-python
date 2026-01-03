from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Creamos el router
router = APIRouter()

# 1. Definimos el modelo de datos que esperamos de Airtable
class LogEntry(BaseModel):
    tabla_origen: str
    record_id: str
    severidad: str
    descripcion: str
    detalles: Optional[str] = None

# 2. Endpoint para recibir logs (El que llamarás desde Airtable)
@router.post("/log")
async def recibir_log(entry: LogEntry):
    """
    Recibe un error de integridad y lo guarda en la base de datos.
    """
    try:
        # AQUÍ IRÁ TU LÓGICA DE POSTGRESQL MAÑANA:
        # await db.execute("INSERT INTO silver_logs ...", entry.dict())
        
        print(f"📥 Log recibido: {entry.tabla_origen} - {entry.severidad}")
        return {"status": "success", "message": "Log registrado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Endpoint para resolver eventos (El que llama el botón del Dashboard)
@router.post("/resolver-evento/{log_id}")
async def resolver_evento(log_id: int, request: Request):
    """
    Marca un error como subsanado. 
    Solo debería funcionar si hay sesión activa (opcional).
    """
    if not request.session.get('user'):
        raise HTTPException(status_code=401, detail="No autorizado")
    
    try:
        # AQUÍ TU LÓGICA DE UPDATE:
        # await db.execute("UPDATE silver_logs SET estado='Resuelto' WHERE id=:id", {"id": log_id})
        
        print(f"✅ Evento {log_id} marcado como resuelto")
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al resolver el evento")
