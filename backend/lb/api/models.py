from pydantic import BaseModel

from lb.rag.db.models import Speakers


class ChatRequest(BaseModel):
    user_message: str
    speaker: Speakers | str | None
    chat_history: list[dict[str, str]] | None


class AiMessage(BaseModel):
    message: str
    sources: list[str]
    context: str
