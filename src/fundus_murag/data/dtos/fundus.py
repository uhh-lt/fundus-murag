from pydantic import BaseModel, Field


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
    description: str
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


class FundusRecordImage(BaseModel):
    """
    A `FundusRecordImage` represents an image associated with a `FundusRecord`.

    Attributes:
        murag_id (str): A unique identifier for the `FundusRecord` in the VectorDB.
        fundus_id (int): An identifier for the `FundusRecord`. If a `FundusRecord` has multiple images, the records share the `fundus_id`.
        image_name (str): The name of the image file associated with the `FundusRecord`.
        base64_image (str): The base64 encoded image data of the `FundusRecord`.
    """

    murag_id: str
    fundus_id: int
    image_name: str
    base64_image: str
