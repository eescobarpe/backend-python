from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from core.config import settings

# Creamos el router (esto es como una "mini-app" de FastAPI)
router = APIRouter()

# Configuración de OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@router.get("/login")
async def login(request: Request):
    """Redirige al usuario a la página de login de Google."""
    # 'auth_callback' es el nombre de la función que definimos justo debajo
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/auth")
async def auth_callback(request: Request):
    """Punto de aterrizaje después de que el usuario se loguea en Google."""
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        return RedirectResponse(url='/login?error=token_failed')
    
    user_info = token.get('userinfo')
    if not user_info:
        raise HTTPException(status_code=400, detail="No se recibió info de usuario")

    # 🛡️ Filtro de seguridad usando el email de settings
    if user_info['email'] != settings.ADMIN_EMAIL:
        raise HTTPException(
            status_code=403, 
            detail=f"Acceso denegado. El email {user_info['email']} no está autorizado."
        )

    # Guardamos el usuario en la sesión
    request.session['user'] = dict(user_info)
    return RedirectResponse(url='/dashboard')

@router.get("/logout")
async def logout(request: Request):
    """Limpia la sesión y redirige al dashboard (que pedirá login de nuevo)."""
    request.session.pop('user', None)
    return RedirectResponse(url='/dashboard')
