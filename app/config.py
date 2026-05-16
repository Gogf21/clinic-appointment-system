import os
from functools import lru_cache

class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:123@localhost:5432/clinic_appointment_db")
    app_title: str = "Система учёта приёмов пациентов"
    app_version: str = "1.0.0"
    debug: bool = True

@lru_cache()
def get_settings():
    return Settings()
