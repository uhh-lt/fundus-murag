from typing import Any, List, TypedDict

import openai
import pandas as pd
from loguru import logger

from fundus_murag.assistant.base_fundus_assistant import BaseFundusAssistant
from fundus_murag.assistant.prompt import ASSISTANT_SYSTEM_INSTRUCTION
from fundus_murag.config.config import load_config
from fundus_murag.singleton_meta import SingletonMeta

OPENAI_MODEL = "gpt-4o-mini"


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

    def _send_text_message_to_model(self, prompt: str) -> Any:
        logger.info(f"Sending text prompt to OpenAI: {prompt}")
        try:
            response = openai.chat.completions.create(
                model=self._model_config["model_name"],
                messages=self.chat_history,
                temperature=self._model_config["temperature"],
            )
            message_content = response.choices[0].message.content
            self.chat_history.append({"role": "assistant", "content": message_content})
            logger.info(f"OpenAI - Text response: {message_content}")
            return response
        except Exception as e:
            logger.error(f"OpenAI - Error during text prompt handling: {e}")
            return {"error": str(e)}

    def _extract_text_from_response(self, raw_response: dict) -> str:
        try:
            return raw_response["choices"][0]["message"]["content"]
        except Exception:
            return ""

    def _start_new_chat_session(self) -> None:
        logger.info("Starting new OpenAI chat session.")
        self.reset_chat_session()
        self._has_active_session = True

    def _chat_session_active(self) -> bool:
        return self._has_active_session

    def _send_followup_message_to_model(self, content: Any) -> Any:
        logger.info(
            f"OpenAI - Sending follow-up content after function call: {content}"
        )
        self.chat_history.append({"role": "assistant", "content": str(content)})
        try:
            response = openai.chat.completions.create(
                model=self._model_config["model_name"],
                messages=self.chat_history,
                temperature=self._model_config["temperature"],
            )
            message_content = response.choices[0].message.content
            self.chat_history.append({"role": "assistant", "content": message_content})
            logger.info(f"OpenAI - Followup response: {message_content}")
            return response
        except Exception as e:
            logger.error(f"OpenAI - Error during followup handling: {e}")
            return {"error": str(e)}

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
        logger.info(
            f"Found {len(df)} models matching initial filter (only_gpt={only_gpt})."
        )

        # models that can process images
        photo_model_substrings = ["o1", "gpt-4"]
        exclude_substrings = ["audio", "realtime", "preview", "turbo"]

        include_pattern = "|".join(photo_model_substrings)
        exclude_pattern = "|".join(exclude_substrings)

        df_filtered = df[
            df["name"].str.contains(include_pattern, case=False)
            & ~df["name"].str.contains(exclude_pattern, case=False)
        ]

        logger.info(f"After photo-processing filter, {len(df_filtered)} models remain.")
        return df_filtered
