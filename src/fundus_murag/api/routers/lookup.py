from fastapi import APIRouter, HTTPException, Path, Query

from fundus_murag.data.dtos.fundus import (
    FundusCollection,
    FundusRecord,
    FundusRecordImage,
)
from fundus_murag.data.vector_db import VectorDB

router = APIRouter(prefix="/data/lookup", tags=["data/lookup"])


vdb = VectorDB()


@router.get(
    "/collections/count",
    summary="Get the total number of FUNDus! collections in the database.",
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
)
def list_all_collections():
    try:
        return vdb.list_all_fundus_collections()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/collections",
    response_model=FundusCollection,
    summary="Get a `FundusCollection` by its name or MURAG ID.",
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
        if collection_name:
            return vdb.get_fundus_collection_by_name(collection_name=collection_name)
        elif murag_id:
            return vdb.get_fundus_collection_by_murag_id(murag_id=murag_id)
        elif collection_name is None and murag_id is None:
            raise ValueError("Either `collection_name` or `murag_id` must be provided.")
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/collections/records/count",
    response_model=dict[str, int],
    summary="Get the number of records per collection.",
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
)
def get_number_of_records_in_collection(
    collection_name: str = Path(description="Unique internal name for the collection."),
) -> int:
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
)
def get_total_number_of_fundus_records() -> int:
    try:
        return vdb.get_total_number_of_fundus_records()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/records",
    response_model=FundusRecord | list[FundusRecord],
    summary="Get a `FundusRecord`s by its ID or the `FundusRecord` by MURAG ID.",
)
def get_fundus_records_by_id(
    fundus_id: int | None = Query(
        None,
        description="An identifier for the `FundusRecord`. If a `FundusRecord` has multiple images, the records share the `fundus_id`.",
    ),
    murag_id: str | None = Query(
        None, description="Unique identifier for the record in the VectorDB."
    ),
):
    try:
        if fundus_id is None and murag_id is None:
            raise ValueError("Either `fundus_id` or `murag_id` must be provided.")
        elif murag_id is not None and fundus_id is not None:
            raise ValueError(
                "Either `fundus_id` or `murag_id` must be provided, not both."
            )
        elif murag_id:
            record = vdb.get_fundus_record_by_murag_id(murag_id=murag_id)
        elif fundus_id:
            record = vdb.get_fundus_records_by_fundus_id(fundus_id=fundus_id)
        else:
            # This can never happen but the linter is not smart enough ...
            raise ValueError("Either `fundus_id` or `murag_id` must be provided.")

        return record
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/records/image",
    response_model=FundusRecordImage,
    summary="Returns the `FundusRecordImage`s from the `FundusRecord` with the specified `murag_id`.",
)
def get_fundus_record_image_by_murag_id(
    murag_id: str = Query(
        ..., description="Unique identifier for the `FundusRecord` in the VectorDB."
    ),
):
    try:
        record_img = vdb.get_fundus_record_image_by_murag_id(murag_id=murag_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return record_img
