from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get(
    "/heartbeat",
    tags=["general"],
    summary="Check if the API is alive",
    response_model=bool,
)
def heartbeat():
    return True


@router.get(
    "/",
    summary="Redirection to /docs",
    tags=["general"],
)
def root_to_docs():
    return RedirectResponse("/docs")
