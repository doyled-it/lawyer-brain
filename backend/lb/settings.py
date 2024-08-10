from enum import Enum
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from lb.rag.db.chroma import CollectionNames
from lb.rag.llm.chat import ModelFamilies


class Environment(str, Enum):
    development = "development"
    production = "production"
    staging = "staging"
    docker = "docker"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LB_")

    dir: Path = Path.home().expanduser() / ".lb"
    environment: Environment | str = Environment.staging
    prod_url: str = ""
    origin: str = ""
    chroma_path: str | Path = "localhost"
    # chroma_path: str | Path = dir / "chroma"
    chroma_docker: bool = True
    chroma_port: int | None = None
    chroma_k: int = 20
    chroma_context: int = 5
    chroma_embedding_function: str = "OpenAI"
    llm_model: str = "gpt-4o-mini"
    llm_model_family: ModelFamilies | str = ModelFamilies.openai
    llm_collection: CollectionNames | str = CollectionNames.fivefour

    @model_validator(mode="after")
    def post_init(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        if not self.chroma_docker:
            self.chroma_path.mkdir(parents=True, exist_ok=True)
        if self.environment == Environment.production:
            self.origin = self.prod_url
        elif (
            self.environment == Environment.staging
            or self.environment == Environment.docker
        ):
            self.origin = "*"
        elif self.environment == Environment.development:
            self.origin = "http://localhost:3000"
