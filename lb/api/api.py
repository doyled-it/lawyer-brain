from fastapi import FastAPI

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


@app.post("/generate")
def generate(user_message: str, speaker: Speakers | str | None = None) -> AiMessage:
    output = chain.invoke({"user_message": user_message, "speaker": speaker})
    return output
