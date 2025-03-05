from abc import ABC, abstractmethod
from typing import Any, List

import pandas as pd

from fundus_murag.assistant.dto import ChatMessage


class BaseFundusAssistant(ABC):
    def __init__(self, model_name: str, use_tools: bool = True):
        self.model_name = model_name
        self.use_tools = use_tools
        self.chat_history = []

    @abstractmethod
    def _extract_text_from_response(self, raw_response: Any) -> str:
        pass

    def send_text_message(self, prompt: str, reset_chat: bool = False) -> Any:
        if reset_chat or not self._chat_session_active():
            self.reset_chat_session()
            self._start_new_chat_session()

        self.chat_history.append({"role": "user", "content": prompt})

        raw_response = self._send_text_message_to_model(prompt)
        final_response = self._handle_function_calls(raw_response)

        assistant_text = self._extract_text_from_response(final_response)
        if assistant_text:
            self.chat_history.append({"role": "assistant", "content": assistant_text})

        return final_response

    @abstractmethod
    def _send_text_message_to_model(self, prompt: str) -> Any:
        pass

    @abstractmethod
    def send_text_image_message(
        self, text_prompt: str, base64_images: List[str], reset_chat: bool = False
    ) -> Any:
        pass

    @abstractmethod
    def _start_new_chat_session(self) -> None:
        pass

    @abstractmethod
    def _chat_session_active(self) -> bool:
        pass

    def reset_chat_session(self) -> None:
        self.chat_history = []
        self._has_active_session = False

    def get_chat_messages(self) -> List[ChatMessage]:
        return [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in self.chat_history
        ]

    def _handle_function_calls(self, response: Any) -> Any:
        while self._is_function_call_response(response):
            result = self._execute_function_call(response)
            response = self._send_followup_message_to_model(result)
        return response

    @abstractmethod
    def _send_followup_message_to_model(self, content: Any) -> Any:
        pass

    def _is_text_response(self, response: Any) -> bool:
        try:
            return bool(
                response.get("text")
                or response.get("choices", [])[0].get("message", {}).get("content")
            )
        except Exception:
            return False

    def _is_function_call_response(self, response: Any) -> bool:
        try:
            return "function_call" in response.get("choices", [])[0].get("message", {})
        except Exception:
            return False

    def _execute_function_call(self, response: Any) -> Any:
        try:
            message = response.get("choices", [])[0].get("message", {})
            function_call = message.get("function_call", {})
            function_name = function_call.get("name", "unknown_function")
            args = function_call.get("arguments", {})
            return {
                "role": "function",
                "name": function_name,
                "content": f"Executed {function_name} with {args}",
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    @abstractmethod
    def list_available_models(only_flash: bool = False) -> pd.DataFrame:
        pass
