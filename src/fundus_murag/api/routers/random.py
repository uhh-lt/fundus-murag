from fastapi import APIRouter, HTTPException, Query

from fundus_murag.data.dtos.fundus import (
    FundusCollection,
    FundusRecord,
)
from fundus_murag.data.vector_db import VectorDB

router = APIRouter(prefix="/data/random", tags=["data/random"])


vdb = VectorDB()


@router.get(
    "/collections",
    response_model=FundusCollection,
    summary="Returns a random `FundusCollection` from FUNDus.",
)
def get_random_fundus_collection(
    n: int = Query(1, description="The number of random collections to return."),
):
    try:
        return vdb.get_random_fundus_collection(n=n)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/records",
    response_model=list[FundusRecord],
    summary="Returns N random `FundusRecord`s from FUNDus.",
)
def get_random_fundus_record(
    n: int = Query(1, description="The number of random records to return."),
    collection_name: str | None = Query(
        None, description="Unique internal name for the collection."
    ),
):
    try:
        return vdb.get_random_fundus_records(n=n, collection_name=collection_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
