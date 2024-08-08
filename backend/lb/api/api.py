from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from lb.api.models import AiMessage
from lb.rag.db.models import Speakers
from lb.rag.db.retriever import FiveFourRetriever
from lb.rag.llm.chat import LLMChain
from lb.settings import Settings

app = FastAPI()
settings = Settings()

retriever = FiveFourRetriever(
    settings.chroma_dir,
    k=settings.chroma_k,
    context=settings.chroma_context,
    embedding_function=settings.chroma_embedding_function,
)

chain = LLMChain(
    llm=settings.llm_model,
    model_family=settings.llm_model_family,
    collection=settings.llm_collection,
    retriever=retriever,
)

# Enable CORS
origins = [
    "http://localhost:3000",  # Adjust this to your frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    user_message: str
    speaker: Speakers | str | None


@app.post("/chat")
async def generate(request: ChatRequest) -> AiMessage:
    output = chain.invoke(
        {"user_message": request.user_message, "speaker": request.speaker}
    )
    return output
