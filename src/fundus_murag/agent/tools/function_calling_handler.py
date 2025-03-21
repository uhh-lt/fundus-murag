import srsly
from fastapi.encoders import jsonable_encoder
from loguru import logger
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam

from fundus_murag.agent.tools.function_schema import generate_openai_function_schema
from fundus_murag.agent.tools.tools import Tool


class FunctionCallingHandler:
    def __init__(
        self,
        available_tools: list[Tool] | None = None,
        use_gemini_format: bool = False,
    ):
        self.use_gemini_format = use_gemini_format
        self._available_tools = available_tools or []
        self._name_to_function = {}
        self.__register_tool_functions()

    def __register_tool_functions(self):
        for tool in self._available_tools:
            for name, func in tool.functions.items():
                if not callable(func):
                    raise ValueError(f"Function `{name}` is not callable")
                self._name_to_function[name] = func
                logger.debug(f"Registered function `{name}`")

    def _get_registered_functions(self) -> list[str]:
        return list(self._name_to_function.keys())

    def execute_function(
        self,
        *,
        name: str,
        convert_results_to_json: bool = True,
        **kwargs,
    ):
        logger.debug(f"Executing function `{name}` with kwargs: {kwargs}")
        if name not in self._name_to_function:
            raise ValueError(f"Function `{name}` not found")
        try:
            res = self._name_to_function[name](**kwargs)
        except Exception as e:
            res = str(e)
        if convert_results_to_json:
            res = srsly.json_dumps(jsonable_encoder(res))
        logger.debug(f"Function `{name}` executed successfully. Result: {res}")
        return res

    def build_open_ai_tool_params(self) -> list[ChatCompletionToolParam]:
        # Generate OpenAI tool params to be used by the OpenAI SDK
        tool_params = []
        for _, func in self._name_to_function.items():
            function = generate_openai_function_schema(func, use_gemini_format=self.use_gemini_format)
            tool_params.append(ChatCompletionToolParam(function=function, type="function"))
        return tool_params
