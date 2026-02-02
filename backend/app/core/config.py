from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Factory AI Monitoring"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/factory_ai"
    )

    FPS_PROCESSING: int = Field(default=1, description="Number of frames to process per second of video")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
