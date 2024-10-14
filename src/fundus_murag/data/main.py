from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fundus_murag.data.routers import general, search, lookup
from fundus_murag.data.setup import lifespan

import uvicorn


# custom method to generate OpenApi function names
def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


app = FastAPI(
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.add_middleware(GZipMiddleware, minimum_size=500)


app.include_router(general.router)
app.include_router(lookup.router)
app.include_router(search.router)


def main() -> None:
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=58008,
        log_level="debug",
        reload=False,
    )


if __name__ == "__main__":
    main()
