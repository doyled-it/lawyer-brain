import json
import os
from pathlib import Path

from chromadb import Client
from chromadb.config import Settings
from dotenv import load_dotenv
from langchain_chroma.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_openai.embeddings import OpenAIEmbeddings

from lb.rag.db.models import CollectionNames
from lb.utils.log import create_logger

log = create_logger(__name__)

load_dotenv()

# See https://docs.trychroma.com/telemetry#in-chromas-backend-using-environment-variables
os.environ["ANONYMIZED_TELEMETRY"] = "False"


def load_transcripts(file_path: str | Path) -> list[dict[str, str]]:
    """Load transcripts from JSON file.

    Arguments:
        file_path: path to JSON file

    Returns:
        list of transcript entries
    """
    file_path = Path(file_path)
    with open(file_path, "r") as file:
        return json.load(file)


def create_ids(transcripts: list[dict[str, str]]) -> list[dict[str, str]]:
    """Create unique IDs for each transcript entry.

    Arguments:
        transcripts: list of transcript entries

    Returns:
        list of transcript entries with unique IDs
    """
    id_transcripts = []
    title_id = 0
    for episode in transcripts["episodes"]:
        ep_transcripts = episode["transcript"]
        for i, entry in enumerate(ep_transcripts):
            id_transcripts.append(
                {
                    "episode_title": episode["title"],
                    "transcript_url": episode["transcript_url"],
                    "timestamp": entry["timestamp"],
                    "speaker": entry["speaker"],
                    "text": entry["text"],
                    "id": f"{title_id}-{i}",
                    "episode_id": title_id,
                    "line_id": i,
                }
            )
        title_id += 1
    return id_transcripts


def create_context(
    transcripts: list[dict[str, str]], context_size: int = 5
) -> list[dict[str, str]]:
    """Create context for each transcript entry and flattens data.

    Arguments:
        transcripts: list of transcript entries
        context_size: number of entries to include in context

    Returns:
        list of transcript entries with context
    """
    context_transcripts = []
    for episode in transcripts["episodes"]:
        ep_transcripts = episode["transcript"]
        for i, entry in enumerate(ep_transcripts):
            start_idx = max(0, i - context_size)
            end_idx = min(len(ep_transcripts), i + context_size + 1)
            context = ep_transcripts[start_idx:end_idx]
            context = "\n\n".join(
                [f"{entry['speaker']}: {entry['text']}" for entry in context]
            )
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


def get_embedding_function(embedding_function: str, progress: bool = False) -> Embeddings:
    if embedding_function.lower() == "openai":
        embedding_function = OpenAIEmbeddings(model="text-embedding-3-small")
    else:
        try:
            embedding_function = HuggingFaceEmbeddings(
                model_name=embedding_function, show_progress=progress
            )
        except ValueError:
            message = (
                f"Invalid embedding function: {embedding_function}. Must be one of "
                "'OpenAI' or a valid Hugging Face sentence-transformer model."
            )
            log.error(message)
            raise ValueError(message)
    return embedding_function


def add_transcripts_to_db(
    transcripts: list[dict[str, str]],
    chroma_path: str | Path,
    collection_name: str,
    embedding_function: str,
    batch_size: int = 256,
    progress: bool = False,
) -> None:
    """Add transcripts to ChromaDB.

    Arguments:
        transcripts: list of transcript entries
        chroma_path: path to ChromaDB
        collection_name: name of collection
        embedding_function: embedding function to use
        batch_size: batch size for embedding
        progress: show progress bar
    """
    if collection_name not in CollectionNames:
        message = (
            f"Invalid collection name: {collection_name}. Must be one of "
            f"{CollectionNames}."
        )
        log.error(message)
        raise ValueError(message)

    if collection_name == CollectionNames.supremecourt:
        raise NotImplementedError("Supreme Court collection not yet implemented.")

    embedding_function = get_embedding_function(embedding_function)

    db = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_function,
        persist_directory=str(chroma_path),
    )
    texts = []
    metadatas = []
    ids = []
    for transcript in transcripts:
        if "[laughter]" in transcript["text"]:
            continue
        texts.append(
            f"({transcript['episode_title']}) {transcript['speaker']}: "
            f"'{transcript['text']}'"
        )
        ids.append(transcript["id"])
        metadata = {
            "episode_title": transcript["episode_title"],
            "transcript_url": transcript["transcript_url"],
            "timestamp": transcript["timestamp"],
            "speaker": transcript["speaker"],
            "episode_id": transcript["episode_id"],
            "line_id": transcript["line_id"],
        }
        metadatas.append(metadata)
    for i in range(0, len(texts), batch_size):
        db.add_texts(
            texts[i : i + batch_size],
            metadatas[i : i + batch_size],
            ids[i : i + batch_size],
            progress=progress,
        )


def retrieve_five_four(
    chroma_path: str | Path,
    query: str,
    speaker: str | None = None,
    k: int = 5,
    context: int = 5,
    embedding_function: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> dict[str, str]:
    """Retrieve a FiveFour transcript entry from ChromaDB.

    Arguments:
        chroma_path: path to ChromaDB
        query: query string
        speaker: speaker to filter by
        k: number of results to return
        context: number of entries to include in context
        embedding_function: embedding function to use

    Returns:
        transcript entry
    """
    # Get the embedding function
    embedding_function = get_embedding_function(embedding_function)

    # Create a ChromaDB client
    db = Chroma(
        collection_name="FiveFour",
        persist_directory=str(chroma_path),
        embedding_function=embedding_function,
    )

    # Filter by speaker if provided
    if speaker is not None:
        filter = {"speaker": speaker}
    else:
        filter = None

    # Get the most similar documents to the query
    documents = db.similarity_search(query=query, k=k, filter=filter)

    # Get the context for each document
    doc_responses = []
    metadata_responses = []
    for doc in documents:
        ids = [
            f'{doc.metadata["episode_id"]}-{doc.metadata["line_id"] + i}'
            for i in range(-context, context)
        ]
        responses = db.get(ids=ids)
        doc_responses.append(responses["documents"])
        metadata_responses.append(responses["metadatas"])

    final_response = ""
    sources = []
    for i, doc_response in enumerate(doc_responses):
        metadata_response = metadata_responses[i]
        combined_lines = "\n\n".join(doc_response)
        if combined_lines not in final_response and "[laughter]" not in combined_lines:
            final_response += (
                f"\n\n## {metadata_response[0]['episode_title']}\n" + combined_lines
            )
            sources.append(metadata_response[0]["transcript_url"])

    return final_response, sources


def delete_collection(chroma_path: str | Path, collection_name: str) -> None:
    """Delete a collection from ChromaDB.

    Arguments:
        chroma_path: path to ChromaDB
        collection_name: name of collection
    """
    db = Chroma(persist_directory=str(chroma_path))
    db.delete_collection(collection_name)
    log.debug(f"Collection {collection_name} deleted from ChromaDB.")


def list_collections(chroma_path: str | Path) -> list[str]:
    """List collections in ChromaDB.

    Arguments:
        chroma_path: path to ChromaDB
    """
    db = Client(settings=Settings(persist_directory=str(chroma_path), is_persistent=True))
    collections = db.list_collections()
    return collections
