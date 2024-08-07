from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from lb.rag.db.chroma import CollectionNames
from lb.rag.llm.chat import ModelFamilies


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LB_")

    dir: Path = Path.home().expanduser() / ".lb"
    chroma_dir: Path = dir / "chroma"
    chroma_k: int = 10
    chroma_context: int = 10
    chroma_embedding_function: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_model: str = "gpt-4o-mini"
    llm_model_family: ModelFamilies | str = ModelFamilies.openai
    llm_collection: CollectionNames | str = CollectionNames.fivefour
