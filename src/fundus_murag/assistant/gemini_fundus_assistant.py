import google.generativeai as genai
import pandas as pd
import srsly
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

from fundus_murag.assistant.dto import ChatMessage
from fundus_murag.assistant.function_call_handler import FunctionCallHandler
from fundus_murag.assistant.prompt import GEMINI_ASSISTANT_SYSTEM_INSTRUCTION
from fundus_murag.assistant.tools import (
    FUNDUS_TOOL,
)
from fundus_murag.config.config import load_config
from fundus_murag.singleton_meta import SingletonMeta

GEMINI_GENERATION_CONFIG = GenerationConfig(
    candidate_count=1,
    temperature=1.0,
    top_p=0.95,
    max_output_tokens=2048,
)


class GeminiFundusAssistant(metaclass=SingletonMeta):
    def __init__(self, model_name: str, use_tools: bool = True):
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
        self._model: GenerativeModel = self.load_model(model_name, use_tools)
        self._function_call_handler = FunctionCallHandler(auto_register_tools=use_tools)

    @logger.catch
    def send_text_message(
        self, prompt: str, reset_chat: bool = False
    ) -> GenerationResponse:
        logger.info(f"Prompt: {prompt} | Reset Chat: {reset_chat}")
        if self._chat_session is None or reset_chat:
            self.reset_chat_session()
            self._chat_session = self._model.start_chat()

        response = self._chat_session.send_message(prompt)
        while self._is_function_call_response(response):
            self._print_function_call(response)
            result = self._execude_function_call(response)
            self._print_function_call_result(result)
            response = self._chat_session.send_message(result)

        self._print_text_response(response)
        return response

    @logger.catch
    def send_text_image_message(
        self, text_prompt: str, base64_images: list[str], reset_chat: bool = False
    ) -> GenerationResponse:
        logger.info(
            f"Text Propmt: {text_prompt} | Images: {len(base64_images)} | Reset Chat: {reset_chat}"
        )
        if self._chat_session is None or reset_chat:
            self.reset_chat_session()
            self._chat_session = self._model.start_chat()

        text_parts = [Part.from_text(text_prompt)]
        image_parts = [
            Part.from_data(base64_image, mime_type="image/png")  # type: ignore
            for base64_image in base64_images
        ]
        prompt = text_parts + image_parts

        response = self._chat_session.send_message(prompt)  # type: ignore
        while self._is_function_call_response(response):
            self._print_function_call(response)
            result = self._execude_function_call(response)
            self._print_function_call_result(result)
            response = self._chat_session.send_message(result)

        self._print_text_response(response)
        return response

    def reset_chat_session(self) -> None:
        self._chat_session = None

    def get_chat_messages(self) -> list[ChatMessage]:
        """
        Returns text `ChatMessage`s in the chat session. That is messages, that are not Function Calls
        or Function Call Responses.
        """
        if self._chat_session is None:
            return []
        messages = []
        for parts in self._chat_session.history:
            role = parts.role
            content = ""
            for p in parts.parts:
                if self._is_text_part(p):
                    content += p.text
            if content:
                messages.append(ChatMessage(role=role, content=content))

        return messages

    def load_model(self, model_name: str, use_tools: bool) -> GenerativeModel:
        model_name = model_name.lower()
        if "/" in model_name:
            model_name = model_name.split("/")[-1]

        model = GenerativeModel(
            model_name=model_name,
            generation_config=GEMINI_GENERATION_CONFIG,
            system_instruction=GEMINI_ASSISTANT_SYSTEM_INSTRUCTION,
            tools=[FUNDUS_TOOL] if use_tools else None,
        )

        return model

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

    def _is_text_part(self, part: Part) -> bool:
        try:
            return part.text is not None
        except Exception:
            return False

    def _is_function_call_part(self, part: Part) -> bool:
        try:
            return part.function_call is not None
        except Exception:
            return False

    def _is_function_call_response_part(self, part: Part) -> bool:
        try:
            return part.function_response is not None
        except Exception:
            return False

    def _execude_function_call(self, response: GenerationResponse) -> Part:
        function_call = response.candidates[0].content.parts[0].function_call
        params = {key: value for key, value in function_call.args.items()}

        try:
            res = self._function_call_handler.execute_function(
                name=function_call.name,
                convert_results_to_json=True,
                **params,
            )
        except Exception as e:
            logger.error(f"Error executing function call: {e}")
            res = {str(type(e)): str(e)}

        return Part.from_function_response(
            name=function_call.name,
            response={"content": res},
        )

    def _print_function_call(
        self,
        response: GenerationResponse,
    ) -> None:
        logger.info("*** Function Call Detected ***")
        function_call = response.candidates[0].content.parts[0].function_call
        logger.info("Function Name: " + function_call.name)
        # truncate values for better readability
        params = {}
        for key, value in function_call.args.items():
            if isinstance(value, str) and len(value) > 256:
                value = value[:256]
            params[key] = value
        logger.info("Function Args: " + srsly.json_dumps(params, indent=2))
        logger.info("*" * 120)

    def _print_function_call_result(self, result: Part) -> None:
        logger.info("*** Function Call Response ***")
        logger.info(srsly.json_dumps(result.to_dict(), indent=2))
        logger.info("*" * 120)

    def _print_text_response(self, response: GenerationResponse) -> None:
        logger.info("+++ Text Response +++")
        logger.info(
            response.candidates[0].text,
        )
        logger.info("+" * 120)

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
            data["name"].append(model.name)
            data["display_name"].append(model.display_name)
            data["input_token_limit"].append(model.input_token_limit)
            data["output_token_limit"].append(model.output_token_limit)

        return pd.DataFrame(data)
