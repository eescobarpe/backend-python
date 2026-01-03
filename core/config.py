import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # --- CONFIGURACIÓN DE LA APP ---
    PROJECT_NAME: str = "SilverNonStop Audit"
    
    # --- SEGURIDAD Y GOOGLE OAUTH ---
    # Los leemos de las variables de entorno de Railway
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET")
    
    # Esta llave es vital para las sesiones (puedes poner una por defecto para local)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "clave-secreta-de-desarrollo-123")
    
    # El email que tú usas para loguearte
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "tu-email@gmail.com")
    
    # --- BASE DE DATOS ---
    # Railway suele darte esta URL completa
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    class Config:
        # Esto permite que si creas un archivo .env en tu PC, lo lea automáticamente
        env_file = ".env"

# Instanciamos para que otros archivos puedan importar 'settings'
settings = Settings()
