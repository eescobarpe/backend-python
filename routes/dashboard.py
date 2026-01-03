from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from core.config import settings

# Configuramos las plantillas (están en la carpeta /templates)
templates = Jinja2Templates(directory="templates")

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def leer_dashboard(request: Request):
    """
    Muestra el panel de control. 
    Si no hay usuario en sesión, redirige al login.
    """
    # 1. Verificamos sesión
    user = request.session.get('user')
    if not user:
        return RedirectResponse(url='/login')

    # 2. Lógica de Base de Datos (Simulada por ahora)
    # Aquí es donde mañana conectaremos con Postgres
    # logs = await db.fetch_all("SELECT * FROM audit_logs ORDER BY timestamp DESC")
    logs = [] # Lista vacía temporal para que no rompa

    # 3. Renderizamos el HTML pasando el objeto 'user' para el avatar
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "logs": logs,
        "user": user,
        "project_name": settings.PROJECT_NAME
    })
