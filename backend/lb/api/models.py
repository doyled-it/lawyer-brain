from pydantic import BaseModel


class AiMessage(BaseModel):
    message: str
    sources: list[str]
    context: str
