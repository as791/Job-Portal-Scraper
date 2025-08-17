"""
Configuration settings for the Slack RAG Bot.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    mongodb_uri: Optional[str] = Field(default="mongodb://localhost:27017", description="MongoDB URI")
    mongodb_db: Optional[str] = Field(default="jobs_db", description="MongoDB database name")
    jobs_collection: Optional[str] = Field(default="jobs", description="MongoDB jobs collection name")
    tags_collection: Optional[str] = Field(default="job_tags", description="MongoDB job jtags collection name")
    headless: bool = Field(default=True, description="Headless mode")
    requests_per_sec: float = Field(default=1.0, description="Requests per second")
    timezone: Optional[str] = Field(default="Asia/Kolkata", description="Timezone")
    linkedin_email: Optional[str] = Field(default=None, description="LinkedIn email")
    linkedin_password: Optional[str] = Field(default=None, description="LinkedIn password")
    log_level: Optional[str] = Field(default="INFO", description="Logging level")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 