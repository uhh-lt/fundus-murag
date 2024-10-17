from vertexai.generative_models import (
    FunctionDeclaration,
    Tool,
)

from typing import Callable

from fundus_murag.assistant.gemini_image_analysis_assistant import (
    GeminiImageAnalysisAssistant,
)
from fundus_murag.data.vector_db import VectorDB
from fundus_murag.ml.client import FundusMLClient
from fundus_murag.assistant.gemini_query_rewriter_assistant import (
    GeminiQueryRewriterAssistant,
)

__VDB__ = VectorDB()
__ML_CLIENT__ = FundusMLClient()
__QUERY_REWRITER__ = GeminiQueryRewriterAssistant()
__IMAGE_ANALYSIS_ASSISTANT__ = GeminiImageAnalysisAssistant()

LOOKUP_FUNCTIONS: dict[str, Callable] = {
    "get_total_number_of_fundus_collections": __VDB__.get_total_number_of_fundus_collections,
    "get_total_number_of_fundus_records": __VDB__.get_total_number_of_fundus_records,
    "get_number_of_records_in_collection": __VDB__.get_number_of_records_in_collection,
    "get_number_of_records_per_collection": __VDB__.get_number_of_records_per_collection,
    "list_all_fundus_collections": __VDB__.list_all_fundus_collections,
    "get_random_fundus_collection": __VDB__.get_random_fundus_collection,
    "get_random_fundus_records": __VDB__.get_random_fundus_records,
    "get_fundus_record_by_murag_id": __VDB__.get_fundus_record_by_murag_id,
    "get_fundus_records_by_fundus_id": __VDB__.get_fundus_records_by_fundus_id,
    "get_fundus_collection_by_name": __VDB__.get_fundus_collection_by_name,
}

SEARCH_FUNCTIONS: dict[str, Callable] = {
    "fundus_collection_lexical_search": __VDB__.fundus_collection_lexical_search,
    "fundus_record_title_lexical_search": __VDB__.fundus_record_title_lexical_search,
    "find_fundus_records_with_similar_image": __VDB__.find_fundus_records_with_similar_image,
    "find_fundus_records_with_images_similar_to_the_text_query": __VDB__.find_fundus_records_with_images_similar_to_the_text_query,
    # "find_fundus_records_with_titles_similar_to_the_text_query": __VDB__.find_fundus_records_with_titles_similar_to_the_text_query,
}

ML_FUNCTIONS: dict[str, Callable] = {
    "compute_image_embedding": __ML_CLIENT__.compute_image_embedding,
    "compute_text_embedding": __ML_CLIENT__.compute_text_embedding,
}

RAG_FUNCTIONS: dict[str, Callable] = {
    "rewrite_user_query_for_cross_modal_text_image_search": __QUERY_REWRITER__.rewrite_user_query_for_cross_modal_text_image_search,
}

IMAGE_ANALYSIS_FUNCTIONS: dict[str, Callable] = {
    "answer_question_about_fundus_record_image": __IMAGE_ANALYSIS_ASSISTANT__.answer_question_about_fundus_record_image,
    "generate_caption_for_fundus_record_image": __IMAGE_ANALYSIS_ASSISTANT__.generate_caption_for_fundus_record_image,
}

LOOKUP_TOOL = Tool(
    function_declarations=[
        FunctionDeclaration.from_func(f) for f in LOOKUP_FUNCTIONS.values()
    ],
)
SEARCH_TOOL = Tool(
    function_declarations=[
        FunctionDeclaration.from_func(f) for f in SEARCH_FUNCTIONS.values()
    ],
)
ML_TOOL = Tool(
    function_declarations=[
        FunctionDeclaration.from_func(f) for f in ML_FUNCTIONS.values()
    ],
)

IMAGE_ANALYSIS_TOOL = Tool(
    function_declarations=[
        FunctionDeclaration.from_func(f) for f in IMAGE_ANALYSIS_FUNCTIONS.values()
    ],
)

# unfortunately, the currently only a single tool is supported, so we merge all functions into a single tool
FUNDUS_TOOL = Tool(
    function_declarations=[
        FunctionDeclaration.from_func(f)
        for f in (
            LOOKUP_FUNCTIONS | SEARCH_FUNCTIONS | IMAGE_ANALYSIS_FUNCTIONS
        ).values()
    ]
)
