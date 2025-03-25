from fastapi import APIRouter, HTTPException

from fundus_murag.data.dtos.fundus import (
    FundusCollection,
    FundusRecord,
)
from fundus_murag.data.dtos.search import (
    CollectionLexicalSearchQuery,
    RecordLexicalSearchQuery,
    SimilaritySearchQuery,
)
from fundus_murag.data.dtos.vector_db import (
    FundusCollectionSemanticSearchResult,
    FundusRecordSemanticSearchResult,
)
from fundus_murag.data.vector_db import VectorDB
from fundus_murag.ml.client import FundusMLClient

router = APIRouter(prefix="/data/search", tags=["data/search"])

vdb = VectorDB()
mlc = FundusMLClient()


@router.post(
    "/records/similar/i2i",
    response_model=list[FundusRecordSemanticSearchResult],
    summary="Perform a similarity search of record images via a query image.",
)
def fundus_record_i2i_similarity_search(query: SimilaritySearchQuery):
    try:
        query_embedding = mlc.compute_image_embedding(base64_image=query.query, return_tensor="np").tolist()  # type: ignore
        return vdb._fundus_record_image_similarity_search(
            query_embedding=query_embedding,
            search_in_collections=query.collection_names,
            top_k=query.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/records/similar/t2i",
    response_model=list[FundusRecordSemanticSearchResult],
    summary="Perform a similarity search of record images via a query string.",
)
def fundus_record_t2i_similarity_search(query: SimilaritySearchQuery):
    try:
        query_embedding = mlc.compute_text_embedding(text=query.query, return_tensor="np").tolist()  # type: ignore
        return vdb._fundus_record_image_similarity_search(
            query_embedding=query_embedding,
            search_in_collections=query.collection_names,
            top_k=query.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/records/similar/i2t",
    response_model=list[FundusRecordSemanticSearchResult],
    summary="Perform a similarity search of record titles via a query image.",
)
def fundus_record_i2t_similarity_search(query: SimilaritySearchQuery):
    try:
        query_embedding = mlc.compute_image_embedding(base64_image=query.query, return_tensor="np").tolist()  # type: ignore
        return vdb._fundus_record_title_similarity_search(
            query_embedding=query_embedding,
            search_in_collections=query.collection_names,
            top_k=query.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/records/similar/t2t",
    response_model=list[FundusRecordSemanticSearchResult],
    summary="Perform a similarity search of record titles via a query string.",
)
def fundus_record_t2t_similarity_search(query: SimilaritySearchQuery):
    try:
        query_embedding = mlc.compute_text_embedding(text=query.query, return_tensor="np").tolist()  # type: ignore
        return vdb._fundus_record_title_similarity_search(
            query_embedding=query_embedding,
            search_in_collections=query.collection_names,
            top_k=query.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/records/lexical/title",
    response_model=list[FundusRecord],
    summary="Perform a lexical search on `FundusRecord` titles using a query string.",
)
def fundus_record_title_lexical_search(query: RecordLexicalSearchQuery):
    try:
        return vdb._fundus_record_lexical_search(
            query=query.query,
            search_in_collections=query.collection_names,
            top_k=query.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/collections/lexical",
    response_model=list[FundusCollection],
    summary="Perform a lexical search on `FundusCollection`s using a query string.",
)
def fundus_collection_lexical_search(query: CollectionLexicalSearchQuery):
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
    "/collections/description/similar",
    response_model=list[FundusCollectionSemanticSearchResult],
    summary="Perform a semantic similarity search on `FundusCollection`s based on their description.",
)
def fundus_collection_description_similarity_search(query: SimilaritySearchQuery):
    query_embedding = mlc.compute_text_embedding(text=query.query, return_tensor="np").tolist()  # type: ignore
    try:
        return vdb.fundus_collection_description_similarity_search(
            query_embedding=query_embedding,
            top_k=query.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/collections/title/similar",
    response_model=list[SimilaritySearchQuery],
    summary="Perform a semantic similarity search on `FundusCollection`s based on their title.",
)
def fundus_collection_title_similarity_search(query: SimilaritySearchQuery):
    try:
        query_embedding = mlc.compute_text_embedding(text=query.query, return_tensor="np").tolist()  # type: ignore
        return vdb.fundus_collection_title_similarity_search(
            query_embedding=query_embedding,
            top_k=query.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
