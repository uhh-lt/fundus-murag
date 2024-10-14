from fastapi import APIRouter, HTTPException, Query

from fundus_murag.data.dto import (
    FundusCollection,
    FundusRecord,
)
from fundus_murag.data.vector_db import VectorDB

router = APIRouter(prefix="/random", tags=["random"])


vdb = VectorDB()


@router.get(
    "/collection",
    response_model=FundusCollection,
    summary="Get a random `FundusCollection`",
    tags=["random"],
)
def get_fundus_collection_by_id():
    try:
        return vdb.get_random_fundus_collection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/record",
    response_model=list[FundusRecord],
    summary="Returns all `FundusRecord`s from FUNDus that share the `fundus_id`.",
    tags=["random"],
)
def get_fundus_records_by_id(
    fundus_id: int | None = Query(
        None,
        description="An identifier for the `FundusRecord`. If a `FundusRecord` has multiple images, the records share the `fundus_id`.",
    ),
    murag_id: str | None = Query(
        None, description="Unique identifier for the record in the VectorDB."
    ),
    return_image: bool = Query(False, description="Include image data if True."),
    return_parent_collection: bool = Query(
        False, description="Include parent collection data if True."
    ),
    return_embeddings: bool = Query(False, description="Include embeddings if True."),
):
    try:
        return vdb.get_fundus_records_by_id(
            fundus_id=fundus_id,
            murag_id=murag_id,
            return_image=return_image,
            return_parent_collection=return_parent_collection,
            return_embeddings=return_embeddings,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
