from typing import Literal

import google.generativeai as genai
import vertexai
from google.oauth2.service_account import Credentials
from loguru import logger
from vertexai.generative_models import (
    GenerationConfig,
    GenerationResponse,
    GenerativeModel,
)

from fundus_murag.assistant.prompts.prompt import (
    QUERY_REWRITER_TEXT_IMAGE_SYSTEM_INSTRUCTION,
    QUERY_REWRITER_TEXT_TEXT_SYSTEM_INSTRUCTION,
)
from fundus_murag.config import load_config
from fundus_murag.singleton_meta import SingletonMeta

GEMINI_GENERATION_CONFIG = GenerationConfig(
    candidate_count=1,
    temperature=1.0,
    top_p=0.95,
    max_output_tokens=512,
)

MODEL_NAME = "gemini-1.5-flash-002"


class GeminiQueryRewriterAssistant(metaclass=SingletonMeta):
    def __init__(self, model_name: str | None = None):
        if model_name is None:
            model_name = MODEL_NAME
        conf = load_config()
        creds = Credentials.from_service_account_file(conf.google.application_credentials_file)

        vertexai.init(
            credentials=creds,
            project=conf.google.project_id,
            location="europe-west3",
        )
        genai.configure(credentials=creds)
        self._text_image_model: GenerativeModel = self._load_model(model_name, "text-image")
        self._text_text_model: GenerativeModel = self._load_model(model_name, "text-text")

    def _load_model(self, model_name: str, type: Literal["text-image", "text-text"]) -> GenerativeModel:
        model_name = model_name.lower()
        if "/" in model_name:
            model_name = model_name.split("/")[-1]

        model = GenerativeModel(
            model_name=model_name,
            generation_config=GEMINI_GENERATION_CONFIG,
            system_instruction=QUERY_REWRITER_TEXT_IMAGE_SYSTEM_INSTRUCTION
            if type == "text-image"
            else QUERY_REWRITER_TEXT_TEXT_SYSTEM_INSTRUCTION,
        )
        return model

    def rewrite_user_query_for_cross_modal_text_to_image_search(self, user_query: str) -> str:
        """
        Rewrites a user query to enhance the results of a cross-modal text-image search.

        Args:
            user_query: The user query to rewrite.

        Returns:
            The rewritten user query optimized for cross-modal text-image search.
        """

        response = self._text_image_model.generate_content(user_query)
        rewritten = self._get_text_response(response)
        if rewritten is not None:
            self._print_rewritten_query(user_query, rewritten)
            return rewritten

        return user_query

    def rewrite_user_query_for_text_to_text_search(self, user_query: str) -> str:
        """
        Rewrites a user query to enhance the results of a semantic textual similarity search.

        Args:
            user_query: The user query to rewrite.

        Returns:
            The rewritten user query optimized for semantic textual similarity search.
        """

        response = self._text_text_model.generate_content(user_query)
        rewritten = self._get_text_response(response)
        if rewritten is not None:
            self._print_rewritten_query(user_query, rewritten)
            return rewritten

        return user_query

    def _get_text_response(self, response: GenerationResponse) -> str | None:
        try:
            return response.candidates[0].text
        except Exception:
            return None

    def _print_rewritten_query(self, user_query: str, rewritten_query: str):
        logger.info(f"User Query: {user_query}")
        logger.info(f"Rewritten Query: {rewritten_query}")
