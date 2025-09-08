from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Document Management System"
    API_V1_STR: str = "/api/v1"

    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str = "a-very-secret-key-for-testing-only" # Temporary default for debugging
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # MinIO
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
