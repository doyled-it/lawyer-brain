import json

from dotenv import load_dotenv
from langchain_chroma.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from rich.progress import track

from lb.utils.log import create_logger

log = create_logger(__name__)

load_dotenv()
# Step 1: Data Preparation


def load_data(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def add_context(transcripts, context_size=5):
    context_transcripts = []
    for episode in track(transcripts, description="Adding context to transcripts"):
        ep_transcripts = episode["transcript"]
        for i, entry in enumerate(ep_transcripts):
            start_idx = max(0, i - context_size)
            end_idx = min(len(ep_transcripts), i + context_size + 1)
            context = ep_transcripts[start_idx:end_idx]
            context_transcripts.append(
                {
                    "episode_title": episode["title"],
                    "transcript_url": episode["transcript_url"],
                    "timestamp": entry["timestamp"],
                    "speaker": entry["speaker"],
                    "text": entry["text"],
                    "context": context,
                }
            )
    return context_transcripts


# Load the JSON data
file_path = "data/transcripts.json"  # Update with the path to your JSON file
data = load_data(file_path)
episodes = data["episodes"]
context_transcripts = add_context(episodes)

# Step 2: ChromaDB Integration

# Initialize Sentence Transformer model
# embedding_model = HuggingFaceEmbeddings(
#     model_name="sentence-transformers/all-mpnet-base-v2"
# )
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

# Initialize ChromaDB client
vectorstore = Chroma(
    collection_name="transcripts",
    embedding_function=embedding_model,
    persist_directory="data/chromadb",
)

# Index the context transcripts
documents = []
for doc in context_transcripts:
    documents.append(
        {
            "title": doc["episode_title"],
            "url": doc["transcript_url"],
            "timestamp": doc["timestamp"],
            "speaker": doc["speaker"],
            "text": doc["text"],
            "context": " ".join([entry["text"] for entry in doc["context"]]),
        }
    )

texts = []
metadatas = []
for doc in documents:
    texts.append(doc["text"])
    metadatas.append(doc)

# Add the documents to the ChromaDB
log.info("Adding documents to ChromaDB")
vectorstore.add_texts(texts=texts, metadatas=metadatas)
log.info("Indexing complete")

# Step 3: Querying with LangChain


def search_transcripts(query, speaker=None):
    query_template = f"{query}"
    if speaker:
        query_template += f" Speaker: {speaker}"

    # Search in ChromaDB
    results = vectorstore.similarity_search(query_template, k=5)

    return results


# Step 4: RAG Model Integration

# Load a pre-trained language model
llm = ChatOpenAI("gpt-4o-mini")

prompt_template = PromptTemplate(
    input_variables=["context", "query"],
    template=(
        "Based on the following context, answer the query: {query}\nContext:\n"
        "{context}"
    ),
)

chain = prompt_template | llm


def generate_response(query, speaker=None):
    log.info(f"Searching for transcripts with query: {query}")
    results = search_transcripts(query, speaker)
    context = "\n".join(
        [f"{r['metadata']['speaker']}: {r['metadata']['text']}" for r in results]
    )

    response = chain.invoke({"context": context, "query": query})

    return response


# Example usage
if __name__ == "__main__":
    query = "What did Peter say about water rights?"
    speaker = "Peter"
    response = generate_response(query, speaker)
    print(response)
