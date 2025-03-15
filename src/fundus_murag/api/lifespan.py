from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from fundus_murag.assistant.assistant_factory import AssistantFactory
from fundus_murag.data.vector_db import VectorDB


@asynccontextmanager
async def api_lifespan(app: FastAPI):
    # Startup
    logger.info("Starting FUNDus! Data API")
    vdb = VectorDB()
    assistant_factory = AssistantFactory()
    yield
    # Shutdown
    vdb.close()
    del vdb
    del assistant_factory
    logger.info("Stopping FUNDus! Data API")
