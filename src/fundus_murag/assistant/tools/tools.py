from typing import Callable

from fundus_murag.assistant.gemini_image_analysis_assistant import (
    GeminiImageAnalysisAssistant,
)
from fundus_murag.assistant.gemini_query_rewriter_assistant import (
    GeminiQueryRewriterAssistant,
)
from fundus_murag.data.vector_db import VectorDB
from fundus_murag.ml.client import FundusMLClient

__VDB__ = VectorDB()
__ML_CLIENT__ = FundusMLClient()
__QUERY_REWRITER__ = GeminiQueryRewriterAssistant()
__IMAGE_ANALYSIS_ASSISTANT__ = GeminiImageAnalysisAssistant()


class Tool:
    def __init__(self):
        self.functions: dict[str, Callable] = {}

    def register_functions(self, functions: dict[str, Callable]) -> None:
        self.functions.update(functions)


LOOKUP_TOOL = Tool()
LOOKUP_TOOL.register_functions(
    {
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
)

LEX_SEARCH_TOOL = Tool()
LEX_SEARCH_TOOL.register_functions(
    {
        "fundus_collection_lexical_search": __VDB__.fundus_collection_lexical_search,
        "fundus_record_title_lexical_search": __VDB__.fundus_record_title_lexical_search,
    }
)

SIM_SEARCH_TOOL = Tool()
SIM_SEARCH_TOOL.register_functions(
    {
        "fundus_collection_title_similarity_search": __VDB__.fundus_collection_title_similarity_search,
        "fundus_collection_description_similarity_search": __VDB__.fundus_collection_description_similarity_search,
        "find_fundus_records_with_similar_image": __VDB__.find_fundus_records_with_similar_image,
        "find_fundus_records_with_images_similar_to_the_text_query": __VDB__.find_fundus_records_with_images_similar_to_the_text_query,
        "find_fundus_records_with_titles_similar_to_the_text_query": __VDB__.find_fundus_records_with_titles_similar_to_the_text_query,
    }
)

IMAGE_ANALYSIS_TOOL = Tool()
IMAGE_ANALYSIS_TOOL.register_functions(
    {
        "answer_question_about_fundus_record_image": __IMAGE_ANALYSIS_ASSISTANT__.answer_question_about_fundus_record_image,
        "generate_caption_for_fundus_record_image": __IMAGE_ANALYSIS_ASSISTANT__.generate_caption_for_fundus_record_image,
        # add ocr
    }
)
