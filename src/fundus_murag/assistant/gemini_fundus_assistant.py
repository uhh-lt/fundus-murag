from typing import Any

import google.generativeai as genai
import pandas as pd
import vertexai
from google.oauth2.service_account import Credentials
from loguru import logger
from vertexai.generative_models import (
    ChatSession,
    GenerationConfig,
    GenerationResponse,
    GenerativeModel,
)

from fundus_murag.assistant.base_fundus_assistant import BaseFundusAssistant
from fundus_murag.assistant.function_call_handler import FunctionCallHandler
from fundus_murag.assistant.prompt import ASSISTANT_SYSTEM_INSTRUCTION
from fundus_murag.assistant.tools import FUNDUS_TOOL
from fundus_murag.config.config import load_config
from fundus_murag.singleton_meta import SingletonMeta

GEMINI_GENERATION_CONFIG = GenerationConfig(
    candidate_count=1,
    temperature=1.0,
    top_p=0.95,
    max_output_tokens=2048,
)


class GeminiFundusAssistant(BaseFundusAssistant, metaclass=SingletonMeta):
    def __init__(self, model_name: str, use_tools: bool = True):
        super().__init__(model_name, use_tools)
        self._conf = load_config()
        creds = Credentials.from_service_account_file(
            self._conf.google_application_credentials_file
        )

        vertexai.init(
            credentials=creds,
            project=self._conf.google_project_id,
            location="europe-west3",
        )
        genai.configure(credentials=creds)

        self._chat_session: ChatSession | None = None
        self._model: GenerativeModel = self._load_model(model_name, use_tools)
        self._function_call_handler = FunctionCallHandler(auto_register_tools=use_tools)

    def _send_text_message_to_model(self, prompt: str) -> GenerationResponse:
        logger.info(f"Prompt: {prompt}")
        response = self._chat_session.send_message(prompt)  # type: ignore
        logger.info(f"Text response received: {response}")
        return response

    def _start_new_chat_session(self) -> None:
        logger.info("Starting new Gemini chat session.")
        self._chat_session = self._model.start_chat()

    def _chat_session_active(self) -> bool:
        return self._chat_session is not None

    def _send_followup_message_to_model(self, content: Any) -> Any:
        logger.info(f"Function call executed. Sending result back: {content}")
        return self._chat_session.send_message(content)  # type: ignore

    @logger.catch
    def send_text_image_message(
        self, text_prompt: str, base64_images: list[str], reset_chat: bool = False
    ) -> GenerationResponse:
        raise NotImplementedError

    def _load_model(self, model_name: str, use_tools: bool) -> GenerativeModel:
        model_name = model_name.lower()
        if "/" in model_name:
            model_name = model_name.split("/")[-1]

        return GenerativeModel(
            model_name=model_name,
            generation_config=GEMINI_GENERATION_CONFIG,
            system_instruction=ASSISTANT_SYSTEM_INSTRUCTION,
            tools=[FUNDUS_TOOL] if use_tools else None,
        )

    @staticmethod
    def list_available_models(only_flash: bool = False) -> pd.DataFrame:
        conf = load_config()
        creds = Credentials.from_service_account_file(
            conf.google_application_credentials_file
        )
        genai.configure(credentials=creds)
        models = []
        for m in genai.list_models():
            if (
                "gemini" not in m.name
                or "1.5" not in m.name
                or "tuning" in m.name
                or "exp" in m.name
                or "8b" in m.name
            ):
                continue
            if only_flash and "flash" not in m.name:
                continue
            models.append(m)

        data = {
            "name": [],
            "display_name": [],
            "input_token_limit": [],
            "output_token_limit": [],
        }
        for model in models:
            # N = model.name
            # data["name"].append(N[7:])
            data["name"].append(model.name)
            data["display_name"].append(model.display_name)
            data["input_token_limit"].append(model.input_token_limit)
            data["output_token_limit"].append(model.output_token_limit)

        return pd.DataFrame(data)
