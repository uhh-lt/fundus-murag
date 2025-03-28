import operator
import time
from functools import reduce
from typing import Any, Literal

import mlflow
import pandas as pd
import weaviate
from loguru import logger
from mlflow.entities import SpanType
from tqdm import tqdm
from weaviate.classes.query import Filter, MetadataQuery, QueryNested, QueryReference

from fundus_murag.agent.tools.query_rewriter import (
    QueryRewriter,
)
from fundus_murag.config import load_config
from fundus_murag.data.dtos.fundus import (
    FundusCollection,
    FundusRecord,
    FundusRecordImage,
    FundusRecordInternal,
)
from fundus_murag.data.dtos.vector_db import (
    FundusCollectionSemanticSearchResult,
    FundusRecordSemanticSearchResult,
)
from fundus_murag.data.schema import (
    FUNDUS_COLLECTION_SCHEMA_NAME,
    FUNDUS_COLLECTION_SCHEMA_VECTORIZER,
    FUNDUS_RECORD_SCHEMA_NAME,
    FUNDUS_RECORD_SCHEMA_REFS,
    FUNDUS_RECORD_SCHEMA_VECTORIZER,
)
from fundus_murag.data.user_image_store import UserImageStore
from fundus_murag.data.utils import (
    load_fundus_collection_embeddings_df,
    load_fundus_collections_df,
    load_fundus_record_embeddings_df,
    load_fundus_records_df,
    read_image_bytes,
)
from fundus_murag.ml.client import FundusMLClient
from fundus_murag.singleton_meta import SingletonMeta


class VectorDB(metaclass=SingletonMeta):
    def __init__(self):
        self._config = load_config()
        self._client = self._connect_to_weaviate()
        self._fundus_ml_client = FundusMLClient(self._config.fundus.ml_url)
        self._query_rewriter = QueryRewriter()
        self._user_image_store = UserImageStore()

        # we load the dataframes because some operations are faster and much easier to do in pandas
        self._records_df = load_fundus_records_df(
            self._config.data.records_df_file,
            self._config.app.dev_mode,
        )
        self._collections_df = load_fundus_collections_df(
            self._records_df,
            self._config.data.collections_df_file,
        )

        self._import_fundus_data(
            self._records_df,
            self._collections_df,
        )

    def __del__(self):
        try:
            self.close()
        except Exception as e:
            logger.error(f"Error while closing VectorDB: {e}")

    def _get_client(self) -> weaviate.WeaviateClient:
        if self._client.is_ready():
            return self._client

        MAX_RETRIES = 5
        while not self._client.is_ready() and MAX_RETRIES > 1:
            self._client = self._connect_to_weaviate()
            MAX_RETRIES -= 1
            time.sleep(1)

        self._client = self._connect_to_weaviate(raise_on_error=True)
        return self._client

    def close(self):
        self._get_client().close()

    def _connect_to_weaviate(self, raise_on_error: bool = False) -> weaviate.WeaviateClient:
        client = weaviate.connect_to_custom(
            http_host=self._config.weaviate.host,
            http_port=self._config.weaviate.http_port,
            http_secure=False,
            grpc_host=self._config.weaviate.host,
            grpc_port=self._config.weaviate.grpc_port,
            grpc_secure=False,
        )
        if not client.is_ready():
            msg = f"Cannot connect to Weaviate {self._config.weaviate.host}:{self._config.weaviate.http_port}!"
            logger.warning(msg)
            if raise_on_error:
                raise ConnectionError(msg)
        logger.info(f"Connected to Weaviate {self._config.weaviate.host}:{self._config.weaviate.http_port}")
        return client

    def is_initialized(self) -> bool:
        return self._get_client().collections.exists(
            FUNDUS_RECORD_SCHEMA_NAME
        ) and self._get_client().collections.exists(FUNDUS_COLLECTION_SCHEMA_NAME)

    def _create_fundus_record_schema(self) -> weaviate.collections.Collection:
        return self._get_client().collections.create(
            name=FUNDUS_RECORD_SCHEMA_NAME,
            # properties=FUNDUS_RECORD_SCHEMA_PROPS,  # comment out for auto schema creation
            vectorizer_config=FUNDUS_RECORD_SCHEMA_VECTORIZER,
            references=FUNDUS_RECORD_SCHEMA_REFS,  # type: ignore
        )

    def _get_fundus_record_collection(self) -> weaviate.collections.Collection:
        return self._get_client().collections.get(FUNDUS_RECORD_SCHEMA_NAME)

    def _create_fundus_collection_schema(self) -> weaviate.collections.Collection:
        return self._get_client().collections.create(
            name=FUNDUS_COLLECTION_SCHEMA_NAME,
            # properties=FUNDUS_COLLECTION_SCHEMA_PROPS, # comment out for auto schema creation
            # vector_index_config=FUNDUS_COLLECTION_SCHEMA_VECTOR_INDEX_CONFIG, #it is already set in FUNDUS_COLLECTION_SCHEMA_VECTORIZER
            vectorizer_config=FUNDUS_COLLECTION_SCHEMA_VECTORIZER,
        )

    def _get_fundus_collection_collection(self) -> weaviate.collections.Collection:
        return self._get_client().collections.get(FUNDUS_COLLECTION_SCHEMA_NAME)

    def _import_fundus_collections(self, collections_df: pd.DataFrame, collection_embeddings_df: pd.DataFrame) -> None:
        if self._get_client().collections.exists(FUNDUS_COLLECTION_SCHEMA_NAME):
            return

        logger.info("Importing FUNDus! Collections...")

        collection = self._create_fundus_collection_schema()

        for _, row in tqdm(
            collections_df.iterrows(),
            total=len(collections_df),
            desc="Importing FUNDus! collections",
            leave=True,
        ):
            title = row["title"] if not pd.isna(row["title"]) else row["title_de"]

            title_de = row["title_de"] if not pd.isna(row["title_de"]) else row["title"]

            props = {
                "murag_id": row["murag_id"],
                "collection_name": row["collection_name"],
                "title": title,
                "title_de": title_de,
                "description": (row["description"]),
                "description_de": (row["description_de"]),
                "contacts": row["contacts"],
                "title_fields": row["title_fields"],
                "fields": row["fields"],
            }

            collection_embeddings = collection_embeddings_df[
                collection_embeddings_df["collection_name"] == row["collection_name"]
            ]
            if len(collection_embeddings) == 0:
                vector = None
            elif len(collection_embeddings) == 1:
                vector = collection_embeddings.iloc[0]["embedding"]
            else:
                vector = {emb["embedding_name"]: emb["embedding"] for _, emb in collection_embeddings.iterrows()}

            collection.data.insert(
                properties=props,
                uuid=row["murag_id"],
                vector=vector,
            )

        logger.info(f"Imported {len(collections_df)} FUNDus! collections.")

    def _import_fundus_records(
        self,
        records_df: pd.DataFrame,
        collections_df: pd.DataFrame,
        record_embeddings_df: pd.DataFrame,
    ) -> None:
        if self._get_client().collections.exists(FUNDUS_RECORD_SCHEMA_NAME):
            return

        logger.info("Importing FUNDus! records...")

        collection = self._create_fundus_record_schema()
        with collection.batch.fixed_size(batch_size=100, concurrent_requests=16) as batch:
            for ridx, row in tqdm(
                records_df.iterrows(),
                total=len(records_df),
                desc="Importing FUNDus! records",
                leave=True,
            ):
                img_path = (self._config.data.fundus_data_root + "/" + row["image_path"]).replace("//", "/")
                try:
                    base64_image = read_image_bytes(img_path)
                except Exception:
                    logger.warning(f"Could not read image at {img_path}. Skipping...")
                    continue

                details = []
                for col in records_df.columns:
                    if col.startswith("details_"):
                        if row[col] is not None:
                            details.append(
                                {
                                    "key": col.replace("details_", ""),
                                    "value": (row[col]),
                                }
                            )

                props = {
                    "murag_id": row["murag_id"],
                    "fundus_id": row["fundus_id"],
                    "title": (row["title"]),
                    "collection_name": row["collection_name"],
                    "catalogno": row["catalogno"],
                    "image": base64_image,
                    "image_name": row["image_name"],
                    "details": details,
                }

                record_embeddings = record_embeddings_df[record_embeddings_df["murag_id"] == row["murag_id"]]
                if len(record_embeddings) == 0:
                    vector = None
                elif len(record_embeddings) == 1:
                    vector = record_embeddings.iloc[0]["embedding"]
                else:
                    vector = {emb["embedding_name"]: emb["embedding"] for _, emb in record_embeddings.iterrows()}

                batch.add_object(
                    uuid=row["murag_id"],
                    properties=props,
                    vector=vector,
                    references={
                        "parent_collection": collections_df[collections_df["collection_name"] == row["collection_name"]]
                        .iloc[0]
                        .murag_id
                    },
                )

                if ridx % 100 == 0:  # type: ignore
                    logger.info(f"Batched {ridx} FUNDus! records for import...")

        logger.info(f"Imported {len(records_df)} FUNDus! records.")

    def _import_fundus_data(
        self,
        records_df: pd.DataFrame,
        collections_df: pd.DataFrame,
    ) -> None:
        if self._config.app.reset_vdb_on_startup:
            self._delete_all_data()
        if not self.is_initialized():
            logger.info("Importing FUNDus! data...")
            record_embeddings_df = load_fundus_record_embeddings_df(
                self._records_df,
                self._config.data.record_embeddings_df_file,
                self._config.app.dev_mode,
            )
            collection_embeddings_df = load_fundus_collection_embeddings_df(
                self._config.data.collections_embeddings_df_file,
            )

            self._import_fundus_collections(collections_df, collection_embeddings_df)
            self._import_fundus_records(records_df, collections_df, record_embeddings_df)
            logger.info("FUNDus! data import complete.")
        else:
            logger.info("FUNDus! data already imported.")

    def _delete_all_data(self):
        logger.warning("Deleting all collections in Weaviate...")
        client = self._get_client()
        client.collections.delete_all()

    def _resolve_detail_field_names(self, details: list[dict[str, str]], collection_name: str) -> dict[str, str]:
        collection = self._collections_df[self._collections_df.collection_name == collection_name].iloc[0]
        fields = {f["name"]: f["label_en"] for f in collection.fields}
        resolved = {}
        for detail in details:
            if detail["value"] == "None" or detail["value"] == "":
                continue
            field_value = detail["value"]
            if detail["key"] == "ident_nr" or detail["key"] not in fields:
                field_name = detail["key"]
            else:
                field_name = fields[detail["key"]]

            resolved[field_name] = field_value

        return resolved

    def _create_fundus_collection_from_query_results(self, res: Any) -> list[FundusCollection]:
        collections = []
        for res_obj in res.objects:
            item_probs = res_obj.properties
            collection = FundusCollection(
                murag_id=str(item_probs["murag_id"]),
                collection_name=item_probs["collection_name"],
                title=item_probs["title"],
                description=item_probs["description"],
                title_de=item_probs["title_de"],
                description_de=item_probs["description_de"],
                contacts=item_probs["contacts"],
                title_fields=item_probs["title_fields"],
                fields=item_probs["fields"],
            )
            collections.append(collection)

        return collections

    def _create_fundus_record_from_query_results(self, res: Any) -> list[FundusRecord | FundusRecordInternal]:
        records = []
        for res_obj in res.objects:
            item_probs = res_obj.properties
            record_internal = None
            collection = None
            base64_image = None
            embeddings = dict()
            collection_name = item_probs["collection_name"]
            details = self._resolve_detail_field_names(item_probs["details"], collection_name)
            record = FundusRecord(
                murag_id=str(item_probs["murag_id"]),
                title=item_probs["title"],
                fundus_id=item_probs["fundus_id"],
                catalogno=item_probs["catalogno"],
                collection_name=collection_name,
                image_name=item_probs["image_name"],
                details=details,
            )

            if "image" in item_probs:
                base64_image = item_probs["image"]

            if res.objects[0].references is not None and "parent_collection" in res.objects[0].references:
                collection = self._create_fundus_collection_from_query_results(
                    res.objects[0].references["parent_collection"]
                )[0]

            embeddings = {}
            if res_obj.vector is not None:
                if isinstance(res_obj.vector, dict):
                    embeddings = res_obj.vector
                else:
                    embeddings["default"] = res_obj.vector

            if collection is not None and base64_image is not None:
                record_internal = FundusRecordInternal(
                    **record.model_dump(),
                    collection=collection,
                    base64_image=base64_image,
                    embeddings=embeddings,
                )

            records.append(record if record_internal is None else record_internal)

        return records

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def get_total_number_of_fundus_records(self) -> int:
        """
        Get the total number of FUNDus! records in the database.

        Returns:
            int: Total count of records.
        """
        try:
            collection = self._get_fundus_record_collection()
            agg = collection.aggregate.over_all(total_count=True)
            if agg.total_count is None:
                return 0
            return agg.total_count
        except Exception:
            return 0

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def get_total_number_of_fundus_collections(self) -> int:
        """
        Get the total number of FUNDus! collections in the database.

        Returns:
            int: Total count of collections.
        """
        try:
            collection = self._get_fundus_collection_collection()
            agg = collection.aggregate.over_all(total_count=True)
            if agg.total_count is None:
                return 0
            return agg.total_count
        except Exception:
            return 0

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def list_all_fundus_collections(self) -> list[FundusCollection]:
        """
        List all `FundusCollection`s in the FUNDus! database.

        Returns:
            list[`FundusCollection`]: A list of all collections.
        """
        collection = self._get_fundus_collection_collection()
        res = collection.query.fetch_objects()
        results = self._create_fundus_collection_from_query_results(res)
        return results

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def get_fundus_collection_by_murag_id(
        self,
        murag_id: str,
    ) -> FundusCollection:
        """
        Get a `FundusCollection` by its unique identifier.

        Args:
            murag_id (str): The unique identifier of the collection in the VectorDB.

        Returns:
            `FundusCollection`: The `FundusCollection` object with the specified `murag_id`.
        """
        collection = self._get_fundus_collection_collection()
        res = collection.query.fetch_objects(
            filters=Filter.by_property("murag_id").equal(murag_id),
            limit=1,
        )
        if len(res.objects) == 0:
            raise KeyError(f"FundusCollection with 'murag_id'={murag_id} not found!")

        results = self._create_fundus_collection_from_query_results(res)[0]
        return results

    def _resolve_collection_name(self, collection_name: str) -> str:
        # exact matches
        collection_name = collection_name.strip().lower()
        if "collection" in collection_name:
            collection_name = collection_name.replace("collection", "").strip()

        if collection_name in self._collections_df.collection_name:
            return collection_name
        elif collection_name in self._collections_df.title.str.lower():
            return self._collections_df[
                self._collections_df.title.str.lower() == collection_name
            ].collection_name.values[0]
        elif collection_name in self._collections_df.title_de.str.lower():
            return self._collections_df[
                self._collections_df.title_de.str.lower() == collection_name
            ].collection_name.values[0]

        # fuzzy matches
        collection_names = self._collections_df.collection_name.tolist()
        collection_titles = self._collections_df.title.str.lower().tolist()
        collection_titles_de = self._collections_df.title_de.str.lower().tolist()

        # pad all lists to the same length
        max_len = max(
            len(collection_names),
            len(collection_titles),
            len(collection_titles_de),
        )
        collection_names += [""] * (max_len - len(collection_names))
        collection_titles += [""] * (max_len - len(collection_titles))
        collection_titles_de += [""] * (max_len - len(collection_titles_de))

        matches = []
        for name, title, title_de in zip(
            collection_names,
            collection_titles,
            collection_titles_de,
        ):
            if collection_name in name or collection_name in title or collection_name in title_de:
                matches.append((name, title, title_de))

        if len(matches) == 0:
            raise KeyError(f"Collection with name '{collection_name}' not found!")
        elif len(matches) > 1:
            raise KeyError(
                f"Ambigious collection name `{collection_name}`! Multiple possible collections found: {matches}"
            )

        results = matches[0][0]
        return results

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def get_fundus_collection_by_name(
        self,
        collection_name: str,
    ) -> FundusCollection:
        """
        Get a `FundusCollection` by its name.

        Args:
            collection_name (str): The name of the collection.

        Returns:
            `FundusCollection`: The `FundusCollection` object with the specified `collection_name`.
        """
        collection_name = self._resolve_collection_name(collection_name)

        collection = self._get_fundus_collection_collection()
        res = collection.query.fetch_objects(
            filters=Filter.by_property("collection_name").equal(collection_name),
            limit=1,
        )
        if len(res.objects) == 0:
            raise KeyError(f"FundusCollection with 'collection_name'={collection_name} not found!")

        results = self._create_fundus_collection_from_query_results(res)
        return results[0]

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def get_random_fundus_collection(
        self,
        n: int = 1,
    ) -> list[FundusCollection]:
        """
        Get random `FundusCollection`s from the FUNDus! database.

        Args:
            n (int, optional): Number of collections to return. Defaults to 1

        Returns:
            `FundusCollection`: A random `FundusCollection` object.
        """
        if n > len(self._collections_df):
            logger.warning(f"Requested {n} random collections, but only {len(self._collections_df)} available.")
            n = len(self._collections_df)

        collection_names = self._collections_df.sample(int(n))["collection_name"].values[0]
        results = [self.get_fundus_collection_by_name(collection_name=cn) for cn in collection_names]
        return results

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def get_random_fundus_records(
        self,
        n: int = 1,
        collection_name: str | None = None,
    ) -> list[FundusRecord | FundusRecordInternal]:
        """
        Get N random `FundusRecord`s. If `collection_name` is specified, the records will be from the respective `FundusCollection`.

        Args:
            n (int, optional): Number of records to return. Defaults to 1
            collection_name (str, optional): An optional name of a `FundusCollection` specifying the records to return. If None, records will be from any `FundusCollection`. Defaults to None.

        Returns:
            list[`FundusRecord`]: A list of N `FundusRecord` objects.
        """
        if collection_name is not None:
            cn = self._resolve_collection_name(collection_name)
            records_in_collection = self._records_df[self._records_df["collection_name"] == cn]
            if len(records_in_collection) == 0:
                raise KeyError(f"Collection with name '{collection_name}' not found!")
        else:
            records_in_collection = self._records_df

        if n > len(records_in_collection):
            logger.warning(f"Requested {n} random records, but only {len(records_in_collection)} available.")
            n = len(records_in_collection)

        murag_ids = list(records_in_collection.sample(n=int(n))["murag_id"].values)

        results = [self.get_fundus_record_by_murag_id(murag_id=murag_id) for murag_id in murag_ids]
        return results

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def get_fundus_record_by_murag_id(
        self,
        murag_id: str,
    ) -> FundusRecord:
        """
        Get a `FundusRecord` by its unique identifier.

        Args:
            murag_id (str): The unique identifier of the record in the VectorDB.

        Returns:
            `FundusRecord`: The `FundusRecord` object with the specified `murag_id`.
        """

        collection = self._get_fundus_record_collection()
        res = collection.query.fetch_objects(
            filters=Filter.by_property("murag_id").equal(murag_id),
            return_references=[],  # return no references
        )
        if len(res.objects) == 0:
            raise KeyError(f"FundusRecord with murag_id={murag_id} not found!")

        results = self._create_fundus_record_from_query_results(res)
        return results[0]

    def get_fundus_record_image_by_murag_id(
        self,
        murag_id: str,
    ) -> FundusRecordImage:
        """
        Get a `FundusRecordImage` by its unique identifier.

        Args:
            murag_id (str): The unique identifier of the record in the VectorDB.

        Returns:
            `FundusRecordImage`: The `FundusRecordImage` object with the specified `murag_id`.
        """
        collection = self._get_fundus_record_collection()
        res = collection.query.fetch_objects(
            filters=Filter.by_property("murag_id").equal(murag_id),
            return_references=[],  # return no references
        )
        if len(res.objects) == 0:
            raise KeyError(f"FundusRecord with murag_id={murag_id} not found!")

        item_probs = res.objects[0].properties
        result = FundusRecordImage(
            murag_id=murag_id,
            fundus_id=item_probs["fundus_id"],  # type: ignore
            image_name=item_probs["image_name"],  # type: ignore
            base64_image=item_probs["image"],  # type: ignore
        )
        return result

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def get_fundus_records_by_fundus_id(
        self,
        fundus_id: int,
    ) -> list[FundusRecord | FundusRecordInternal]:
        """
        Returns all `FundusRecord`s that share the given `fundus_id`. If a `FundusRecord` has multiple images, the records share the `fundus_id`.

        Args:
            fundus_id (int): An identifier for the `FundusRecord`s.

        Returns:
            `FundusRecord`: The `FundusRecord` object(s) with the specified `fundus_id`.
        """

        collection = self._get_fundus_record_collection()
        res = collection.query.fetch_objects(
            filters=Filter.by_property("fundus_id").equal(fundus_id),
        )
        if len(res.objects) == 0:
            raise KeyError(f"FundusRecord with fundus_id={fundus_id} not found!")

        results = self._create_fundus_record_from_query_results(res)
        return results

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def find_fundus_records_with_similar_image(
        self,
        murag_id: str,
        search_in_collections: list[str] | None = None,
        top_k: int = 10,
    ) -> list[FundusRecordSemanticSearchResult]:
        """
        Find `FundusRecord`s with images similar to the one specified by the `murag_id`. This uses semantic similarity search based on image embeddings.

        Args:
            murag_id (str): The unique identifier of the record in the VectorDB.
            search_in_collections (list[str], optional): Names of `FundusCollection`s to restrict the search. Defaults to None.
            top_k (int, optional): Number of top results to return. Defaults to 10

        Returns:
            list[FundusRecordSemanticSearchResult]: `FundusRecord`s search results with similarity scores.
        """
        record = self.get_fundus_record_internal_by_murag_id(murag_id)
        image_embedding = self._fundus_ml_client.compute_image_embedding(
            record.base64_image, return_tensor="np"
        ).tolist()  # type: ignore
        results = self._fundus_record_image_similarity_search(
            image_embedding,
            search_in_collections=search_in_collections,
            top_k=top_k,
        )
        return results

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def find_fundus_records_with_images_similar_to_the_text_query(
        self,
        query: str,
        search_in_collections: list[str] | None = None,
        top_k: int = 10,
    ) -> list[FundusRecordSemanticSearchResult]:
        """
        Find `FundusRecord`s with images similar to the text query.
        This uses cross-modal text-image semantic similarity search based on multimodal embeddings.
        Use this to search for images similar to the text query.

        Args:
            query (str): The text query.
            search_in_collections (list[str], optional): Names of `FundusCollection`s to restrict the search. Defaults to None.
            top_k (int, optional): Number of top results to return. Defaults to 10

        Returns:
            list[FundusRecordSemanticSearchResult]: `FundusRecord`s search results with similarity scores.
        """
        query = self._query_rewriter.rewrite_user_query_for_cross_modal_text_to_image_search(query)
        text_embedding = self._fundus_ml_client.compute_text_embedding(query, return_tensor="np").tolist()  # type: ignore
        results = self._fundus_record_image_similarity_search(
            text_embedding,
            search_in_collections=search_in_collections,
            top_k=top_k,
        )
        return results

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def find_fundus_records_with_images_similar_to_user_image(
        self,
        user_image_id: str,
        search_in_collections: list[str] | None = None,
        top_k: int = 10,
    ) -> list[FundusRecordSemanticSearchResult]:
        """
        Find `FundusRecord`s with images similar to the user-provided image.
        This uses image similarity search based on image embeddings.
        Use this if a user provides an image and you want to find similar images in the database.

        Args:
            user_image_id (str): The unique identifier of the user-provided image.
            search_in_collections (list[str], optional): Names of `FundusCollection`s to restrict the search. Defaults to None.
            top_k (int, optional): Number of top results to return. Defaults to 10

        Returns:
            list[FundusRecordSemanticSearchResult]: `FundusRecord`s search results with similarity scores.
        """
        base64_user_image: str = self._user_image_store.load_user_image(user_image_id, base64=True)  # type: ignore
        base64_user_image = base64_user_image.split(",")[-1]
        image_embedding = self._fundus_ml_client.compute_image_embedding(
            base64_image=base64_user_image, return_tensor="np"
        ).tolist()  # type: ignore
        results = self._fundus_record_image_similarity_search(
            image_embedding,
            search_in_collections=search_in_collections,
            top_k=top_k,
        )
        return results

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def find_fundus_records_with_titles_similar_to_the_text_query(
        self,
        query: str,
        search_in_collections: list[str] | None = None,
        top_k: int = 10,
    ) -> list[FundusRecordSemanticSearchResult]:
        """
        Find `FundusRecord`s with titles similar to the text query.
        This uses textual semantic similarity search based on text embeddings.
        Use this only to search for records based on their titles.
        If you want to search for records based on their images, use `find_fundus_records_with_similar_image`.

        Args:
            query (str): The text query.
            search_in_collections (list[str], optional): Names of `FundusCollection`s to restrict the search. Defaults to None.
            top_k (int, optional): Number of top results to return. Defaults to 10

        Returns:
            list[FundusRecordSemanticSearchResult]: `FundusRecord`s search results with similarity scores.
        """
        # query = (
        #     self._query_rewriter.rewrite_user_query_for_cross_modal_text_image_search(
        #         query
        #     )
        # )
        text_embedding = self._fundus_ml_client.compute_text_embedding(query, return_tensor="np").tolist()  # type: ignore
        results = self._fundus_record_title_similarity_search(
            text_embedding,
            search_in_collections=search_in_collections,
            top_k=top_k,
        )
        return results

    def _fundus_record_image_similarity_search(
        self,
        query_embedding: list[float],
        search_in_collections: list[str] | None = None,
        top_k: int = 10,
        return_internal_records: bool = False,
    ) -> list[FundusRecordSemanticSearchResult]:
        """
        Perform a similarity search of `FundusRecord`s based on their image embedding.

        Args:
            query_embedding (list[float]): The query embedding vector.
            search_in_collections (list[str], optional): Names of `FundusCollection`s to restrict the search. Defaults to None.
            top_k (int, optional): Number of top results to return. Defaults to 10
            return_internal_record (bool, optional): Whether to return FundusRecordInternal objects. Defaults to False.

        Returns:
            list[FundusRecordSemanticSearchResult]: `FundusRecord`s search results with similarity scores.
        """
        results = self._fundus_record_similarity_search(
            query_embedding=query_embedding,
            target_vector="record_image",
            search_in_collections=search_in_collections,
            top_k=top_k,
            return_internal_records=return_internal_records,
        )
        return results

    def _fundus_record_title_similarity_search(
        self,
        query_embedding: list[float],
        search_in_collections: list[str] | None = None,
        top_k: int = 10,
        return_internal_records: bool = False,
    ) -> list[FundusRecordSemanticSearchResult]:
        """
        Perform a similarity search of `FundusRecord`s based on their title embedding.

        Args:
            query_embedding (list[float]): The query embedding vector.
            search_in_collections (list[str], optional): Names of `FundusCollection`s to restrict the search. Defaults to None.
            top_k (int, optional): Number of top results to return. Defaults to 10
            return_internal_record (bool, optional): Whether to return FundusRecordInternal objects. Defaults to False.

        Returns:
            list[FundusRecordSemanticSearchResult]: `FundusRecord`s search results with similarity scores.
        """
        results = self._fundus_record_similarity_search(
            query_embedding=query_embedding,
            target_vector="record_title",
            search_in_collections=search_in_collections,
            top_k=top_k,
            return_internal_records=return_internal_records,
        )
        return results

    def _fundus_record_similarity_search(
        self,
        query_embedding: list[float],
        target_vector: Literal["record_image", "record_title"],
        search_in_collections: list[str] | None = None,
        top_k: int = 10,
        return_internal_records: bool = False,
    ) -> list[FundusRecordSemanticSearchResult]:
        """
        Perform a similarity search of records via their image or title embedding.

        Args:
            query_embedding (list[float]): The query embedding vector.
            target_vector (Literal["record_image", "record_title"]): The target vector for the similarity search.
            search_in_collections (list[str], optional): Names of `FundusCollection`s to restrict the search. Defaults to None.
            top_k (int, optional): Number of top results to return. Defaults to 10
            return_internal_record (bool, optional): Whether to return FundusRecordInternal objects with additional data. Defaults to False.

        Returns:
            list[FundusRecordSemanticSearchResult]: `FundusRecord`s search results with similarity scores.
        """
        filters = None
        if search_in_collections is not None and len(search_in_collections) > 0:
            filters = reduce(
                operator.or_,
                [
                    Filter.by_property("collection_name").equal(self._resolve_collection_name(collection_name))
                    for collection_name in search_in_collections
                ],
            )

        collection = self._get_client().collections.get("FundusRecord")

        # Set up query parameters based on whether we need internal record data
        return_props = list(filter(lambda c: c != "details", FundusRecord.model_fields.keys())) + [
            QueryNested(name="details", properties=["key", "value"])
        ]
        return_references = None
        include_vector = False

        if return_internal_records:
            # Include image and parent collection reference for FundusRecordInternal
            return_props.append("image")
            return_references = QueryReference(link_on="parent_collection")
            include_vector = ["record_image", "record_title"]

        results = collection.query.near_vector(
            query_embedding,
            target_vector=target_vector,
            filters=filters,
            limit=int(top_k),
            return_metadata=MetadataQuery(certainty=True, distance=True),
            return_properties=return_props,
            return_references=return_references,
            include_vector=include_vector,
        )

        records = self._create_fundus_record_from_query_results(results)

        simsearch_results = []
        for record, res_obj in zip(records, results.objects):
            res = FundusRecordSemanticSearchResult(
                record=record,
                distance=res_obj.metadata.distance,  # type: ignore
                certainty=res_obj.metadata.certainty,  # type: ignore
            )

            simsearch_results.append(res)

        return simsearch_results

    def get_fundus_record_internal_by_murag_id(
        self,
        murag_id: str,
        include_vector: bool | list[Literal["record_image", "record_title"]] = False,
    ) -> FundusRecordInternal:
        """
        Get a `FundusRecordInternal` by its unique identifier.

        Args:
            murag_id (str): The unique identifier of the record in the VectorDB.

        Returns:
            `FundusRecordInternal`: The `FundusRecordInternal` object with the specified `murag_id`.
        """
        return_props = (
            list(filter(lambda c: c != "details", FundusRecord.model_fields.keys()))
            + [QueryNested(name="details", properties=["key", "value"])]
            + ["image"]
        )
        collection = self._get_fundus_record_collection()
        res = collection.query.fetch_objects(
            filters=Filter.by_property("murag_id").equal(murag_id),
            return_references=QueryReference(
                link_on="parent_collection",
            ),
            return_properties=return_props,
            include_vector=["record_image", "record_title"] if include_vector else False,
        )
        if len(res.objects) == 0:
            raise KeyError(f"FundusRecord with murag_id={murag_id} not found!")

        rec = self._create_fundus_record_from_query_results(res)
        if not isinstance(rec[0], FundusRecordInternal):
            raise ValueError(f"FundusRecordInternal not found for the given {murag_id=}!")

        return rec[0]

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def fundus_record_title_lexical_search(
        self,
        query: str,
        *,
        collection_name: str | None = None,
        top_k: int = 10,
    ) -> list[FundusRecord]:
        """
        Perform a lexical search for `FundusRecord`s using a query string. This searches only in the title field.
        If `collection_name` is specified, the search will be restricted to the specified collection.

        Args:
            query (str): The search query.
            collection_name (str, optional): Name of the `FundusCollection` to restrict the search. Defaults to None.
            top_k (int, optional): Number of top results to return. Defaults to 10

        Returns:
            list[FundusRecord]: `FundusRecord`s matching the search query.
        """

        results = self._fundus_record_lexical_search(
            query,
            search_in_collections=[collection_name] if collection_name is not None else None,
            top_k=top_k,
            search_in_title=True,
        )
        return results

    def _fundus_record_lexical_search(
        self,
        query: str,
        search_in_collections: list[str] | None = None,
        search_in_title: bool = True,
        top_k: int = 10,
    ) -> list[FundusRecord]:
        """
        Perform a lexical search for `FundusRecord`s using a query string.
        Currently this searches only in the title field but will be extended to other fields in the details.

        Args:
            query (str): The search query.
            search_in_collections (list[str], optional): Names of `FundusCollection`s to restrict the search. Defaults to None.
            top_k (int, optional): Number of top results to return. Defaults to 10

        Returns:
            list[FundusRecord]: `FundusRecord`s matching the search query.
        """
        if not search_in_title:
            raise NotImplementedError("Currently only title search is supported. Please set `search_in_title=True`.")

        filters = None
        if search_in_collections is not None and len(search_in_collections) > 0:
            filters = reduce(
                operator.or_,
                [
                    Filter.by_property("collection_name").equal(self._resolve_collection_name(collection_name))
                    for collection_name in search_in_collections
                ],
            )

        collection = self._get_client().collections.get("FundusRecord")

        results = collection.query.bm25(
            query,
            query_properties=["title"],
            filters=filters,
            limit=int(top_k),
        )

        results = self._create_fundus_record_from_query_results(results)
        return results

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def fundus_collection_lexical_search(
        self,
        query: str,
        *,
        top_k: int = 10,
    ) -> list[FundusCollection]:
        """
        Perform a lexical search for `FundusCollection`s using a query string.
        This searches in the collection ID, title, and description fields.

        Args:
            query (str): The search query.
            top_k (int, optional): Number of top results to return. Defaults to 10

        Returns:
            list[FundusCollection]: `FundusCollection`s matching the search query.
        """

        results = self._fundus_collection_lexical_search(
            query,
            top_k=int(top_k),
            search_in_collection_name=True,
            search_in_title=True,
            search_in_description=True,
            search_in_german_title=True,
            search_in_german_description=True,
        )
        return results

    def _fundus_collection_lexical_search(
        self,
        query: str,
        *,
        top_k: int = 10,
        search_in_collection_name: bool = True,
        search_in_title: bool = True,
        search_in_description: bool = True,
        search_in_german_title: bool = True,
        search_in_german_description: bool = True,
    ) -> list[FundusCollection]:
        """
        Perform a lexical search on `FundusCollection`s using a query string.

        Args:
            query (str): The search query.
            top_k (int, optional): Number of top results to return. Defaults to 10
            search_in_collection_name (bool, optional): Search in collection IDs if True. Defaults to True.
            search_in_title (bool, optional): Search in English titles if True. Defaults to True.
            search_in_description (bool, optional): Search in English descriptions if True. Defaults to True.
            search_in_german_title (bool, optional): Search in German titles if True. Defaults to True.
            search_in_german_description (bool, optional): Search in German descriptions if True. Defaults to True.

        Returns:
            list[FundusCollection]: `FundusCollection`s matching the search query.
        """

        collection = self._get_client().collections.get("FundusCollection")
        query_properties = []
        if search_in_collection_name:
            query_properties.extend(["collection_name"])
        if search_in_title:
            query_properties.extend(["title"])
        if search_in_description:
            query_properties.extend(["description"])
        if search_in_german_title:
            query_properties.extend(["title_de"])
        if search_in_german_description:
            query_properties.extend(["description_de"])

        if len(query_properties) == 0:
            raise ValueError("At least one property must be selected for search!")

        res = collection.query.bm25(
            query,
            query_properties=query_properties,
            limit=top_k,
        )

        results = self._create_fundus_collection_from_query_results(res)
        return results

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def fundus_collection_description_similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
    ) -> list[FundusCollectionSemanticSearchResult]:
        """
        Perform a similarity search of `FundusCollection`s based on their title embedding.

        Args:
            query_embedding (list[float]): The query embedding vector.
            top_k (int, optional): Number of top results to return. Defaults to 10

        Returns:
            list[FundusCollection]: `FundusCollection`s search results with similarity scores.
        """
        results = self._fundus_collection_similarity_search(
            query_embedding=query_embedding,
            target_vector="collection_description",
            top_k=int(top_k),
        )
        return results

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def fundus_collection_title_similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
    ) -> list[FundusCollectionSemanticSearchResult]:
        """
        Perform a similarity search of `FundusCollection`s based on their title embedding.

        Args:
            query_embedding (list[float]): The query embedding vector.
            top_k (int, optional): Number of top results to return. Defaults to 10

        Returns:
            list[FundusCollection]: `FundusCollection`s search results with similarity scores.
        """
        results = self._fundus_collection_similarity_search(
            query_embedding=query_embedding,
            target_vector="collection_title",
            top_k=int(top_k),
        )
        return results

    def _fundus_collection_similarity_search(
        self,
        query_embedding: list[float],
        target_vector: Literal["collection_title", "collection_description"],
        top_k: int = 10,
    ) -> list[FundusCollectionSemanticSearchResult]:
        """
        Perform a similarity search of `FundusCollection`s based on their title embedding.
        Returns structured results with certainty and distance scores.
        """
        collection = self._get_client().collections.get("FundusCollection")

        results = collection.query.near_vector(
            query_embedding,
            target_vector=target_vector,
            limit=int(top_k),
            return_metadata=MetadataQuery(certainty=True, distance=True),
        )

        collections = self._create_fundus_collection_from_query_results(results)

        # Convert results to FundusCollectionSemanticSearchResult with certainty & distance
        simsearch_results = []
        for collection, res_obj in zip(collections, results.objects):
            res = FundusCollectionSemanticSearchResult(
                **collection.model_dump(),
                distance=res_obj.metadata.distance,  # type: ignore
                certainty=res_obj.metadata.certainty,  # type: ignore
            )

            simsearch_results.append(res)

        results = simsearch_results
        return results

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def get_number_of_records_per_collection(self) -> dict[str, int]:
        """
        Get the number of records in each collection.

        Returns:
            dict[str, int]: A dictionary with the collection name as key and the number of records as value.
        """
        results = self._records_df.groupby("collection_name").size().to_dict()  # type: ignore
        return results

    @mlflow.trace(
        span_type=SpanType.TOOL,
    )
    def get_number_of_records_in_collection(self, collection_name: str) -> int:
        """
        Get the number of records in the specified collection.

        Returns:
            int: The number of records in the collection.
        """
        collection_name = self._resolve_collection_name(collection_name)
        results = len(self._records_df[self._records_df["collection_name"] == collection_name])
        return results
