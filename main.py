from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncpg
import uvicorn
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Literal
import json
import hashlib
import logging

app = FastAPI(
    title="SilverNonStop Sistema de Auditoría Completo",
    description="Sistema de auditoría dinámico completo para arquitectura SilverNonStop",
    version="1.0.0"
)

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de base de datos
DATABASE_URL = os.environ.get("DATABASE_URL")

# Modelos para el sistema de auditoría (basados en tu documentación)
class EventoAuditoriaBase(BaseModel):
    tabla_origen: str
    tipo_evento: str
    severidad: Literal["CRITICA", "ALTA", "MEDIA", "BAJA", "INFO"]
    descripcion: str
    campo_afectado: Optional[str] = None
    record_id: Optional[str] = None
    datos_contexto: Optional[Dict] = {}
    categoria_error: Optional[str] = None
    impacto_narrativa: Optional[str] = "Sin_Impacto"
    accion_requerida: Optional[str] = "Revisar manualmente"

class ErrorCriticoRequest(BaseModel):
    tabla_origen: str
    descripcion: str
    campo_afectado: Optional[str] = None
    record_id: Optional[str] = None

class CampoFaltanteRequest(BaseModel):
    tabla_origen: str
    campo_faltante: str
    contexto: Optional[Dict] = {}

class ErrorFEMRequest(BaseModel):
    campo: str
    descripcion: str
    contexto: Optional[Dict] = {}

class ErrorDespivotadoRequest(BaseModel):
    record_id: str
    campo: str
    error: str

class InfoGeneralRequest(BaseModel):
    tabla_origen: str
    descripcion: str
    contexto: Optional[Dict] = {}

# Script SQL completo para crear todas las tablas
CREATE_COMPLETE_AUDIT_SYSTEM_SQL = """
-- Tabla principal de auditoría SilverNonStop (basada en tu documentación)
CREATE TABLE IF NOT EXISTS silvernostop_audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    tabla_origen VARCHAR(100) NOT NULL,
    tipo_evento VARCHAR(100) NOT NULL,
    severidad VARCHAR(20) NOT NULL,
    descripcion TEXT NOT NULL,
    campo_afectado VARCHAR(100),
    record_id VARCHAR(50),
    datos_contexto JSONB DEFAULT '{}',
    estado_resolucion VARCHAR(50) DEFAULT 'Pendiente',
    accion_requerida TEXT,
    categoria_error VARCHAR(100),
    impacto_narrativa VARCHAR(50) DEFAULT 'Sin_Impacto',
    automatizacion_origen VARCHAR(100) DEFAULT 'Railway_API',
    hash_datos VARCHAR(50),
    es_recurrente BOOLEAN DEFAULT FALSE,
    contador_ocurrencias INTEGER DEFAULT 1,
    arquitectura_version VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de configuración dinámica (basada en tu ConfiguracionDinamicaAuditoria)
CREATE TABLE IF NOT EXISTS silvernostop_config_auditoria (
    id SERIAL PRIMARY KEY,
    tabla_detectada VARCHAR(100) NOT NULL UNIQUE,
    categoria VARCHAR(50) NOT NULL,
    criticidad VARCHAR(20) NOT NULL,
    tipos_evento_validos JSONB DEFAULT '[]',
    patrones_deteccion JSONB DEFAULT '[]',
    activa BOOLEAN DEFAULT TRUE,
    detectada_automaticamente BOOLEAN DEFAULT TRUE,
    fecha_deteccion TIMESTAMPTZ DEFAULT NOW(),
    ultima_actualizacion TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de métricas de éxito SilverNonStop
CREATE TABLE IF NOT EXISTS silvernostop_metricas (
    id SERIAL PRIMARY KEY,
    fecha_medicion DATE DEFAULT CURRENT_DATE,
    fems_minimos_configurados INTEGER DEFAULT 0,
    nodos_mapa_valor_activos INTEGER DEFAULT 0,
    campos_configuracion_completa_pct DECIMAL(5,2) DEFAULT 0.0,
    errores_criticos_pendientes INTEGER DEFAULT 0,
    calidad_perfiles_silver_pct DECIMAL(5,2) DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON silvernostop_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_tabla_origen ON silvernostop_audit_log(tabla_origen);
CREATE INDEX IF NOT EXISTS idx_audit_severidad ON silvernostop_audit_log(severidad);
CREATE INDEX IF NOT EXISTS idx_audit_hash ON silvernostop_audit_log(hash_datos);
CREATE INDEX IF NOT EXISTS idx_audit_categoria ON silvernostop_audit_log(categoria_error);
CREATE INDEX IF NOT EXISTS idx_audit_estado ON silvernostop_audit_log(estado_resolucion);

-- Insertar configuración inicial para SilverNonStop (basada en tu documentación)
INSERT INTO silvernostop_config_auditoria (tabla_detectada, categoria, criticidad, tipos_evento_validos) VALUES
('Sistema_General', 'sistema', 'BAJA', '["Info_General", "Sistema_Warning"]'),
('Campo_origen_despivotar', 'core', 'CRITICA', '["Error_Integridad", "Campo_Faltante", "Configuracion_Incorrecta", "Despivotado_Error"]'),
('Talento6X_etapas', 'core', 'ALTA', '["Datos_Vida_Laboral_Corruptos", "Etapas_Laborales_Inconsistentes", "Fechas_Invalidas"]'),
('T6X_etapas_FEM', 'fem', 'ALTA', '["FEM_Inconsistente", "FEM_Faltante", "Configuracion_FEM_Invalida"]'),
('Config_FEM', 'fem', 'CRITICA', '["Configuracion_FEM_Invalida", "Scope_FEM_Incorrecto"]'),
('T6X_etapas_etiquetas', 'procesamiento', 'MEDIA', '["Despivotado_Error", "Sincronizacion_Fallida", "Campo_Obsoleto"]'),
('Mapa_Valor', 'output', 'MEDIA', '["Narrativa_Error", "Mapa_Valor_Incompleto", "Generacion_Fallida"]')
ON CONFLICT (tabla_detectada) DO NOTHING;

-- Función para actualizar timestamp automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para actualizar timestamp
CREATE TRIGGER update_audit_log_updated_at BEFORE UPDATE ON silvernostop_audit_log 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_config_updated_at BEFORE UPDATE ON silvernostop_config_auditoria 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
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
    """Inicializar sistema completo de auditoría al arrancar"""
    try:
        conn = await get_db_connection()
        await conn.execute(CREATE_COMPLETE_AUDIT_SYSTEM_SQL)
        await conn.close()
        logger.info("✅ Sistema completo de auditoría SilverNonStop inicializado")
    except Exception as e:
        logger.error(f"❌ Error inicializando sistema de auditoría: {e}")

@app.get("/")
async def root():
    return {
        "message": "🔍 SilverNonStop Sistema de Auditoría Completo",
        "status": "active",
        "version": "1.0.0",
        "database": "PostgreSQL",
        "arquitectura": "Sistema completo de auditoría desacoplado",
        "componentes": [
            "Logging centralizado en PostgreSQL",
            "Configuración dinámica automática",
            "Validación y corrección automática",
            "Métricas de éxito SilverNonStop",
            "Endpoints especializados por tipo de error"
        ],
        "endpoints_principales": [
            "/docs - Documentación Swagger completa",
            "/setup-sistema - Configurar sistema completo",
            "/log-error-critico - Registrar error crítico",
            "/log-campo-faltante - Registrar campo faltante",
            "/log-error-fem - Registrar error FEM",
            "/log-error-despivotado - Registrar error despivotado",
            "/log-info - Registrar información general",
            "/diagnostico-completo - Diagnóstico completo",
            "/metricas-silvernostop - Métricas de éxito"
        ]
    }

@app.post("/setup-sistema")
async def setup_sistema_completo():
    """Configurar sistema completo de auditoría SilverNonStop"""
    try:
        conn = await get_db_connection()
        await conn.execute(CREATE_COMPLETE_AUDIT_SYSTEM_SQL)
        await conn.close()
        
        return {
            "status": "success",
            "mensaje": "Sistema completo de auditoría configurado correctamente",
            "tablas_creadas": [
                "silvernostop_audit_log - Tabla principal de auditoría",
                "silvernostop_config_auditoria - Configuración dinámica",
                "silvernostop_metricas - Métricas de éxito"
            ],
            "configuracion_inicial": [
                "7 tablas SilverNonStop configuradas automáticamente",
                "Tipos de evento especializados por categoría",
                "Índices optimizados para consultas",
                "Triggers automáticos para timestamps"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error configurando sistema: {str(e)}")

# ENDPOINTS ESPECIALIZADOS (Conversión directa de tu script)

@app.post("/log-error-critico")
async def log_error_critico(request: ErrorCriticoRequest):
    """Registrar error crítico (conversión de logErrorCritico)"""
    evento = EventoAuditoriaBase(
        tabla_origen=request.tabla_origen,
        tipo_evento="Error_Integridad",
        severidad="CRITICA",
        descripcion=request.descripcion,
        campo_afectado=request.campo_afectado,
        record_id=request.record_id,
        impacto_narrativa="Bloquea_Generacion",
        accion_requerida="Corregir inmediatamente"
    )
    return await procesar_evento_auditoria(evento)

@app.post("/log-campo-faltante")
async def log_campo_faltante(request: CampoFaltanteRequest):
    """Registrar campo faltante (conversión de logCampoFaltante)"""
    evento = EventoAuditoriaBase(
        tabla_origen=request.tabla_origen,
        tipo_evento="Campo_Faltante",
        severidad="ALTA",
        descripcion=f"Campo requerido '{request.campo_faltante}' no encontrado",
        campo_afectado=request.campo_faltante,
        datos_contexto=request.contexto,
        impacto_narrativa="Datos_Incompletos",
        accion_requerida=f"Configurar campo '{request.campo_faltante}'"
    )
    return await procesar_evento_auditoria(evento)

@app.post("/log-error-fem")
async def log_error_fem(request: ErrorFEMRequest):
    """Registrar error FEM (conversión de logErrorFEM)"""
    evento = EventoAuditoriaBase(
        tabla_origen="Config_FEM",
        tipo_evento="FEM_Inconsistente",
        severidad="MEDIA",
        descripcion=request.descripcion,
        campo_afectado=request.campo,
        datos_contexto=request.contexto,
        categoria_error="Configuracion_FEM",
        impacto_narrativa="Degrada_Calidad",
        accion_requerida="Revisar configuración FEM"
    )
    return await procesar_evento_auditoria(evento)

@app.post("/log-error-despivotado")
async def log_error_despivotado(request: ErrorDespivotadoRequest):
    """Registrar error de despivotado (conversión de logErrorDespivotado)"""
    evento = EventoAuditoriaBase(
        tabla_origen="Campo_origen_despivotar",
        tipo_evento="Despivotado_Error",
        severidad="ALTA",
        descripcion=f"Error en despivotado del campo '{request.campo}': {request.error}",
        campo_afectado=request.campo,
        record_id=request.record_id,
        categoria_error="Despivotado_SilverNonStop",
        impacto_narrativa="Bloquea_Generacion",
        accion_requerida="Revisar configuración de despivotado"
    )
    return await procesar_evento_auditoria(evento)

@app.post("/log-info")
async def log_info_general(request: InfoGeneralRequest):
    """Registrar información general (conversión de logInfo)"""
    evento = EventoAuditoriaBase(
        tabla_origen=request.tabla_origen,
        tipo_evento="Info_General",
        severidad="INFO",
        descripcion=request.descripcion,
        datos_contexto=request.contexto,
        impacto_narrativa="Sin_Impacto",
        accion_requerida="Ninguna"
    )
    return await procesar_evento_auditoria(evento)

# FUNCIÓN PRINCIPAL DE PROCESAMIENTO (Conversión de crearLogSilverNonStop)
async def procesar_evento_auditoria(evento: EventoAuditoriaBase):
    """Función principal de procesamiento (conversión de tu script)"""
    try:
        conn = await get_db_connection()
        
        # Validar tabla origen
        tabla_validada = await validar_tabla_existe(evento.tabla_origen)
        
        # Generar hash para detección de duplicados
        hash_datos = generar_hash_evento(evento)
        
        # Verificar si es duplicado
        existing = await conn.fetchrow(
            "SELECT id, contador_ocurrencias FROM silvernostop_audit_log WHERE hash_datos = $1",
            hash_datos
        )
        
        if existing:
            # Incrementar contador de duplicado
            await conn.execute(
                """UPDATE silvernostop_audit_log 
                   SET contador_ocurrencias = contador_ocurrencias + 1,
                       es_recurrente = TRUE,
                       updated_at = NOW()
                   WHERE id = $1""",
                existing['id']
            )
            
            await conn.close()
            return {
                "status": "duplicado_actualizado",
                "evento_id": existing['id'],
                "contador_ocurrencias": existing['contador_ocurrencias'] + 1,
                "mensaje": "Evento duplicado, contador incrementado"
            }
        else:
            # Crear nuevo evento
            categoria_automatica = determinar_categoria_automatica(tabla_validada, evento.tipo_evento)
            
            evento_id = await conn.fetchval(
                """INSERT INTO silvernostop_audit_log 
                   (tabla_origen, tipo_evento, severidad, descripcion, campo_afectado, 
                    record_id, datos_contexto, categoria_error, impacto_narrativa, 
                    automatizacion_origen, hash_datos, accion_requerida, arquitectura_version)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                   RETURNING id""",
                tabla_validada,
                evento.tipo_evento,
                evento.severidad,
                evento.descripcion,
                evento.campo_afectado,
                evento.record_id,
                json.dumps(evento.datos_contexto),
                evento.categoria_error or categoria_automatica,
                evento.impacto_narrativa,
                "Railway_API",
                hash_datos,
                evento.accion_requerida,
                datetime.now().isoformat()
            )
            
            await conn.close()
            
            # Si es crítico, log especial
            if evento.severidad == "CRITICA":
                logger.warning(f"🚨 ALERTA CRÍTICA SILVERNOSTOP: {tabla_validada} - {evento.descripcion}")
            
            return {
                "status": "success",
                "evento_id": evento_id,
                "mensaje": f"Evento registrado para {tabla_validada}",
                "categoria_asignada": evento.categoria_error or categoria_automatica,
                "hash_datos": hash_datos
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando evento: {str(e)}")

@app.get("/diagnostico-completo")
async def diagnostico_completo():
    """Diagnóstico completo del sistema (conversión de diagnosticarArquitectura)"""
    try:
        conn = await get_db_connection()
        
        # Estadísticas generales
        total_eventos = await conn.fetchval("SELECT COUNT(*) FROM silvernostop_audit_log")
        
        # Eventos por severidad
        severidad_rows = await conn.fetch(
            "SELECT severidad, COUNT(*) as count FROM silvernostop_audit_log GROUP BY severidad"
        )
        eventos_por_severidad = {row['severidad']: row['count'] for row in severidad_rows}
        
        # Eventos críticos pendientes
        criticos_pendientes = await conn.fetchval(
            "SELECT COUNT(*) FROM silvernostop_audit_log WHERE severidad = 'CRITICA' AND estado_resolucion = 'Pendiente'"
        )
        
        # Tablas monitoreadas
        tablas_rows = await conn.fetch(
            "SELECT DISTINCT tabla_origen FROM silvernostop_audit_log ORDER BY tabla_origen"
        )
        tablas_monitoreadas = [row['tabla_origen'] for row in tablas_rows]
        
        # Eventos recientes
        eventos_recientes = await conn.fetch(
            """SELECT timestamp, tabla_origen, tipo_evento, severidad, descripcion 
               FROM silvernostop_audit_log 
               ORDER BY timestamp DESC LIMIT 10"""
        )
        
        # Estado del sistema
        estado_sistema = "SALUDABLE"
        if criticos_pendientes > 0:
            estado_sistema = "CRITICO"
        elif eventos_por_severidad.get("ALTA", 0) > 5:
            estado_sistema = "ATENCION"
        
        await conn.close()
        
        return {
            "diagnostico_silvernostop": {
                "estado_sistema": estado_sistema,
                "total_eventos": total_eventos,
                "eventos_por_severidad": eventos_por_severidad,
                "criticos_pendientes": criticos_pendientes,
                "tablas_monitoreadas": tablas_monitoreadas,
                "eventos_recientes": [dict(evento) for evento in eventos_recientes],
                "ultima_actualizacion": datetime.now().isoformat()
            },
            "metricas_objetivo": {
                "fems_minimos_requeridos": 5,
                "nodos_mapa_valor_requeridos": 5,
                "configuracion_completa_objetivo": 90.0,
                "errores_criticos_objetivo": 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en diagnóstico: {str(e)}")

@app.get("/metricas-silvernostop")
async def obtener_metricas_silvernostop():
    """Métricas específicas de éxito SilverNonStop"""
    try:
        conn = await get_db_connection()
        
        # Calcular métricas actuales
        criticos_pendientes = await conn.fetchval(
            "SELECT COUNT(*) FROM silvernostop_audit_log WHERE severidad = 'CRITICA' AND estado_resolucion = 'Pendiente'"
        )
        
        # Simular métricas (en producción vendrían de Airtable)
        metricas_actuales = {
            "fems_minimos_configurados": 5,  # Sector, Rol, Equipo, Áreas, Países
            "nodos_mapa_valor_activos": 4,   # Simulado
            "campos_configuracion_completa_pct": 85.5,
            "errores_criticos_pendientes": criticos_pendientes,
            "calidad_perfiles_silver_pct": 92.3
        }
        
        # Guardar métricas
        await conn.execute(
            """INSERT INTO silvernostop_metricas 
               (fems_minimos_configurados, nodos_mapa_valor_activos, 
                campos_configuracion_completa_pct, errores_criticos_pendientes, 
                calidad_perfiles_silver_pct)
               VALUES ($1, $2, $3, $4, $5)""",
            metricas_actuales["fems_minimos_configurados"],
            metricas_actuales["nodos_mapa_valor_activos"],
            metricas_actuales["campos_configuracion_completa_pct"],
            metricas_actuales["errores_criticos_pendientes"],
            metricas_actuales["calidad_perfiles_silver_pct"]
        )
        
        await conn.close()
        
        return {
            "metricas_silvernostop": metricas_actuales,
            "objetivos": {
                "fems_minimos": 5,
                "nodos_mapa_valor": 5,
                "configuracion_completa": 90.0,
                "errores_criticos": 0,
                "calidad_perfiles": 95.0
            },
            "estado_cumplimiento": {
                "fems_ok": metricas_actuales["fems_minimos_configurados"] >= 5,
                "nodos_ok": metricas_actuales["nodos_mapa_valor_activos"] >= 5,
                "configuracion_ok": metricas_actuales["campos_configuracion_completa_pct"] >= 90.0,
                "criticos_ok": metricas_actuales["errores_criticos_pendientes"] == 0,
                "calidad_ok": metricas_actuales["calidad_perfiles_silver_pct"] >= 95.0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo métricas: {str(e)}")

# Funciones auxiliares (conversión de tu script)
async def validar_tabla_existe(nombre_tabla: str) -> str:
    """Validar tabla existe (conversión de validarTablaOrigen)"""
    tablas_validas = [
        "Sistema_General", "Campo_origen_despivotar", "Talento6X_etapas",
        "T6X_etapas_FEM", "Config_FEM", "T6X_etapas_etiquetas", "Mapa_Valor"
    ]
    
    if nombre_tabla in tablas_validas:
        return nombre_tabla
    
    logger.warning(f"⚠️ Tabla '{nombre_tabla}' no encontrada. Usando 'Sistema_General'")
    return "Sistema_General"

def generar_hash_evento(evento: EventoAuditoriaBase) -> str:
    """Generar hash para detección de duplicados (conversión de generarHashSimple)"""
    data_string = f"{evento.tabla_origen}_{evento.tipo_evento}_{evento.campo_afectado}_{evento.record_id}"
    return hashlib.md5(data_string.encode()).hexdigest()[:16]

def determinar_categoria_automatica(tabla_origen: str, tipo_evento: str) -> str:
    """Determinar categoría automáticamente (conversión de determinarCategoria)"""
    mapeo_tabla = {
        "Campo_origen_despivotar": "Despivotado_SilverNonStop",
        "Config_FEM": "Configuracion_FEM",
        "T6X_etapas_FEM": "Configuracion_FEM",
        "Talento6X_etapas": "Vida_Laboral_Processing",
        "T6X_etapas_etiquetas": "Mapa_Valor_SilverNonStop",
        "Mapa_Valor": "Narrativa_Generation_Silver"
    }
    
    mapeo_tipo = {
        "FEM_Inconsistente": "Configuracion_FEM",
        "Despivotado_Error": "Despivotado_SilverNonStop",
        "Narrativa_Error": "Narrativa_Generation_Silver",
        "Sincronizacion_Fallida": "Sincronizacion_SilverNonStop"
    }
    
    return mapeo_tipo.get(tipo_evento) or mapeo_tabla.get(tabla_origen) or "Integridad_Datos"

# Configuración para Railway
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
@app.get("/reset-sistema-total")
async def reset_sistema_total():
    try:
        conn = await get_db_connection()
        # Borramos todo para limpiar la estructura antigua
        await conn.execute("DROP TABLE IF EXISTS silvernostop_audit_log CASCADE")
        await conn.execute("DROP TABLE IF EXISTS silvernostop_config_auditoria CASCADE")
        await conn.execute("DROP TABLE IF EXISTS silvernostop_metricas CASCADE")
        await conn.close()
        return {"status": "success", "message": "Estructura antigua eliminada. Procede a /setup-sistema"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
@app.post("/resolver-evento/{evento_id}")
async def resolver_evento(evento_id: int):
    """Marca un error como solucionado para limpiar el diagnóstico"""
    try:
        conn = await get_db_connection()
        # Actualizamos el estado a 'Resuelto'
        await conn.execute(
            "UPDATE silvernostop_audit_log SET estado_resolucion = 'Resuelto', updated_at = NOW() WHERE id = $1",
            evento_id
        )
        await conn.close()
        return {"status": "success", "mensaje": f"Evento {evento_id} marcado como RESUELTO. El sistema volverá a estar SALUDABLE."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# ... (tus otros imports y configuración de DB)

templates = Jinja2Templates(directory="templates")

@app.get("/dashboard", response_class=HTMLResponse)
async def leer_dashboard(request: Request):
    # 1. Obtenemos los datos reales de la base de datos
    conn = await get_db_connection()
    logs = await conn.fetch("SELECT * FROM silvernostop_audit_log ORDER BY timestamp DESC LIMIT 50")
    await conn.close()
    
    # 2. Enviamos los datos al HTML
    return templates.TemplateResponse("dashboard.html", {"request": request, "logs": logs})
import os
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware

# --- INICIALIZACIÓN ---
app = FastAPI()

# 1. MIDDLEWARE DE SESIÓN (Indispensable para Google Login)
# Asegúrate de tener 'SECRET_KEY' en las variables de Railway
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "silver_ultra_secret_2026"))

templates = Jinja2Templates(directory="templates")

# 2. CONFIGURACIÓN DE GOOGLE OAUTH
oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("519442882454-ap4k1al3tvgl3ptmjm0741u0sa4mnl49.apps.googleusercontent.com"),
    client_secret=os.getenv("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"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# --- RUTAS DE AUTENTICACIÓN ---

@app.get("/login")
async def login(request: Request):
    # Genera la URL de redirección hacia Google
    # 'auth_callback' es el nombre de la función que definimos abajo
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth")
async def auth_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        return HTMLResponse(content=f"Error de autenticación: {e}", status_code=400)
    
    user_info = token.get('userinfo')
    if not user_info:
        raise HTTPException(status_code=400, detail="No se pudo obtener información de Google")

    # 🛡️ FILTRO DE SEGURIDAD SILVER: Solo tú entras
    # Cambia 'tu-email@gmail.com' por tu dirección real
    EMAIL_AUTORIZADO = "escobar.enrique@gmail.com" 
    
    if user_info['email'] != EMAIL_AUTORIZADO:
        raise HTTPException(
            status_code=403, 
            detail=f"Acceso denegado. El email {user_info['email']} no está autorizado."
        )

    # Si todo es correcto, guardamos el usuario en la sesión del navegador
    request.session['user'] = dict(user_info)
    return RedirectResponse(url='/dashboard')

@app.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/dashboard')

# --- RUTA PROTEGIDA (DASHBOARD) ---

@app.get("/dashboard", response_class=HTMLResponse)
async def leer_dashboard(request: Request):
    # Verificamos si hay un usuario logueado en la sesión
    user = request.session.get('user')
    if not user:
        return RedirectResponse(url='/login')

    # AQUÍ TU LÓGICA DE BASE DE DATOS PARA TRAER LOS LOGS
    # conn = await get_db_connection()
    # logs = await conn.fetch("SELECT * FROM silvernostop_audit_log ORDER BY timestamp DESC LIMIT 50")
    # await conn.close()

    # Simulamos logs para que no de error si aún no conectas la DB aquí
    logs = [] # Sustituir por la consulta real a la base de datos

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "logs": logs,
        "user": user # Pasamos el usuario para saludar en el HTML: {{ user.name }}
    })
