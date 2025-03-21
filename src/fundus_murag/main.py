import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.routing import APIRoute

from fundus_murag.logging_config import setup_logging

setup_logging()

from fundus_murag.api.lifespan import api_lifespan  # noqa: E402


# Custom method to generate OpenApi function names
def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


app = FastAPI(
    title="Fundus MURAG API",
    description="The Fundus MURAG API",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=api_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
app.add_middleware(GZipMiddleware, minimum_size=500)

# Include routers after app is created
from fundus_murag.api.routers import (  # noqa: E402
    agents,
    assistant,
    general,
    lookup,
    random,
    search,
)

app.include_router(general.router)
app.include_router(lookup.router)
app.include_router(random.router)
app.include_router(search.router)
app.include_router(agents.router)
app.include_router(assistant.router)


def run_api():
    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", 8000))

    uvicorn.run(
        "fundus_murag.merged_api:app",
        host=host,
        port=port,
        reload=bool(int(os.environ.get("DEBUG", "0"))),
    )


if __name__ == "__main__":
    run_api()
