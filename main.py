from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from core.config import settings
from routes import auth, audit, dashboard

# 1. Creamos la App con el nombre que definimos en config
app = FastAPI(title=settings.PROJECT_NAME)

# 2. Middleware de Sesión (Vital para el Login)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# 3. Registro de Rutas (Importamos los módulos creados)
app.include_router(auth.router, tags=["Seguridad"])
app.include_router(audit.router, prefix="/api", tags=["Auditoría"])
app.include_router(dashboard.router, tags=["Interfaz"])

# 4. Ruta raíz opcional
@app.get("/")
async def root():
    return {"message": f"Bienvenido a {settings.PROJECT_NAME} API"}
