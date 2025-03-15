from enum import Enum
from typing import Callable

from openai.types.shared_params.function_definition import FunctionDefinition
from vertexai.generative_models import FunctionDeclaration, Tool

from fundus_murag.assistant.gemini_image_analysis_assistant import (
    GeminiImageAnalysisAssistant,
)
from fundus_murag.assistant.gemini_query_rewriter_assistant import (
    GeminiQueryRewriterAssistant,
)
from fundus_murag.assistant.tools.function_schema import function_schema
from fundus_murag.data.vector_db import VectorDB
from fundus_murag.ml.client import FundusMLClient


class FundusTool(str, Enum):
    LOOKUP = "LOOKUP"
    SIM_SEARCH = "SIM_SEARCH"
    LEX_SEARCH = "LEX_SEARCH"
    IMAGE_ANALYSIS = "IMAGE_ANALYSIS"


__VDB__ = VectorDB()
__ML_CLIENT__ = FundusMLClient()
__QUERY_REWRITER__ = GeminiQueryRewriterAssistant()
__IMAGE_ANALYSIS_ASSISTANT__ = GeminiImageAnalysisAssistant()

__LOOKUP_FUNCTIONS__: dict[str, Callable] = {
    # RECORD LOOKUP FUNCTIONS
    "get_total_number_of_fundus_records": __VDB__.get_total_number_of_fundus_records,
    "get_number_of_records_per_collection": __VDB__.get_number_of_records_per_collection,
    "get_number_of_records_in_collection": __VDB__.get_number_of_records_in_collection,
    "get_random_fundus_records": __VDB__.get_random_fundus_records,
    "get_fundus_record_by_murag_id": __VDB__.get_fundus_record_by_murag_id,
    # COLLECTION LOOKUP FUNCTIONS
    "get_total_number_of_fundus_collections": __VDB__.get_total_number_of_fundus_collections,
    "list_all_fundus_collections": __VDB__.list_all_fundus_collections,
    "get_random_fundus_collection": __VDB__.get_random_fundus_collection,
    "get_fundus_collection_by_name": __VDB__.get_fundus_collection_by_name,
}

__LEX_SEARCH_FUNCTIONS__: dict[str, Callable] = {
    "fundus_collection_lexical_search": __VDB__.fundus_collection_lexical_search,
    "fundus_record_title_lexical_search": __VDB__.fundus_record_title_lexical_search,
}

__SIM_SEARCH_FUNCTIONS__: dict[str, Callable] = {
    "fundus_collection_title_similarity_search": __VDB__.fundus_collection_title_similarity_search,
    "fundus_collection_description_similarity_search": __VDB__.fundus_collection_description_similarity_search,
    "find_fundus_records_with_similar_image": __VDB__.find_fundus_records_with_similar_image,
    "find_fundus_records_with_images_similar_to_the_text_query": __VDB__.find_fundus_records_with_images_similar_to_the_text_query,
    "find_fundus_records_with_titles_similar_to_the_text_query": __VDB__.find_fundus_records_with_titles_similar_to_the_text_query,
}

__IMAGE_ANALYSIS_FUNCTIONS__: dict[str, Callable] = {
    "answer_question_about_fundus_record_image": __IMAGE_ANALYSIS_ASSISTANT__.answer_question_about_fundus_record_image,
    "generate_caption_for_fundus_record_image": __IMAGE_ANALYSIS_ASSISTANT__.generate_caption_for_fundus_record_image,
}

__TOOLS__: dict[str, dict[str, Callable]] = {
    FundusTool.LOOKUP: __LOOKUP_FUNCTIONS__,
    FundusTool.LEX_SEARCH: __LEX_SEARCH_FUNCTIONS__,
    FundusTool.SIM_SEARCH: __SIM_SEARCH_FUNCTIONS__,
    FundusTool.IMAGE_ANALYSIS: __IMAGE_ANALYSIS_FUNCTIONS__,
}


def get_tool_functions(tool: FundusTool) -> dict[str, Callable]:
    if tool not in __TOOLS__:
        raise ValueError(f"Tool {tool} not found")
    return __TOOLS__[tool]


def replace_integer_types(data):
    # helper function to replace 'integer' type with 'number' in the JSON schema
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            if key == "type" and value == "integer":
                new_data[key] = "number"
            else:
                new_data[key] = replace_integer_types(value)
        return new_data
    elif isinstance(data, list):
        return [replace_integer_types(item) for item in data]
    else:
        return data


def replace_type__with_type(data):
    # helper function to replace 'type_' with 'type' in the JSON schema
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            if key == "type_":
                new_data["type"] = value
            else:
                new_data[key] = replace_type__with_type(value)
        return new_data
    elif isinstance(data, list):
        return [replace_type__with_type(item) for item in data]
    else:
        return data


def upper_case_types(data):
    # helper function to uppercase all types in the JSON schema
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            if key == "type":
                new_data[key] = value.upper()
            else:
                new_data[key] = upper_case_types(value)
        return new_data
    elif isinstance(data, list):
        return [upper_case_types(item) for item in data]
    else:
        return data


def purge_titles(data):
    # helper function to remove parameter "title"s in the JSON schema
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            if key == "title" and "type" in data.keys():
                continue
            else:
                new_data[key] = purge_titles(value)
        return new_data
    elif isinstance(data, list):
        return [purge_titles(item) for item in data]
    else:
        return data


def purge_defaults(data):
    # helper function to remove parameter "default"s in the JSON schema
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            if key == "default" and "type" in data.keys():
                continue
            else:
                new_data[key] = purge_defaults(value)
        return new_data
    elif isinstance(data, list):
        return [purge_defaults(item) for item in data]
    else:
        return data


def get_openai_function_schema(
    func: Callable, use_gemini_format: bool = False
) -> FunctionDefinition:
    func_schema = function_schema(func)
    func_name = func_schema.name
    func_desc = func_schema.description

    if use_gemini_format:
        # this is a stupid but necessary hack to get the schema in the format accepted by Gemini because
        # Gemini expects OpenAPI schema but does not support AnyOf (Union) types nor default values. Also the FunctionDeclaration
        # generation outputs a schema with 'type_' instead of 'type' which is not supported by Gemini.
        params_schema = Tool(
            function_declarations=[FunctionDeclaration.from_func(func)]
        ).to_dict()["function_declarations"][0]["parameters"]
        params_schema = replace_type__with_type(params_schema)
        params_schema = purge_titles(params_schema)
        params_schema = purge_defaults(params_schema)
    else:
        params_schema = dict(func_schema.params_json_schema)
        # params_schema = replace_integer_types(params_schema)
        params_schema = purge_titles(params_schema)
        params_schema = purge_defaults(params_schema)

    # https://platform.openai.com/docs/guides/function-calling?api-mode=chat&lang=python#defining-functions
    func_def = FunctionDefinition(
        name=func_name,
        description=func_desc or "No description provided.",
        parameters=params_schema,  # type: ignore
        strict=True,
    )
    return func_def
