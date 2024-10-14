from fastapi import APIRouter, HTTPException, Query

from fundus_murag.data.dto import (
    FundusCollection,
    FundusRecord,
)
from fundus_murag.data.vector_db import VectorDB

router = APIRouter(prefix="/lookup", tags=["lookup"])


vdb = VectorDB()


@router.get(
    "/collections/count",
    summary="Get the total number of FUNDus! collections in the database.",
    tags=["lookup"],
)
def get_total_number_of_fundus_collections() -> int:
    try:
        return vdb.get_total_number_of_fundus_collections()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/collections/list",
    response_model=list[FundusCollection],
    summary="List all `FundusCollection`s in the FUNDus! database.",
    tags=["lookup"],
)
def list_all_collections():
    try:
        return vdb.list_all_fundus_collections()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/collections/get",
    response_model=FundusCollection,
    summary="Get a `FundusCollection` by its unique identifier.",
    tags=["lookup"],
)
def get_fundus_collection_by_id(
    collection_name: str | None = Query(
        None, description="Unique internal name for the collection."
    ),
    murag_id: str | None = Query(
        None, description="Unique identifier for the collection in the VectorDB."
    ),
):
    try:
        return vdb.get_fundus_collection_by_name(collection_name, murag_id=murag_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/collections/random",
    response_model=FundusCollection,
    summary="Returns a random `FundusCollection` from FUNDus.",
    tags=["lookup"],
)
def get_random_fundus_collection():
    try:
        return vdb.get_random_fundus_collection()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/collections/records",
    response_model=dict[str, int],
    summary="Get the number of records per collection.",
    tags=["lookup"],
)
def get_number_of_records_per_collection() -> dict[str, int]:
    """
    Get the number of records per collection.

    Returns:
        dict[str, int]: A dictionary with collection names as keys and the number of records as values.
    """
    try:
        return vdb.get_number_of_records_per_collection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/collections/{collection_name}/records/count",
    response_model=int,
    summary="Get the number of records per collection.",
    tags=["lookup"],
)
def get_number_of_records_in_collection(collection_name: str) -> int:
    """
    Get the number of records in the specified collection.

    Returns:
        int: The number of records in the collection.
    """
    try:
        return vdb.get_number_of_records_in_collection(collection_name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/records/count",
    summary="Get the total number of FUNDus! records in the database.",
    tags=["lookup"],
)
def get_total_number_of_fundus_records() -> int:
    try:
        return vdb.get_total_number_of_fundus_records()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/records/get",
    response_model=list[FundusRecord],
    summary="Returns all `FundusRecord`s from FUNDus that share the `fundus_id`.",
    tags=["lookup"],
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
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/records/random",
    response_model=FundusRecord,
    summary="Returns a random `FundusRecord` from FUNDus.",
    tags=["lookup"],
)
def get_random_fundus_record(
    return_image: bool = Query(False, description="Include image data if True."),
    return_parent_collection: bool = Query(
        False, description="Include parent collection data if True."
    ),
    return_embeddings: bool = Query(False, description="Include embeddings if True."),
):
    try:
        return vdb.get_random_fundus_record(
            return_image=return_image,
            return_parent_collection=return_parent_collection,
            return_embeddings=return_embeddings,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
