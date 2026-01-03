import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # --- CONFIGURACIÓN DE LA APP ---
    PROJECT_NAME: str = "SilverNonStop Audit"
    
    # --- SEGURIDAD Y GOOGLE OAUTH ---
    # Usamos Optional[str] para que no falle si la variable no existe en el arranque
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    
    # Llave para sesiones con valor por defecto
    SECRET_KEY: str = os.getenv("SECRET_KEY", "silver_secret_default_2026")
    
    # Email autorizado
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "tu-email@gmail.com")
    
    # --- BASE DE DATOS ---
    # Si no hay base de datos, ponemos None para que no crashee
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    class Config:
        env_file = ".env"
        # Esta línea es importante: permite que existan variables extra o falten algunas sin morir
        extra = "ignore" 

# Instanciamos
settings = Settings()
