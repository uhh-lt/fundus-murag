import json
from typing import Any, List, Optional, Tuple, TypedDict

import openai
import pandas as pd
from loguru import logger

from fundus_murag.assistant.base_fundus_assistant import BaseFundusAssistant
from fundus_murag.assistant.function_call_handler import FunctionCallHandler
from fundus_murag.assistant.prompt import ASSISTANT_SYSTEM_INSTRUCTION
from fundus_murag.config.config import load_config
from fundus_murag.singleton_meta import SingletonMeta

# Default model name if none provided
OPENAI_MODEL = "gpt-4-0613"


class ModelConfig(TypedDict):
    model_name: str
    system_instruction: str
    temperature: float


BASE_MODEL_CONFIG: ModelConfig = {
    "model_name": "",
    "system_instruction": "",
    "temperature": 1.0,
}


class OpenAIFundusAssistant(BaseFundusAssistant, metaclass=SingletonMeta):
    def __init__(self, model_name: str, use_tools: bool = True) -> None:
        super().__init__(model_name, use_tools)
        self._conf = load_config()
        openai.api_key = self._conf.open_ai_project_id

        self._model_config: ModelConfig = self._create_model_config(
            model_name, use_tools
        )
        self._has_active_session = False

        self._function_call_handler = FunctionCallHandler(auto_register_tools=use_tools)

        self._persistent_history = self.chat_history

    def _get_full_history(self) -> List[dict]:
        full_history = []
        if self._model_config["system_instruction"]:
            full_history.append(
                {"role": "system", "content": self._model_config["system_instruction"]}
            )
        full_history.extend(self._persistent_history)
        return full_history

    def switch_model(self, new_model_name: str):
        if new_model_name != self.model_name:
            self.model_name = new_model_name
            self._model_config = self._create_model_config(
                new_model_name, self.use_tools
            )
            self.reset_chat_session()

    def _send_text_message_to_model(self, prompt: str) -> Any:
        logger.info(f"Sending text prompt to OpenAI: {prompt}")
        self._persistent_history.append({"role": "user", "content": prompt})

        response = self._create_chat_completion(self._get_full_history())
        final_response = self._handle_function_calls(response)
        return final_response

    def _is_function_call_response(self, response: Any) -> bool:
        try:
            message = response.choices[0].message
            has_function_call = (
                hasattr(message, "function_call") and message.function_call is not None
            )
            logger.debug(f"Function call detected: {has_function_call}")
            return has_function_call
        except Exception as e:
            logger.error(f"Error checking for function call: {e}")
            return False

    def _parse_function_call(self, response: Any) -> Tuple[str, dict]:
        message = response.choices[0].message
        function_call = message.function_call
        function_args_str = function_call.arguments or "{}"
        function_args = json.loads(function_args_str)
        return function_call.name, function_args

    def _execute_function_call(self, response: Any) -> dict:
        try:
            function_name, result = self._execute_function_call_common(response)
            return {"role": "function", "name": function_name, "content": result}
        except Exception as e:
            logger.error(f"Error executing function call: {e}")
            return {"role": "function", "name": "Error", "content": str(e)}

    def _extract_text_from_response(self, raw_response: Any) -> str:
        try:
            return raw_response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error extracting text from response: {e}")
            return ""

    def _create_chat_completion(self, messages: List[dict]) -> Any:
        functions: Optional[List[dict]] = None
        function_call_setting: str = "auto"

        if self.use_tools:
            functions = self._function_call_handler.get_tool_schema_list()

        try:
            response = openai.chat.completions.create(
                model=self._model_config["model_name"],
                messages=messages,  # type: ignore
                temperature=self._model_config["temperature"],
                functions=functions,  # type: ignore
                function_call=function_call_setting,
            )
            logger.info(f"OpenAI response received: {response}")
            return response  # type: ignore
        except openai.error.OpenAIError as e:  # type: ignore
            logger.error(f"OpenAIError: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": str(e)}

    def _send_followup_message_to_model(self, content: Any) -> Any:
        logger.info("Sending follow-up message to OpenAI after function call.")
        self._persistent_history.append({"role": "assistant", "content": str(content)})
        response = self._create_chat_completion(self._get_full_history())
        return response

    def _start_new_chat_session(self) -> None:
        logger.info("Starting new OpenAI chat session.")
        self.reset_chat_session()
        self._has_active_session = True

    def reset_chat_session(self) -> None:
        super().reset_chat_session()
        self._persistent_history.clear()
        self._has_active_session = False

    def _chat_session_active(self) -> bool:
        return self._has_active_session

    def send_text_image_message(
        self, text_prompt: str, base64_images: List[str], reset_chat: bool = False
    ) -> Any:
        raise NotImplementedError

    def _create_model_config(self, model_name: str, use_tools: bool) -> ModelConfig:
        model_config = BASE_MODEL_CONFIG.copy()
        model_config["model_name"] = model_name or OPENAI_MODEL
        model_config["system_instruction"] = ASSISTANT_SYSTEM_INSTRUCTION
        return model_config

    @staticmethod
    def list_available_models(only_gpt: bool = False) -> pd.DataFrame:
        conf = load_config()
        openai.api_key = conf.open_ai_project_id

        logger.info("Fetching OpenAI models.")
        try:
            model_list = openai.models.list().data
        except Exception as e:
            logger.error(f"Error fetching OpenAI models: {e}")
            return pd.DataFrame()

        if only_gpt:
            model_list = [m for m in model_list if "gpt" in m.id.lower()]

        data = {
            "name": [],
            "display_name": [],
            "input_token_limit": [],
            "output_token_limit": [],
        }

        for model_obj in model_list:
            data["name"].append(model_obj.id)
            data["display_name"].append(model_obj.id)
            data["input_token_limit"].append(None)
            data["output_token_limit"].append(None)

        df = pd.DataFrame(data)
        photo_model_substrings = ["gpt-4"]
        exclude_substrings = [
            "audio",
            "realtime",
            "preview",
            "turbo",
            "chatgpt-4o-latest",
        ]

        include_pattern = "|".join(photo_model_substrings)
        exclude_pattern = "|".join(exclude_substrings)

        df_filtered = df[
            df["name"].str.contains(include_pattern, case=False)
            & ~df["name"].str.contains(exclude_pattern, case=False)
        ]

        return df_filtered
