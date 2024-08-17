import os
from pathlib import Path

import chromadb
from langchain_chroma.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
from langchain_openai.embeddings import OpenAIEmbeddings

from lb.rag.db.models import CollectionNames, Speakers
from lb.utils.log import create_logger

log = create_logger(__name__)

os.environ["ANONYMIZED_TELEMETRY"] = "False"


class FiveFourRetriever:
    def __init__(
        self,
        chroma_path: str | Path,
        chroma_docker: bool = False,
        chroma_port: int = 9000,
        k: int = 5,
        context: int = 5,
        embedding_function: str = "OpenAI",
    ) -> None:
        self.chroma_path = chroma_path
        self.chroma_docker = chroma_docker
        self.chroma_port = chroma_port
        self.k = k
        self.context = context
        self._embedding_name = embedding_function

        self.embedding_function = self._get_embedding_function(embedding_function)
        self.db = self._create_chroma_db()

    def _get_embedding_function(
        self, embedding_function: str, progress: bool = False
    ) -> Embeddings:
        """Get the embedding function based on the provided name.

        Arguments:
            embedding_function: name of the embedding function
            progress: whether to show progress bar

        Returns:
            The LangChain embedding function
        """
        if embedding_function.lower() == "openai":
            embedding_function = OpenAIEmbeddings(model="text-embedding-3-small")
        else:
            try:
                from langchain_huggingface.embeddings import HuggingFaceEmbeddings
            except ImportError:
                message = (
                    "Hugging Face embeddings are not installed. "
                    "Please install with `pip install 'lawyerbrain[huggingface]' "
                    "package."
                )
                log.error(message)
                raise ImportError(message)
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

    def _create_chroma_db(self) -> Chroma:
        """Create a ChromaDB client.

        Returns:
            The ChromaDB client
        """
        # Create a ChromaDB client
        if not self.chroma_docker:
            return Chroma(
                collection_name=CollectionNames.fivefour,
                persist_directory=str(self.chroma_path),
                embedding_function=self.embedding_function,
            )
        else:
            if self.chroma_port is None:
                client = chromadb.HttpClient(self.chroma_path)
            else:
                client = chromadb.HttpClient(self.chroma_path, self.chroma_port)
            return Chroma(
                collection_name=CollectionNames.fivefour,
                client=client,
                embedding_function=self.embedding_function,
            )

    def invoke(
        self, user_message: str, speaker: Speakers | None = None
    ) -> tuple[str, list[str]]:
        """Invoke the retriever with the user's message.

        Arguments:
            user_message: the user's message
            speaker: the speaker to filter by

        Returns:
            The response to the user's message
        """
        # Filter by speaker if provided
        if speaker is not None:
            filter = {"speaker": speaker}
        else:
            filter = None

        # Get the most similar documents to the user_message
        documents = self.db.max_marginal_relevance_search(
            query=user_message, k=self.k, filter=filter
        )

        # Get the context for each document
        doc_responses = []
        metadata_responses = []
        for doc in documents:
            ids = [
                f'{doc.metadata["episode_id"]}-{doc.metadata["line_id"] + i}'
                for i in range(-self.context, self.context)
            ]
            responses = self.db.get(ids=ids)
            doc_responses.append(responses["documents"])
            metadata_responses.append(responses["metadatas"])

        final_response = ""
        sources = []
        for i, doc_response in enumerate(doc_responses):
            metadata_response = metadata_responses[i]
            combined_lines = "\n\n".join(doc_response)
            if (
                combined_lines not in final_response
                and "[laughter]" not in combined_lines
            ):
                final_response += (
                    f"\n\n## {metadata_response[0]['episode_title']}\n" + combined_lines
                )
                sources.append(metadata_response[0]["transcript_url"])

        return {"context": final_response, "sources": sources}
