from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database — les vars POSTGRES_* les llegeix docker-compose directament del .env,
    # Python només necessita la URL completa.
    DATABASE_URL: str

    # App
    ENV: str = "development"
    LOG_LEVEL: str = "debug"
    APP_VERSION: str = "0.1.0"

    # CORS — string comma-separated (el split va a main.py per evitar problemes
    # de parsing JSON de pydantic-settings amb list[str])
    CORS_ORIGINS: str = "http://localhost:8080"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
