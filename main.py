from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg
import uvicorn
import os
from datetime import datetime
from typing import Optional
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de base de datos PostgreSQL
DATABASE_URL = os.environ.get("DATABASE_URL")

app = FastAPI(
    title="SilverNonStop Sistema de Auditoría",
    description="Sistema de auditoría para SilverNonStop con PostgreSQL",
    version="1.0.0"
)

# Modelos
class ErrorCriticoRequest(BaseModel):
    tabla_origen: str
    descripcion: str
    campo_afectado: Optional[str] = None
    record_id: Optional[str] = None

# SQL para crear tabla PostgreSQL
CREATE_AUDIT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS silvernostop_audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    tabla_origen VARCHAR(100) NOT NULL,
    tipo_evento VARCHAR(100) NOT NULL,
    severidad VARCHAR(20) NOT NULL,
    descripcion TEXT NOT NULL,
    campo_afectado VARCHAR(100),
    record_id VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON silvernostop_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_severidad ON silvernostop_audit_log(severidad);
CREATE INDEX IF NOT EXISTS idx_audit_tabla ON silvernostop_audit_log(tabla_origen);
"""

# Función para conectar a PostgreSQL
async def get_db_connection():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error conectando a PostgreSQL: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Inicializar PostgreSQL al arrancar"""
    try:
        conn = await get_db_connection()
        await conn.execute(CREATE_AUDIT_TABLE_SQL)
        await conn.close()
        logger.info("✅ Sistema de auditoría SilverNonStop inicializado con PostgreSQL")
    except Exception as e:
        logger.error(f"❌ Error inicializando sistema: {e}")

@app.get("/")
async def root():
    return {
        "message": "🔍 SilverNonStop Sistema de Auditoría",
        "status": "active",
        "version": "1.0.0",
        "database": "PostgreSQL",
        "migration": "✅ Migrado desde SQLite",
        "endpoints": [
            "/docs - Documentación Swagger",
            "/setup-sistema - Configurar sistema",
            "/log-error-critico - Registrar error crítico",
            "/diagnostico - Diagnóstico básico",
            "/verificar-postgresql - Verificar PostgreSQL",
            "/admin/tablas - Ver tablas",
            "/admin/estructura - Ver estructura"
        ]
    }

@app.post("/setup-sistema")
async def setup_sistema():
    """Configurar sistema de auditoría"""
    try:
        conn = await get_db_connection()
        await conn.execute(CREATE_AUDIT_TABLE_SQL)
        await conn.close()
        
        return {
            "status": "success",
            "mensaje": "Sistema de auditoría configurado correctamente con PostgreSQL",
            "database": "PostgreSQL",
            "migration": "✅ Migrado desde SQLite"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error configurando sistema: {str(e)}")

@app.post("/log-error-critico")
async def log_error_critico(request: ErrorCriticoRequest):
    """Registrar error crítico"""
    try:
        conn = await get_db_connection()
        
        evento_id = await conn.fetchval(
            """INSERT INTO silvernostop_audit_log 
               (tabla_origen, tipo_evento, severidad, descripcion, campo_afectado, record_id)
               VALUES ($1, $2, $3, $4, $5, $6)
               RETURNING id""",
            request.tabla_origen,
            "Error_Integridad",
            "CRITICA",
            request.descripcion,
            request.campo_afectado,
            request.record_id
        )
        
        await conn.close()
        
        logger.warning(f"🚨 ALERTA CRÍTICA: {request.tabla_origen} - {request.descripcion}")
        
        return {
            "status": "success",
            "evento_id": evento_id,
            "mensaje": f"Error crítico registrado para {request.tabla_origen}",
            "database": "PostgreSQL"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registrando evento: {str(e)}")

@app.get("/diagnostico")
async def diagnostico_basico():
    """Diagnóstico básico del sistema"""
    try:
        conn = await get_db_connection()
        
        # Contar eventos totales
        total_eventos = await conn.fetchval("SELECT COUNT(*) FROM silvernostop_audit_log")
        
        # Contar eventos críticos
        criticos = await conn.fetchval(
            "SELECT COUNT(*) FROM silvernostop_audit_log WHERE severidad = 'CRITICA'"
        )
        
        await conn.close()
        
        return {
            "estado_sistema": "CRITICO" if criticos > 0 else "SALUDABLE",
            "total_eventos": total_eventos,
            "eventos_criticos": criticos,
            "database": "PostgreSQL",
            "migration": "✅ Migrado desde SQLite",
            "ultima_actualizacion": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en diagnóstico: {str(e)}")

@app.get("/verificar-postgresql")
async def verificar_postgresql():
    """Verificar que PostgreSQL funciona correctamente"""
    try:
        conn = await get_db_connection()
        
        # Verificar versión de PostgreSQL
        version_pg = await conn.fetchval("SELECT version()")
        
        # Verificar que la tabla existe
        tabla_existe = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'silvernostop_audit_log')"
        )
        
        # Contar registros
        total_registros = await conn.fetchval("SELECT COUNT(*) FROM silvernostop_audit_log")
        
        # Info de conexión
        db_info = await conn.fetchrow("SELECT current_database(), current_user")
        
        await conn.close()
        
        return {
            "postgresql_disponible": True,
            "version_postgresql": version_pg.split()[1] if version_pg else "Unknown",
            "tabla_auditoria_existe": tabla_existe,
            "total_registros": total_registros,
            "database_name": db_info['current_database'],
            "user": db_info['current_user'],
            "migration": "✅ Migrado desde SQLite",
            "status": "✅ PostgreSQL funcionando correctamente"
        }
        
    except Exception as e:
        return {
            "postgresql_disponible": False,
            "error": str(e),
            "status": "❌ Error con PostgreSQL"
        }

@app.get("/eventos-recientes")
async def eventos_recientes():
    """Ver eventos recientes"""
    try:
        conn = await get_db_connection()
        
        eventos = await conn.fetch(
            """SELECT id, timestamp, tabla_origen, tipo_evento, severidad, 
                      descripcion, campo_afectado, record_id
               FROM silvernostop_audit_log 
               ORDER BY timestamp DESC 
               LIMIT 10"""
        )
        
        await conn.close()
        
        eventos_list = []
        for evento in eventos:
            eventos_list.append({
                "id": evento['id'],
                "timestamp": evento['timestamp'].isoformat(),
                "tabla_origen": evento['tabla_origen'],
                "tipo_evento": evento['tipo_evento'],
                "severidad": evento['severidad'],
                "descripcion": evento['descripcion'],
                "campo_afectado": evento['campo_afectado'],
                "record_id": evento['record_id']
            })
        
        return {
            "eventos": eventos_list,
            "total": len(eventos_list),
            "database": "PostgreSQL",
            "migration": "✅ Migrado desde SQLite"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo eventos: {str(e)}")

# ENDPOINTS DE ADMINISTRACIÓN (NUEVOS)
@app.get("/admin/tablas")
async def ver_tablas():
    """Ver todas las tablas de PostgreSQL"""
    try:
        conn = await get_db_connection()
        
        tablas = await conn.fetch(
            """SELECT table_name, table_type 
               FROM information_schema.tables 
               WHERE table_schema = 'public'
               ORDER BY table_name"""
        )
        
        await conn.close()
        
        return {
            "tablas": [{"nombre": t['table_name'], "tipo": t['table_type']} for t in tablas],
            "total": len(tablas),
            "database": "PostgreSQL"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo tablas: {str(e)}")

@app.get("/admin/estructura")
async def ver_estructura():
    """Ver estructura de la tabla principal"""
    try:
        conn = await get_db_connection()
        
        columnas = await conn.fetch(
            """SELECT column_name, data_type, is_nullable, column_default
               FROM information_schema.columns 
               WHERE table_name = 'silvernostop_audit_log'
               ORDER BY ordinal_position"""
        )
        
        await conn.close()
        
        return {
            "tabla": "silvernostop_audit_log",
            "columnas": [
                {
                    "nombre": c['column_name'],
                    "tipo": c['data_type'],
                    "nullable": c['is_nullable'],
                    "default": c['column_default']
                } for c in columnas
            ],
            "total_columnas": len(columnas),
            "database": "PostgreSQL"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estructura: {str(e)}")

@app.get("/admin/todos-eventos")
async def todos_eventos():
    """Ver TODOS los eventos (sin límite)"""
    try:
        conn = await get_db_connection()
        
        eventos = await conn.fetch(
            """SELECT * FROM silvernostop_audit_log 
               ORDER BY timestamp DESC"""
        )
        
        await conn.close()
        
        return {
            "eventos": [dict(evento) for evento in eventos],
            "total": len(eventos),
            "database": "PostgreSQL",
            "migration": "✅ Migrado desde SQLite"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo todos los eventos: {str(e)}")

# Configuración para Railway
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
