from typing import Callable

import srsly
from fastapi.encoders import jsonable_encoder
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam

from fundus_murag.assistant.tools.tools import (
    FundusTool,
    get_openai_function_schema,
    get_tool_functions,
)


class FunctionCallHandler:
    def __init__(
        self,
        available_tools: list[FundusTool] | None = None,
        use_gemini_format: bool = False,
    ):
        self.use_gemini_format = use_gemini_format
        available_tools = available_tools or []
        self._available_tools = [
            FundusTool[tool] if isinstance(tool, str) else tool
            for tool in available_tools
        ]
        self._name_to_function = {}
        self.__register_tools()

    def __register_tools(self):
        for tool in self._available_tools:
            tool_funcs = get_tool_functions(tool)
            for name, func in tool_funcs.items():
                self._register_function(name, func)

    def _register_function(self, name: str, func: Callable) -> None:
        self._name_to_function[name] = func

    def _get_registered_functions(self) -> list[str]:
        return list(self._name_to_function.keys())

    def execute_function(
        self,
        *,
        name: str,
        convert_results_to_json: bool = True,
        **kwargs,
    ):
        if name not in self._name_to_function:
            raise ValueError(f"Function `{name}` not found")
        try:
            res = self._name_to_function[name](**kwargs)
        except Exception as e:
            res = str(e)
        if convert_results_to_json:
            return srsly.json_dumps(jsonable_encoder(res))
        return res

    def get_open_ai_tool_params(self) -> list[ChatCompletionToolParam]:
        tool_params = []
        for _, func in self._name_to_function.items():
            function = get_openai_function_schema(
                func, use_gemini_format=self.use_gemini_format
            )
            tool_params.append(
                ChatCompletionToolParam(function=function, type="function")
            )
        return tool_params
