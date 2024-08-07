from enum import Enum
from operator import itemgetter
from typing import Any

from langchain_anthropic.chat_models import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.output_parsers.json import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_openai.chat_models import ChatOpenAI

from lb.rag.db.models import CollectionNames
from lb.rag.db.retriever import FiveFourRetriever
from lb.rag.llm.outputs import FiveFourModelOutput
from lb.rag.llm.prompts import FIVEFOUR_AS_SPEAKER_TEMPLATE, FIVEFOUR_TEMPLATE


class ModelFamilies(str, Enum):
    openai = "OpenAI"
    anthropic = "Anthropic"
    google = "Google"
    mistralai = "MistralAI"


class LLMChain:
    def __init__(
        self,
        llm: str,
        model_family: str,
        collection: CollectionNames,
        retriever: FiveFourRetriever,
    ) -> None:
        self._llm = llm
        self.llm = self._load_llm(llm, model_family)
        self.parser = self._load_parser(collection)
        self.prompt = self._load_prompt(collection)
        self.retriever = retriever
        self.chain = self._create_chain()

    def invoke(self, input: dict[str, Any]) -> dict[str, Any]:
        return self.chain.invoke(input)

    def _load_llm(self, llm: str, model_family: ModelFamilies | str) -> BaseChatModel:
        if model_family == ModelFamilies.openai:
            return ChatOpenAI(model=llm)
        elif model_family == ModelFamilies.anthropic:
            return ChatAnthropic(model_name=llm)
        elif model_family == ModelFamilies.google:
            return ChatGoogleGenerativeAI(model=llm)
        elif model_family == ModelFamilies.mistralai:
            return ChatMistralAI(model_name=llm)
        else:
            raise ValueError(f"Model family {model_family} not supported.")

    def _load_parser(self, collection: CollectionNames | str) -> BaseOutputParser:
        if collection == CollectionNames.fivefour:
            return JsonOutputParser(pydantic_object=FiveFourModelOutput)
        elif collection == CollectionNames.supremecourt:
            raise NotImplementedError("Supreme Court collection not yet implemented.")
        else:
            raise ValueError(f"Collection {collection} not supported")

    def _load_prompt(self, collection: CollectionNames | str) -> callable:
        if collection == CollectionNames.fivefour:
            return self._fivefour_route_prompt
        elif collection == CollectionNames.supremecourt:
            raise NotImplementedError("Supreme Court collection not yet implemented.")
        else:
            raise ValueError(f"Collection {collection} not supported.")

    def _fivefour_route_prompt(self, input: dict[str, Any]) -> dict[str, Any]:
        if input["speaker"] is not None:
            prompt = PromptTemplate.from_template(
                FIVEFOUR_AS_SPEAKER_TEMPLATE,
                partial_variables={
                    "format_instructions": self.parser.get_format_instructions()
                },
            )
        else:
            prompt = PromptTemplate.from_template(
                FIVEFOUR_TEMPLATE,
                partial_variables={
                    "format_instructions": self.parser.get_format_instructions()
                },
            )
        return prompt

    def _split_retriever_output(self, retriever_output: dict[str, Any]) -> dict[str, Any]:
        return {
            "context": retriever_output["retriever_output"]["context"],
            "sources": retriever_output["retriever_output"]["sources"],
            "speaker": retriever_output["speaker"],
            "user_message": retriever_output["user_message"],
        }

    def _create_chain(self) -> None:
        return (
            {
                "retriever_output": itemgetter("user_message")
                | RunnableLambda(self.retriever.invoke),
                "speaker": itemgetter("speaker"),
                "user_message": itemgetter("user_message"),
            }
            | RunnableLambda(self._split_retriever_output)
            | RunnableParallel(
                message=RunnableLambda(self.prompt)
                | self.llm
                | self.parser
                | itemgetter("message"),
                sources=itemgetter("sources"),
                context=itemgetter("context"),
            )
        )
