from typing import Callable


class Tool:
    def __init__(self, name: str):
        self.name = name
        self.functions: dict[str, Callable] = {}

    def register_functions(self, functions: dict[str, Callable]) -> None:
        self.functions.update(functions)

    def __str__(self) -> str:
        return f"Tool(Name={self.name}, Functions={list(self.functions.keys())})"

    def __repr__(self) -> str:
        return str(self)


def get_lookup_tool() -> Tool:
    # avoid circular imports
    from fundus_murag.data.vector_db import VectorDB

    vdb = VectorDB()
    lookup_tool = Tool(name="DB Lookup Tool")
    lookup_tool.register_functions(
        {
            # RECORD LOOKUP FUNCTIONS
            "get_total_number_of_fundus_records": vdb.get_total_number_of_fundus_records,
            "get_number_of_records_per_collection": vdb.get_number_of_records_per_collection,
            "get_number_of_records_in_collection": vdb.get_number_of_records_in_collection,
            "get_random_fundus_records": vdb.get_random_fundus_records,
            "get_fundus_record_by_murag_id": vdb.get_fundus_record_by_murag_id,
            # COLLECTION LOOKUP FUNCTIONS
            "get_total_number_of_fundus_collections": vdb.get_total_number_of_fundus_collections,
            "list_all_fundus_collections": vdb.list_all_fundus_collections,
            "get_random_fundus_collection": vdb.get_random_fundus_collection,
            "get_fundus_collection_by_name": vdb.get_fundus_collection_by_name,
        }
    )
    return lookup_tool


def get_lex_search_tool() -> Tool:
    # avoid circular imports
    from fundus_murag.data.vector_db import VectorDB

    vdb = VectorDB()

    lex_search_tool = Tool(name="Lexical Search Tool")
    # because VectorDB is a singleton, the methods of the instance are always the same and we can use them in the dict
    lex_search_tool.register_functions(
        {
            "fundus_collection_lexical_search": vdb.fundus_collection_lexical_search,
            "fundus_record_title_lexical_search": vdb.fundus_record_title_lexical_search,
        }
    )
    return lex_search_tool


def get_sim_search_tool() -> Tool:
    # avoid circular imports
    from fundus_murag.data.vector_db import VectorDB

    vdb = VectorDB()

    sim_search_tool = Tool(name="Similarity Search Tool")
    # because VectorDB is a singleton, the methods of the instance are always the same and we can use them in the dict
    sim_search_tool.register_functions(
        {
            "fundus_collection_title_similarity_search": vdb.fundus_collection_title_similarity_search,
            "fundus_collection_description_similarity_search": vdb.fundus_collection_description_similarity_search,
            "find_fundus_records_with_similar_image": vdb.find_fundus_records_with_similar_image,
            "find_fundus_records_with_images_similar_to_the_text_query": vdb.find_fundus_records_with_images_similar_to_the_text_query,
            "find_fundus_records_with_images_similar_to_the_user_image": vdb.find_fundus_records_with_images_similar_to_user_image,
            "find_fundus_records_with_titles_similar_to_the_text_query": vdb.find_fundus_records_with_titles_similar_to_the_text_query,
        }
    )

    return sim_search_tool


def get_image_analysis_tool() -> Tool:
    # avoid circular imports
    from fundus_murag.agent.tools.image_analyzer import ImageAnalyzer

    img_analyzer = ImageAnalyzer()
    image_analysis_tool = Tool(name="Image Analysis Tool")
    image_analysis_tool.register_functions(
        {
            "answer_question_about_fundus_record_image": img_analyzer.answer_question_about_fundus_record_image,
            "generate_caption_for_fundus_record_image": img_analyzer.generate_caption_for_fundus_record_image,
            "extract_text_from_fundus_record_image": img_analyzer.extract_text_from_fundus_record_image,
            "detect_objects_in_fundus_record_image": img_analyzer.detect_objects_in_fundus_record_image,
        }
    )
    return image_analysis_tool
