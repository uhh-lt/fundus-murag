from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from fundus_murag.data.vector_db import VectorDB


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting FUNDus! Data API")
    vdb = vdb = VectorDB()
    yield
    # Shutdown
    vdb.close()
    logger.info("Stopping FUNDus! Data API")
