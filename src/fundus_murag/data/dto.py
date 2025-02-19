from pydantic import BaseModel, Field


class LexicalSearchQuery(BaseModel):
    """
    A `LexicalSearchQuery` represents a query for a lexical search based on a text query.


    Attributes:
        query (str): The search query.
        top_k (int, optional): Number of top results to return. Defaults to 10.
        search_in_collection_name (bool, optional): Search in collection IDs if True. Defaults to True.
        search_in_title (bool, optional): Search in English titles if True. Defaults to True.
        search_in_description (bool, optional): Search in English descriptions if True. Defaults to True.
        search_in_german_title (bool, optional): Search in German titles if True. Defaults to True.
        search_in_german_description (bool, optional): Search in German descriptions if True. Defaults to True.
    """

    query: str
    top_k: int = 10
    search_in_collection_name: bool = True
    search_in_title: bool = True
    search_in_description: bool = True
    search_in_german_title: bool = True
    search_in_german_description: bool = True


class RecordLexicalSearchQuery(BaseModel):
    """
    A `RecordLexicalSearchQuery` represents a query for a lexical search of `FundusRecord`s by title.

    Attributes:
        query (str): The search query.
        top_k (int, optional): Number of top results to return. Defaults to 10.
        collection_name (str, optional): Restrict the search to a specific collection if provided.
    """

    query: str
    top_k: int = 10
    collection_name: str | None = None


class EmbeddingQuery(BaseModel):
    """
    A `EmbeddingQuery` represents a query for similarity search based on an image embedding.

    Attributes:
        query_embedding (np.ndarray): The query embedding vector.
        search_in_collections (list[str], optional): Collection IDs to restrict the search. Defaults to None.
        top_k (int, optional): Number of top results to return. Defaults to 10.
        return_image (bool, optional): Include image data if True. Defaults to False.
        return_parent_collection (bool, optional): Include parent collection data if True. Defaults to False.
        return_embeddings (bool, optional): Include embeddings if True. Defaults to False.
    """

    query_embedding: list[float]
    search_in_collections: list[str] | None = None
    top_k: int = 10
    return_image: bool = False
    return_parent_collection: bool = False
    return_embeddings: bool = False


class FundusCollectionContact(BaseModel):
    """
    A `FundusCollectionContact` represents a contact person for a `FundusCollection`.

    Attributes:
        city (str): The city of the contact person.
        contact_name (str): The name of the contact person.
        department (str): The department of the contact person.
        email (str): The email of the contact person.
        institution (str): The institution of the contact person.
        position (str): The position of the contact person.
        street (str): The street of the contact person.
        tel (str): The telephone number of the contact person.
        www_department (str): The department website of the contact person.
        www_name (str): The personal website of the contact person.
    """

    city: str
    contact_name: str
    department: str
    email: str
    institution: str
    position: str
    street: str
    tel: str
    www_department: str
    www_name: str


class FundusRecordField(BaseModel):
    """
    A `FundusRecordField` represents a field, i.e., detail of a `FundusRecord`. This is

    Attributes:
        name (str): The name of the field.
        label_en (str): The label of the field in English.
        label_de (str): The label of the field in German.
    """

    name: str
    label_en: str
    label_de: str


class FundusCollection(BaseModel):
    """
    A `FundusCollection` represents a collection of `FundusRecord`s with details such as a unique identifier,
    title, and description.

    Attributes:
        murag_id (str): Unique identifier for the collection in the VectorDB.
        collection_name (str): Unique identifier for the collection.
        title (str): Title of the collection in English.
        title_de (str): Title of the collection in German.
        description (str): Description of the collection in English.
        description_de (str): Description of the collection in German.
        contacts (list[FundusCollectionContact]): A list of contact persons for the collection.
        title_fields (list[str]): A list of fields that are used as titles for the `FundusRecord` in the collection.
        fields (list[FundusRecordField]): A list of fields for the `FundusRecord`s in the collection.
    """

    murag_id: str
    collection_name: str
    title: str
    title_de: str
    description: str = Field(default=None)
    description_de: str
    contacts: list[FundusCollectionContact] = Field(default_factory=list)
    title_fields: list[str] = Field(default_factory=list)
    fields: list[FundusRecordField] = Field(default_factory=list)


class FundusRecord(BaseModel):
    """
    A `FundusRecord` represents an record in the FUNDus collection, with details such as catalog number,
    associated collection, image name, and metadata.

    Attributes:
        murag_id (int): A unique identifier for the `FundusRecord` in the VectorDB.
        title (str): The title of the `FundusRecord`.
        fundus_id (int): An identifier for the `FundusRecord`. If a `FundusRecord` has multiple images, the records share the `fundus_id`.
        catalogno (str): The catalog number associated with the `FundusRecord`.
        collection_name (str): The unique name of the `FundusCollection` to which this `FundusRecord` belongs.
        image_name (str): The name of the image file associated with the `FundusRecord`.
        details (dict[str, str]): Additional metadata for the `FundusRecord`.
    """

    murag_id: str
    title: str
    fundus_id: int
    catalogno: str
    collection_name: str
    image_name: str
    details: dict[str, str] = Field(default_factory=dict)


class FundusRecordInternal(FundusRecord):
    """
    A `FundusRecordInternal` represents an internal record in the FUNDus collection, with details such as the base64 image,
    and embeddings.

    Attributes:
        base64_image (str | None, optional): The base64 encoded image data of the `FundusRecord`.
        collection (FundusCollection): The `FundusCollection` to which this `FundusRecord` belongs.
        embeddings (dict[str, float]): A dictionary containing embeddings for the `FundusRecord`, where keys are strings
            and values are the embeddings as lists of floats.
    """

    base64_image: str
    collection: FundusCollection
    embeddings: dict[str, list[float]] = Field(default_factory=dict)


class FundusRecordSemanticSearchResult(FundusRecord):
    """
    A `FundusRecordSemanticSearchResult` represents a semantic search result record with additional details such as
    certainty and distance scores.

    Attributes:
        certainty: float: The certainty score of the search result.
        distance: float: The distance between the query and the search result.
    """

    certainty: float
    distance: float


class FundusRecordInternalSemanticSearchResult(FundusRecordInternal):
    """
    A `FundusRecordInternalSemanticSearchResult` represents a semantic search result record with additional details such as
    certainty and distance scores.

    Attributes:
        certainty: float: The certainty score of the search result.
        distance: float: The distance between the query and the search result.
    """

    certainty: float
    distance: float


class FundusCollectionSemanticSearchResult(FundusCollection):
    """
    A `FundusCollectionSemanticSearchResult` represents a semantic search result for a `FundusCollection`,
    including additional details such as certainty and distance scores.

    Attributes:
        certainty (float): The certainty score of the search result.
        distance (float): The distance between the query and the search result.
    """

    certainty: float
    distance: float
