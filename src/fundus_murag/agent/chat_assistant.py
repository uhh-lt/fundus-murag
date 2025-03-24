import json
import re
from functools import cache
from typing import Any, Iterable

import google.auth.transport.requests
import mlflow
import openai
import pandas as pd
from google.auth import default
from loguru import logger
from mlflow.entities import SpanType
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam,
)
from openai.types.chat.chat_completion_content_part_image_param import (
    ChatCompletionContentPartImageParam,
)
from openai.types.chat.chat_completion_content_part_param import ChatCompletionContentPartParam
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam,
)
from openai.types.chat.chat_completion_tool_message_param import (
    ChatCompletionToolMessageParam,
)
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)

from fundus_murag.agent.tools.function_calling_handler import FunctionCallingHandler
from fundus_murag.agent.tools.tools import Tool
from fundus_murag.config import load_config
from fundus_murag.data.dtos.agent import AgentModel, ChatMessage

# https://platform.openai.com/docs/api-reference/chat/create
OPENAI_GENERATION_CONFIG = {
    "n": 1,  # number of completions to generate
    "temperature": 1.0,
    "max_completion_tokens": 8192,
}


class ChatAssistant:
    def __init__(
        self,
        *,
        assistant_name: str | None = None,
        model_name: str | None = None,
        system_instruction: str | None = None,
        available_tools: list[Tool] | None = None,
        generatin_config: dict[str, Any] = OPENAI_GENERATION_CONFIG,
    ):
        """
        The ChatAssistant class is a wrapper around the OpenAI Chat API that provides a simplified interface for
        interacting with the OpenAI Chat API. It allows sending user messages to the model and receiving responses from
        the model. The assistant can be configured with a specific model, system instruction, and available tools.

        Args:
            assistant_name (str, optional): The name of the assistant just for logging purposes. Defaults to None.
            model_name (str, optional): The name of the OpenAI model to use. If not provided, the default model specified in the config file will be used.
            system_instruction (str, optional): The system instruction to provide to the model. If not provided, no system instruction will be used.
            available_tools (list[FundusTool], optional): The list of available tools that the assistant can use. If not provided, no tools will be available.
            generatin_config (dict, optional): The generation configuration to use when sending messages to the model. Defaults to the OPENAI_GENERATION_CONFIG.
        """
        self._conf = load_config()
        self.model_name = model_name or self._conf.assistant.default_model
        self.assistant_name = assistant_name or "NO NAME"
        if not self.is_model_available(self.model_name):
            raise ValueError(f"Model '{self.model_name}' is not available.")
        self._system_instruction = system_instruction
        self._available_tools = available_tools
        if available_tools is None:
            self._available_tools = []
        self._function_call_handler = FunctionCallingHandler(
            available_tools=self._available_tools,
            use_gemini_format=self.model_name.startswith("google/"),
        )
        self._generation_config = generatin_config
        self._chat_history: list[ChatCompletionMessageParam] = []

    def send_user_message(
        self,
        text_message: str,
        base64_image: str | None = None,
    ) -> str:
        logger.info(f"[{self.assistant_name}] Sending user message to model {self.model_name}: {text_message}")
        if len(self._chat_history) == 0:
            self._chat_history.extend(self._build_system_instruction(self._system_instruction))
        user_message = self._build_user_messages(text_message, base64_image)
        self._chat_history.extend(user_message)
        response = self._run_agentic_loop()
        return response

    def get_converstation_history(self) -> list[ChatMessage]:
        # only return the user and assistant text messages
        messages = []
        for message in self._chat_history:
            if message.get("role", None) == "user":
                role = "user"
            elif message.get("role", None) == "assistant":
                role = "assistant"
            else:
                continue
            content = self._get_message_content(message)
            if len(content) > 0:
                messages.append(ChatMessage(role=role, content=content))
        return messages

    @staticmethod
    @cache
    def list_available_models() -> pd.DataFrame:
        try:
            open_ai_models = openai.models.list().data
        except Exception as e:
            logger.error(f"Error fetching OpenAI models: {e}")
            return pd.DataFrame()

        def get_display_name(model_id: str) -> str:
            return (
                model_id.replace("-", " ")
                .replace("google/", "")
                .replace("gpt", "GPT")
                .replace("flash", "Flash")
                .replace("pro", "Pro")
                .replace("gemini", "Gemini")
                .replace(" mini", " Mini")
            )

        models = []

        # https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/call-vertex-using-openai-library#supported_models
        gemini_models = [
            "google/gemini-2.0-flash",
            "google/gemini-1.5-flash",
            "google/gemini-1.5-pro",
        ]
        for model in gemini_models:
            models.append(
                {
                    "name": model,
                    "display_name": get_display_name(model),
                }
            )

        open_ai_pattern = r"(?:gpt\-4o|o1|o3)(?:-mini)?-202[4-9]-[0-9]{2}-[0-9]{2}"
        for model_obj in open_ai_models:
            if re.match(open_ai_pattern, model_obj.id):
                models.append(
                    {
                        "name": model_obj.id,
                        "display_name": get_display_name(model_obj.id),
                    }
                )
        df = pd.DataFrame(models)
        return df

    @staticmethod
    def get_default_model() -> AgentModel:
        conf = load_config()
        default = conf.assistant.default_model
        available = ChatAssistant.list_available_models()
        model = available[available["name"] == default]
        if model.empty:
            model = available.iloc[0]

        return AgentModel(
            name=model["name"].values[0],
            display_name=model["display_name"].values[0],
        )

    @staticmethod
    def is_model_available(model_name: str) -> bool:
        available_models = ChatAssistant.list_available_models()
        return model_name in available_models["name"].values

    @cache
    def _get_api_client(self) -> openai.OpenAI:
        if self.model_name.startswith("google/"):
            return self._get_vertexai_openai_client()
        return self._get_openai_client()

    def _get_openai_client(self) -> openai.OpenAI:
        logger.debug(f"[{self.assistant_name}] Creating client for OpenAI Models.")
        client = openai.OpenAI()
        return client

    def _get_vertexai_openai_client(self) -> openai.OpenAI:
        logger.debug(f"[{self.assistant_name}] Creating client for VertexAI Models.")
        # https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/call-vertex-using-openai-library
        project_id = self._conf.google.project_id
        location = self._conf.google.default_location

        credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        credentials.refresh(google.auth.transport.requests.Request())  # type: ignore
        api_key = credentials.token  # type: ignore

        client = openai.OpenAI(
            base_url=(
                f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/endpoints/openapi"
            ),
            api_key=api_key,
        )
        return client

    def _build_user_messages(
        self, prompt: str, base64_image: str | None = None
    ) -> list[ChatCompletionUserMessageParam]:
        # currently we only support a single image which gets appended to the prompt
        content: list[ChatCompletionContentPartParam] = [
            {"type": "text", "text": prompt},
        ]
        if base64_image:
            if not base64_image.startswith("data:image/"):
                base64_image = f"data:image/png;base64,{base64_image}"

            img_content = ChatCompletionContentPartImageParam(
                image_url={
                    "url": base64_image,
                    "detail": "auto",
                },
                type="image_url",
            )
            content.append(img_content)
        messages = [ChatCompletionUserMessageParam(role="user", content=content)]
        return messages

    def _build_system_instruction(
        self, system_instruction: str | None = None
    ) -> list[ChatCompletionSystemMessageParam]:
        if system_instruction:
            return [{"role": "system", "content": system_instruction}]
        return []

    def _add_assistant_response_to_chat_history(self, response: ChatCompletion) -> None:
        message = response.choices[0].message
        if message.role == "assistant":
            self._chat_history.append(ChatCompletionAssistantMessageParam(**message.model_dump()))

    def _create_chat_completion_from_history(self) -> ChatCompletion:
        tools = self._function_call_handler.build_open_ai_tool_params()
        messages = self._chat_history
        client = self._get_api_client()
        try:
            if len(tools) > 0:
                logger.debug(
                    f"[{self.assistant_name}] Sending OpenAI completion request with tools: {self._available_tools}"
                )
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    **self._generation_config,
                )
            else:
                logger.debug(f"[{self.assistant_name}] Sending OpenAI completion request without tools.")
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    **self._generation_config,
                )
            logger.debug(f"[{self.assistant_name}] OpenAI response received: {response}")
            return response
        except openai.OpenAIError as e:
            logger.error(f"[{self.assistant_name}] An OpenAIError occured: {e}")
            raise e
        except Exception as e:
            logger.error(f"[{self.assistant_name}] Unexpected Error of Type {type(e)}: {e}")
            raise e

    @mlflow.trace(span_type=SpanType.AGENT)
    def _run_agentic_loop(self) -> str:
        # 1. Send the messages in the chat history to the model
        response = self._create_chat_completion_from_history()
        self._add_assistant_response_to_chat_history(response)

        # 2. Run the agentic loop until no tool calls are present in the response
        while self._is_tool_call_response(response):
            logger.debug(f"[{self.assistant_name}] Tool Calls detected in response!")
            # execute the tool calls
            tool_messages = self._execute_tool_calls(response)
            # add the tool messages to the chat history and send them back to the model
            self._chat_history.extend(tool_messages)
            response = self._create_chat_completion_from_history()
            self._add_assistant_response_to_chat_history(response)

        # 3. Return the final response
        message = self._get_message_content(response)
        return message

    def _get_message_content(self, response_or_message: ChatCompletion | ChatCompletionMessageParam) -> str:
        text = ""
        if isinstance(response_or_message, ChatCompletion):
            message = response_or_message.choices[0].message
            if message.content:
                text = message.content
        else:
            # assistant or user message
            content = response_or_message.get("content")
            texts = []
            if isinstance(content, str):
                texts.append(content)
            elif isinstance(content, Iterable):
                for part in content:
                    if isinstance(part, str):
                        texts.append(part)
                    else:
                        t = part.get("text", part.get("refusal", None))
                        if t:
                            texts.append(t)

            if texts:
                text = "\n".join(texts)

        return text

    def _is_tool_call_response(self, response: ChatCompletion) -> bool:
        try:
            tool_calls = response.choices[0].message.tool_calls
            return tool_calls is not None and len(tool_calls) > 0
        except Exception:
            return False

    def _execute_tool_calls(self, response: ChatCompletion) -> list[ChatCompletionToolMessageParam]:
        tool_calls = tool_calls = response.choices[0].message.tool_calls
        if tool_calls is None:
            return []

        tool_messages = []
        for tc in tool_calls:
            try:
                tool_name = tc.function.name
                tool_args_str = tc.function.arguments or "{}"
                tool_args = json.loads(tool_args_str)

                result_json_str = self._function_call_handler.execute_function(
                    name=tool_name,
                    **tool_args,
                )

                tool_message = ChatCompletionToolMessageParam(content=result_json_str, role="tool", tool_call_id=tc.id)
                tool_messages.append(tool_message)
            except Exception as e:
                logger.error(f"[{self.assistant_name}] Error executing tool call: {e}")
                raise e

        return tool_messages

    def _str__(self):
        return (
            f"FundusAssistant(\n\tmodel_name={self.model_name},\n\t",
            f"tools={self._available_tools},\n\t",
            f"system_instruction={self._system_instruction}\n)",
        )

    def _repr__(self):
        return self._str__()
