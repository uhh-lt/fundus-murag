from typing import Callable
from fastapi.encoders import jsonable_encoder
import srsly

from fundus_murag.assistant.tools import (
    LOOKUP_FUNCTIONS,
    SEARCH_FUNCTIONS,
    ML_FUNCTIONS,
    IMAGE_ANALYSIS_FUNCTIONS,
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

    def get_registered_functions(self) -> list[str]:
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
