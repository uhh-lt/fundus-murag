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
    Part,
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
        logger.info("Text response received from Gemini.")
        self._print_text_response(response)
        return response

    def _extract_text_from_response(self, raw_response: GenerationResponse) -> str:
        if raw_response.candidates and raw_response.candidates[0].text:
            return raw_response.candidates[0].text
        return ""

    def _start_new_chat_session(self) -> None:
        logger.info("Starting new Gemini chat session.")
        self._chat_session = self._model.start_chat()

    def reset_chat_session(self) -> None:
        super().reset_chat_session()
        self._chat_session = None

    def _chat_session_active(self) -> bool:
        return self._chat_session is not None

    def _is_text_response(self, response: GenerationResponse) -> bool:
        try:
            return response.candidates[0].text is not None
        except Exception:
            return False

    def _is_function_call_response(self, response: GenerationResponse) -> bool:
        try:
            return len(response.candidates[0].function_calls) > 0
        except Exception:
            return False

    def _execute_function_call(self, response: GenerationResponse) -> Part:
        try:
            self._print_function_call(response)
            function_call = response.candidates[0].content.parts[0].function_call
            params = dict(function_call.args)
            res = self._function_call_handler.execute_function(
                name=function_call.name,
                convert_results_to_json=True,
                **params,
            )
            part = Part.from_function_response(
                name=function_call.name,
                response={"content": res},
            )
            self._print_function_call_result(part)
            return part
        except Exception as e:
            logger.error(f"Error executing function call: {e}")
            return Part.from_function_response(
                name="Error",
                response={"content": str(e)},
            )

    def _send_followup_message_to_model(self, content: Any) -> GenerationResponse:
        logger.info("Sending function call result back to Gemini.")
        response = self._chat_session.send_message(content)  # type: ignore
        self._print_text_response(response)
        return response

    def _handle_function_calls(
        self, response: GenerationResponse
    ) -> GenerationResponse:
        while self._is_function_call_response(response):
            part = self._execute_function_call(response)
            response = self._send_followup_message_to_model(part)
        return response

    def _print_function_call(self, response: GenerationResponse) -> None:
        logger.info("*** Function Call Detected ***")
        function_call = response.candidates[0].content.parts[0].function_call
        logger.info(f"Function Name: {function_call.name}")
        truncated_args = {}
        for key, val in function_call.args.items():
            if isinstance(val, str) and len(val) > 256:
                val = val[:256] + "..."
            truncated_args[key] = val
        logger.info(f"Function Args: {truncated_args}")
        logger.info("*" * 120)

    def _print_function_call_result(self, result: Part) -> None:
        logger.info("*** Function Call Response ***")
        logger.info(result.to_dict())
        logger.info("*" * 120)

    def _print_text_response(self, response: GenerationResponse) -> None:
        logger.info("+++ Text Response +++")
        text = ""
        try:
            text = response.candidates[0].text or ""
        except ValueError:
            # Gemini raises ValueError if .text is not available
            logger.info("No text available in this response.")
        logger.info(text)
        logger.info("+" * 120)

    def send_text_image_message(
        self, text_prompt: str, base64_images: list[str], reset_chat: bool = False
    ) -> GenerationResponse:
        raise NotImplementedError

    @staticmethod
    def _load_model(model_name: str, use_tools: bool) -> GenerativeModel:
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
            # Filter out any non-Gemini or dev/tuning versions
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
            data["name"].append(model.name)
            data["display_name"].append(model.display_name)
            data["input_token_limit"].append(model.input_token_limit)
            data["output_token_limit"].append(model.output_token_limit)

        return pd.DataFrame(data)
