import logging
import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger("trainup")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"  # development | production | test
    DATABASE_URL: str = "sqlite:///./trainup.db"
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost"
    TIMEZONE: str = "America/Sao_Paulo"
    ENABLE_DOCS: bool = True
    SEED_DEMO: bool = True

    # Cadastro / autenticação
    PERSONAL_SIGNUP_CODE: str = ""  # vazio = cadastro público de personal desabilitado
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_MAX_ATTEMPTS_PER_EMAIL: int = 20  # teto por e-mail, independe do IP (barra spoof de cabeçalho)
    LOGIN_WINDOW_SECONDS: int = 300
    TRUST_PROXY_HEADERS: bool = False  # true apenas atrás do nginx (docker-compose.yml)
    RESET_TOKEN_MINUTES: int = 30

    # Ciência de dados
    STAGNATION_N: int = 3

    # Automação (catraca virtual)
    CHECKIN_EARLY_MIN: int = 15
    CATRACA_OPEN_SECONDS: int = 10
    CATRACA_MAX_DENIALS: int = 3
    CATRACA_BLOCK_SECONDS: int = 60


settings = Settings()

if not settings.SECRET_KEY:
    if settings.APP_ENV == "production":
        raise RuntimeError("SECRET_KEY é obrigatória em produção. Gere com: openssl rand -hex 32")
    settings.SECRET_KEY = secrets.token_urlsafe(48)
    log.warning("SECRET_KEY não definida: usando chave temporária (os logins expiram ao reiniciar).")
elif settings.APP_ENV == "production" and len(settings.SECRET_KEY) < 32:
    raise RuntimeError("SECRET_KEY muito curta: use pelo menos 32 caracteres.")
