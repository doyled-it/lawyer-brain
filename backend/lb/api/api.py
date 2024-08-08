from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lb.api.models import AiMessage, ChatRequest
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat")
async def chat(request: ChatRequest) -> AiMessage:
    output = chain.invoke(
        {
            "user_message": request.user_message,
            "speaker": request.speaker,
            "chat_history": request.chat_history,
        }
    )
    return output
