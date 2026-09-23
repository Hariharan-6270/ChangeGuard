from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://guard_user:guard_pass@postgres:5432/changeguard_db"
    OPENAI_API_KEY: str = "dummy-key-or-replace-with-real"
    OPENAI_MODEL: str = "gpt-4o-mini"
    HIGH_RISK_THRESHOLD: int = 70
    MEDIUM_RISK_THRESHOLD: int = 30

    class Config:
        env_file = ".env"

settings = Settings()