from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["general"])


@router.get(
    "/heartbeat",
    summary="Check if the API is alive",
    response_model=bool,
)
def heartbeat():
    return True


@router.get(
    "/",
    summary="Redirection to /docs",
)
def root_to_docs():
    return RedirectResponse("/docs")
