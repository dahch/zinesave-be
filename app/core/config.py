from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "production"
    FRONTEND_URL: str
    BACKEND_URL: str
    DATABASE_URL: str
    
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_PROJECT_ID: str
    
    DROPBOX_CLIENT_ID: str | None = None
    DROPBOX_CLIENT_SECRET: str | None = None
    
    ONEDRIVE_CLIENT_ID: str | None = None
    ONEDRIVE_TENANT_ID: str | None = None
    ONEDRIVE_CLIENT_SECRET_ID: str | None = None
    ONEDRIVE_CLIENT_SECRET: str | None = None
    
    JWT_SECRET: str
    
    B2_KEY_ID: str | None = None
    B2_APPLICATION_KEY: str | None = None
    B2_BUCKET_NAME: str | None = None
    B2_ENDPOINT_URL: str | None = None
    
    SENTRY_DSN: str | None = None
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "redis"
    REDIS_PORT: str = '6379'
    
    MAILERSEND_API_KEY: str | None = None
    MAILERSEND_FROM_EMAIL: str = "noreply@zinesave.io"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()