import inspect
from typing import Callable, List, get_type_hints

import srsly
from fastapi.encoders import jsonable_encoder

from fundus_murag.assistant.tools import (
    IMAGE_ANALYSIS_FUNCTIONS,
    LOOKUP_FUNCTIONS,
    ML_FUNCTIONS,
    SEARCH_FUNCTIONS,
)


class FunctionCallHandler:
    def __init__(self, auto_register_tools: bool = True):
        self._name_to_function = {}
        if auto_register_tools:
            self._register_tools()

    def _register_tools(self):
        for tool in [
            LOOKUP_FUNCTIONS,
            SEARCH_FUNCTIONS,
            ML_FUNCTIONS,
            IMAGE_ANALYSIS_FUNCTIONS,
        ]:
            for name, func in tool.items():
                self.register_function(name, func)

    def register_function(self, name: str, func: Callable) -> None:
        self._name_to_function[name] = func

    def get_registered_functions(self) -> List[str]:
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
        res = self._name_to_function[name](**kwargs)
        if convert_results_to_json:
            return self._res_to_json(res)
        return res

    def _res_to_json(self, res) -> str:
        return srsly.json_dumps(jsonable_encoder(res))

    def get_tool_schema_list(self) -> List[dict]:
        """
        Generate a list of JSON schemas for each registered function.
        Each schema follows the OpenAI function calling format.
        """
        schemas = []
        for func_name, func in self._name_to_function.items():
            try:
                type_hints = get_type_hints(func, globals(), locals())
            except Exception:
                type_hints = {}
            sig = inspect.signature(func)
            properties = {}
            required = []
            for param in sig.parameters.values():
                if param.name in ("self", "cls"):
                    continue
                param_type = type_hints.get(param.name, str)
                # Map common Python types to JSON types.
                mapping = {
                    int: "number",
                    float: "number",
                    bool: "boolean",
                    str: "string",
                }
                json_type = mapping.get(param_type, "string")
                properties[param.name] = {
                    "type": json_type,
                    "description": f"Parameter '{param.name}' of type {json_type}.",
                }
                if param.default == inspect.Parameter.empty:
                    required.append(param.name)
            schema = {
                "name": func_name,
                "description": func.__doc__.strip()
                if func.__doc__
                else f"No description provided for {func_name}.",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            }
            schemas.append(schema)
        return schemas
