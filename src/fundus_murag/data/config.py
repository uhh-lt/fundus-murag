from weaviate.classes.config import (
    Configure,
    DataType,
    Property,
    ReferenceProperty,
    Tokenization,
    VectorDistances,
)

FUNDUS_RECORD_SCHEMA_NAME = "FundusRecord"
FUNDUS_RECORD_SCHEMA_VECTORIZER = [
    Configure.NamedVectors.none(
        name="record_title",
        vector_index_config=Configure.VectorIndex.hnsw(
            distance_metric=VectorDistances.COSINE,
        ),
    ),
    Configure.NamedVectors.none(
        name="record_image",
        vector_index_config=Configure.VectorIndex.hnsw(
            distance_metric=VectorDistances.COSINE
        ),
    ),
]
FUNDUS_RECORD_SCHEMA_PROPS = [
    Property(
        name="murag_id",
        data_type=DataType.TEXT,
        tokenization=Tokenization.FIELD,
        description="The unique identifier of the FundusRecord in the VectorDB",
        skip_vectorization=True,
        vectorize_property_name=False,
    ),
    Property(
        name="fundus_id",
        data_type=DataType.INT,
        description="The identifier of the FundusRecord. There can be multiple FundusRecords with the same fundus_id!",
        skip_vectorization=True,
        vectorize_property_name=False,
    ),
    Property(
        name="title",
        data_type=DataType.TEXT,
        tokenization=Tokenization.WORD,
        description="The title of the parent FUNDus! Collection",
        skip_vectorization=True,
        vectorize_property_name=False,
    ),
    Property(
        name="collection_name",
        data_type=DataType.TEXT,
        tokenization=Tokenization.FIELD,
        description="The id of the parent FUNDus! Collection",
        skip_vectorization=True,
        vectorize_property_name=False,
    ),
    Property(
        name="catalogno",
        data_type=DataType.TEXT,
        tokenization=Tokenization.FIELD,
        description="The catalog number of the FundusRecord in the VectorDB",
        skip_vectorization=True,
        vectorize_property_name=False,
    ),
    Property(
        name="image_name",
        data_type=DataType.TEXT,
        tokenization=Tokenization.FIELD,
        description="The name of one of the images of the FundusRecord",
        skip_vectorization=True,
        vectorize_property_name=False,
    ),
    Property(
        name="image",
        data_type=DataType.BLOB,
        description="One of the images of the FundusRecord",
        skip_vectorization=True,
        vectorize_property_name=False,
    ),
    Property(
        name="details",
        data_type=DataType.OBJECT_ARRAY,
        description="A dictionary with additional details of the FundusRecord",
        skip_vectorization=True,
        vectorize_property_name=False,
        nested_properties=[
            Property(
                name="key",
                data_type=DataType.TEXT,
                description="The key of the detail",
                skip_vectorization=True,
                vectorize_property_name=False,
                tokenization=Tokenization.FIELD,
            ),
            Property(
                name="value",
                data_type=DataType.TEXT,
                description="The value of the detail",
                skip_vectorization=True,
                vectorize_property_name=False,
                tokenization=Tokenization.FIELD,
            ),
        ],
    ),
]
FUNDUS_RECORD_SCHEMA_REFS = [
    ReferenceProperty(
        name="parent_collection",
        target_collection="FundusCollection",
        description="The parent FundusCollection",
    )
]


FUNDUS_COLLECTION_SCHEMA_NAME = "FundusCollection"
FUNDUS_COLLECTION_SCHEMA_VECTORIZER = Configure.Vectorizer.none()
FUNDUS_COLLECTION_SCHEMA_VECTOR_INDEX_CONFIG = Configure.VectorIndex.hnsw(
    distance_metric=VectorDistances.COSINE
)
FUNDUS_COLLECTION_SCHEMA_PROPS = [
    Property(
        name="murag_id",
        data_type=DataType.TEXT,
        tokenization=Tokenization.FIELD,
        description="The unique identifier of the FundusCollection in the VectorDB",
        skip_vectorization=True,
        vectorize_property_name=False,
    ),
    Property(
        name="collection_name",
        data_type=DataType.TEXT,
        tokenization=Tokenization.FIELD,
        description="The unique name of the FundusCollection",
        skip_vectorization=True,
        vectorize_property_name=False,
    ),
    Property(
        name="title",
        data_type=DataType.TEXT,
        tokenization=Tokenization.WORD,
        description="The title of the FundusCollection in English",
        skip_vectorization=True,
        vectorize_property_name=False,
    ),
    Property(
        name="title_de",
        data_type=DataType.TEXT,
        tokenization=Tokenization.WORD,
        description="The title of the FundusCollection in German",
        skip_vectorization=True,
        vectorize_property_name=False,
    ),
    Property(
        name="description",
        data_type=DataType.TEXT,
        tokenization=Tokenization.WORD,
        description="The description of the FundusCollection in English",
        skip_vectorization=True,
        vectorize_property_name=False,
    ),
    Property(
        name="description_de",
        data_type=DataType.TEXT,
        tokenization=Tokenization.WORD,
        description="The description of the FundusCollection in German",
        skip_vectorization=True,
        vectorize_property_name=False,
    ),
    Property(
        name="title_fields",
        data_type=DataType.TEXT_ARRAY,
        description="The fields that are used in the title of the FundusCollection",
        skip_vectorization=True,
        vectorize_property_name=False,
    ),
    Property(
        name="fields",
        data_type=DataType.OBJECT_ARRAY,
        description="The fields of the FundusCollection",
        skip_vectorization=True,
        vectorize_property_name=False,
        nested_properties=[
            Property(
                name="name",
                data_type=DataType.TEXT,
                description="The name of the field",
                skip_vectorization=True,
                vectorize_property_name=False,
                tokenization=Tokenization.FIELD,
            ),
            Property(
                name="label_en",
                data_type=DataType.TEXT,
                description="The label of the field in English",
                skip_vectorization=True,
                vectorize_property_name=False,
                tokenization=Tokenization.FIELD,
            ),
            Property(
                name="label_de",
                data_type=DataType.TEXT,
                description="The label of the field in German",
                skip_vectorization=True,
                vectorize_property_name=False,
                tokenization=Tokenization.FIELD,
            ),
        ],
    ),
    Property(
        name="contacts",
        data_type=DataType.OBJECT_ARRAY,
        description="The contacts of the FundusCollection",
        skip_vectorization=True,
        vectorize_property_name=False,
        nested_properties=[
            Property(
                name="city",
                data_type=DataType.TEXT,
                description="The city of the contact",
                skip_vectorization=True,
                vectorize_property_name=False,
                tokenization=Tokenization.FIELD,
            ),
            Property(
                name="contact_name",
                data_type=DataType.TEXT,
                description="The name of the contact",
                skip_vectorization=True,
                vectorize_property_name=False,
                tokenization=Tokenization.FIELD,
            ),
            Property(
                name="department",
                data_type=DataType.TEXT,
                description="The department of the contact",
                skip_vectorization=True,
                vectorize_property_name=False,
                tokenization=Tokenization.FIELD,
            ),
            Property(
                name="email",
                data_type=DataType.TEXT,
                description="The email of the contact",
                skip_vectorization=True,
                vectorize_property_name=False,
                tokenization=Tokenization.FIELD,
            ),
            Property(
                name="institution",
                data_type=DataType.TEXT,
                description="The institution of the contact",
                skip_vectorization=True,
                vectorize_property_name=False,
                tokenization=Tokenization.FIELD,
            ),
            Property(
                name="position",
                data_type=DataType.TEXT,
                description="The position of the contact",
                skip_vectorization=True,
                vectorize_property_name=False,
                tokenization=Tokenization.FIELD,
            ),
            Property(
                name="street",
                data_type=DataType.TEXT,
                description="The street of the contact",
                skip_vectorization=True,
                vectorize_property_name=False,
                tokenization=Tokenization.FIELD,
            ),
            Property(
                name="tel",
                data_type=DataType.TEXT,
                description="The telephone number of the contact",
                skip_vectorization=True,
                vectorize_property_name=False,
                tokenization=Tokenization.FIELD,
            ),
            Property(
                name="www_department",
                data_type=DataType.TEXT,
                description="The website of the department",
                skip_vectorization=True,
                vectorize_property_name=False,
                tokenization=Tokenization.FIELD,
            ),
            Property(
                name="www_name",
                data_type=DataType.TEXT,
                description="The website of the contact",
                skip_vectorization=True,
                vectorize_property_name=False,
                tokenization=Tokenization.FIELD,
            ),
        ],
    ),
]
