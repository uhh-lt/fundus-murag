from pydantic import BaseModel, Field


class LexicalSearchQueryBase(BaseModel):
    query: str = Field(description="The query string.")
    top_k: int = Field(default=10, description="The number of results to return.")


class CollectionLexicalSearchQuery(LexicalSearchQueryBase):
    search_in_collection_name: bool = Field(default=True, description="Search in the name of the collection.")
    search_in_title: bool = Field(default=True, description="Search in the title of the collection.")
    search_in_description: bool = Field(default=True, description="Search in the description of the collection.")
    search_in_german_title: bool = Field(default=True, description="Search in the German title of the collection.")
    search_in_german_description: bool = Field(
        default=True, description="Search in the German description of the collection."
    )


class RecordLexicalSearchQuery(LexicalSearchQueryBase):
    collection_names: list[str] | None = Field(
        None,
        description="The names of the collections to search in. If None, search in all collections",
    )


class SimilaritySearchQuery(BaseModel):
    query: str = Field(
        description="The query string if it is a text search, or the base64 encoded image if it is an image search."
    )
    top_k: int = Field(default=10, description="The number of results to return.")
    confidence_threshold: float = Field(default=0.0, description="The minimum confidence threshold.")
    collection_names: list[str] | None = Field(
        None,
        description="The names of the collections to search in. If None, search in all collections. Only used for record searches.",
    )
