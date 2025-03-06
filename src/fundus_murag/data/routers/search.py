import base64

import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile

from fundus_murag.data.dto import (
    EmbeddingQuery,
    FundusCollection,
    FundusCollectionSemanticSearchResult,
    FundusRecord,
    FundusRecordSemanticSearchResult,
    LexicalSearchQuery,
    RecordLexicalSearchQuery,
)
from fundus_murag.data.vector_db import VectorDB
from fundus_murag.ml.client import FundusMLClient

router = APIRouter(prefix="/search", tags=["search"])

vdb = VectorDB()

ml_client = FundusMLClient()


@router.post(
    "/records/image_similarity_search",
    # "/records/image_similarity_search",
    response_model=list[FundusRecordSemanticSearchResult],
    summary="Perform a similarity search of records based on an image embedding.",
    tags=["search"],
)
def fundus_record_image_similarity_search(query: EmbeddingQuery):
    """
    Perform a similarity search of records based on an image embedding.

    Args:
        query (EmbeddingQuery): The embedding query parameters.

    Returns:
        List[FundusRecordSemanticSearchResult]: A list of search results.
    """
    try:
        query_embedding = np.array(query.query_embedding).tolist()
        return vdb._fundus_record_image_similarity_search(
            query_embedding=query_embedding,
            search_in_collections=query.search_in_collections,
            top_k=query.top_k,
            # return_image=query.return_image,
            # return_resolved_collection=query.return_parent_collection,
            # return_embeddings=query.return_embeddings,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/records/title_similarity_search",
    response_model=list[FundusRecordSemanticSearchResult],
    summary="Perform a similarity search of records based on a title embedding.",
    tags=["search"],
)
def fundus_record_title_similarity_search(query: EmbeddingQuery):
    """
    Perform a similarity search of records based on a title embedding.

    Args:
        query (EmbeddingQuery): The embedding query parameters.

    Returns:
        list[FundusRecordSemanticSearchResult]: A list of search results.
    """
    try:
        query_embedding = list(query.query_embedding)
        return vdb._fundus_record_title_similarity_search(
            query_embedding=query_embedding,
            search_in_collections=query.search_in_collections,
            top_k=query.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/records/title_lexical_search",
    response_model=list[FundusRecord],
    summary="Perform a lexical search on `FundusRecord`s by title.",
    tags=["search"],
)
def fundus_record_title_lexical_search(query: RecordLexicalSearchQuery):
    """
    Endpoint to search `FundusRecord`s based on title.

    Args:
        query (RecordLexicalSearchQuery): The search parameters.

    Returns:
        list[FundusRecord]: A list of `FundusRecord`s matching the query.
    """
    try:
        # Pass parameters to the vector database
        return vdb.fundus_record_title_lexical_search(
            query=query.query,
            collection_name=query.collection_name,
            top_k=query.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/collections/title_lexical_search",
    response_model=list[FundusCollection],
    summary="Perform a lexical search on `FundusCollection`s using a query string.",
    tags=["search"],
)
def fundus_collection_lexical_search(query: LexicalSearchQuery):
    """
    Perform a lexical search on `FundusCollection`s based on title.

    Args:
        query (LexicalSearchQuery): The search parameters.

    Returns:
        List[FundusCollection]: A list of matching collections.
    """
    try:
        return vdb._fundus_collection_lexical_search(
            query=query.query,
            top_k=query.top_k,
            search_in_collection_name=query.search_in_collection_name,
            search_in_title=query.search_in_title,
            search_in_description=query.search_in_description,
            search_in_german_title=query.search_in_german_title,
            search_in_german_description=query.search_in_german_description,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/collections/title_similarity_search",
    response_model=list[FundusCollectionSemanticSearchResult],
    summary="Perform a semantic similarity search on `FundusCollection`s based on their title.",
    tags=["search"],
)
def fundus_collection_title_similarity_search(query: EmbeddingQuery):
    """
    Perform a semantic similarity search on `FundusCollection`s based on their title.

    Args:
        query (EmbeddingQuery): The embedding query parameters.

    Returns:
        List[FundusCollectionSemanticSearchResult]: A list of search results.
    """
    try:
        query_embedding = list(query.query_embedding)
        return vdb.fundus_collection_title_similarity_search(
            query_embedding=query_embedding,
            top_k=query.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/collections/description_similarity_search",
    response_model=list[FundusCollectionSemanticSearchResult],  # Updated response model
    summary="Perform a semantic similarity search on `FundusCollection`s based on their title description.",
    tags=["search"],
)
def fundus_collection_description_similarity_search(query: EmbeddingQuery):
    """
    Perform a semantic similarity search on `FundusCollection`s based on their description.

    Args:
        query (EmbeddingQuery): The embedding query parameters.

    Returns:
        List[FundusCollectionSemanticSearchResult]: A list of search results.
    """
    try:
        query_embedding = list(query.query_embedding)
        return vdb.fundus_collection_description_similarity_search(
            query_embedding=query_embedding,
            top_k=query.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/image_to_image_search",
    response_model=list[FundusRecordSemanticSearchResult],
    summary="Upload an image, process it, and perform a similarity search.",
    tags=["image"],
)
async def image_to_image_search(file: UploadFile = File(...)):
    """
    Upload an image, find its embedding, perform a similarity search, and return a list of matching records.

    Args:
        file (UploadFile): Uploaded image file.

    Returns:
        List[FundusRecordSemanticSearchResult]: A list of search results.
    """
    try:
        image_bytes = await file.read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        #  FundusMLClient for image embedding
        embedding = ml_client.compute_image_embedding(image_base64, return_tensor="np")

        if (
            embedding is None
            or not isinstance(embedding, (np.ndarray, list))
            or len(embedding) == 0
        ):
            raise HTTPException(
                status_code=500, detail="Failed to retrieve embedding from ML server"
            )

        query_embedding = np.array(embedding).flatten().tolist()

        # Search in all collections `search_in_collections=None`
        search_query = EmbeddingQuery(
            query_embedding=query_embedding, search_in_collections=None
        )

        search_results = vdb._fundus_record_image_similarity_search(
            query_embedding=search_query.query_embedding,
            search_in_collections=search_query.search_in_collections,
            top_k=search_query.top_k,
        )
        return search_results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
