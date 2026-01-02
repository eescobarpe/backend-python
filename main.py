from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import sqlite3
from datetime import datetime
from typing import Optional
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SilverNonStop Sistema de Auditoría",
    description="Sistema de auditoría para SilverNonStop con SQLite",
    version="1.0.0"
)

# Modelos
class ErrorCriticoRequest(BaseModel):
    tabla_origen: str
    descripcion: str
    campo_afectado: Optional[str] = None
    record_id: Optional[str] = None

# Función para inicializar SQLite
def init_sqlite():
    conn = sqlite3.connect('auditoria.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS silvernostop_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            tabla_origen TEXT NOT NULL,
            tipo_evento TEXT NOT NULL,
            severidad TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            campo_afectado TEXT,
            record_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.on_event("startup")
async def startup_event():
    """Inicializar SQLite al arrancar"""
    try:
        init_sqlite()
        logger.info("✅ Sistema de auditoría SilverNonStop inicializado con SQLite")
    except Exception as e:
        logger.error(f"❌ Error inicializando sistema: {e}")

@app.get("/")
async def root():
    return {
        "message": "🔍 SilverNonStop Sistema de Auditoría",
        "status": "active",
        "version": "1.0.0",
        "database": "SQLite",
        "endpoints": [
            "/docs - Documentación Swagger",
            "/setup-sistema - Configurar sistema",
            "/log-error-critico - Registrar error crítico",
            "/diagnostico - Diagnóstico básico",
            "/verificar-sqlite - Verificar SQLite"
        ]
    }

@app.post("/setup-sistema")
async def setup_sistema():
    """Configurar sistema de auditoría"""
    try:
        init_sqlite()
        return {
            "status": "success",
            "mensaje": "Sistema de auditoría configurado correctamente con SQLite"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error configurando sistema: {str(e)}")

@app.post("/log-error-critico")
async def log_error_critico(request: ErrorCriticoRequest):
    """Registrar error crítico"""
    try:
        conn = sqlite3.connect('auditoria.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO silvernostop_audit_log 
            (tabla_origen, tipo_evento, severidad, descripcion, campo_afectado, record_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            request.tabla_origen,
            "Error_Integridad",
            "CRITICA",
            request.descripcion,
            request.campo_afectado,
            request.record_id
        ))
        
        evento_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.warning(f"🚨 ALERTA CRÍTICA: {request.tabla_origen} - {request.descripcion}")
        
        return {
            "status": "success",
            "evento_id": evento_id,
            "mensaje": f"Error crítico registrado para {request.tabla_origen}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registrando evento: {str(e)}")

@app.get("/diagnostico")
async def diagnostico_basico():
    """Diagnóstico básico del sistema"""
    try:
        conn = sqlite3.connect('auditoria.db')
        cursor = conn.cursor()
        
        # Contar eventos totales
        cursor.execute("SELECT COUNT(*) FROM silvernostop_audit_log")
        total_eventos = cursor.fetchone()[0]
        
        # Contar eventos críticos
        cursor.execute("SELECT COUNT(*) FROM silvernostop_audit_log WHERE severidad = 'CRITICA'")
        criticos = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "estado_sistema": "CRITICO" if criticos > 0 else "SALUDABLE",
            "total_eventos": total_eventos,
            "eventos_criticos": criticos,
            "database": "SQLite",
            "ultima_actualizacion": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en diagnóstico: {str(e)}")

@app.get("/verificar-sqlite")
async def verificar_sqlite():
    """Verificar que SQLite funciona correctamente"""
    try:
        import sqlite3
        conn = sqlite3.connect('auditoria.db')
        cursor = conn.cursor()
        
        # Verificar que la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='silvernostop_audit_log'")
        tabla_existe = cursor.fetchone() is not None
        
        # Verificar versión de SQLite
        cursor.execute("SELECT sqlite_version()")
        version_sqlite = cursor.fetchone()[0]
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM silvernostop_audit_log")
        total_registros = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "sqlite_disponible": True,
            "version_sqlite": version_sqlite,
            "tabla_auditoria_existe": tabla_existe,
            "total_registros": total_registros,
            "archivo_db": "auditoria.db",
            "status": "✅ SQLite funcionando correctamente"
        }
        
    except Exception as e:
        return {
            "sqlite_disponible": False,
            "error": str(e),
            "status": "❌ Error con SQLite"
        }

@app.get("/eventos-recientes")
async def eventos_recientes():
    """Ver eventos recientes"""
    try:
        conn = sqlite3.connect('auditoria.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM silvernostop_audit_log 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        
        eventos = []
        for row in cursor.fetchall():
            eventos.append({
                "id": row[0],
                "timestamp": row[1],
                "tabla_origen": row[2],
                "tipo_evento": row[3],
                "severidad": row[4],
                "descripcion": row[5],
                "campo_afectado": row[6],
                "record_id": row[7]
            })
        
        conn.close()
        
        return {
            "eventos": eventos,
            "total": len(eventos)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo eventos: {str(e)}")

# Configuración para Railway
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
