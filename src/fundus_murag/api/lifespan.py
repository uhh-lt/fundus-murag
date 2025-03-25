from contextlib import asynccontextmanager

import mlflow
from fastapi import FastAPI
from loguru import logger

from fundus_murag.agent.chat_assistant_factory import ChatAssistantFactory
from fundus_murag.agent.fundus_multi_agent_system_factory import FundusMultiAgentSystemFactory
from fundus_murag.config import load_config
from fundus_murag.data.user_image_store import UserImageStore
from fundus_murag.data.vector_db import VectorDB


@asynccontextmanager
async def api_lifespan(app: FastAPI):
    # Startup
    config = load_config()
    mlflow.set_tracking_uri(f"http://{config.mlflow.host}:{config.mlflow.port}")
    mlflow.set_experiment("/fundus")
    mlflow.openai.autolog()
    logger.info("Starting FUNDus! Data API")
    chat_assistant_factory = ChatAssistantFactory()
    fundus_agent_factory = FundusMultiAgentSystemFactory()
    vdb = VectorDB()
    user_image_store = UserImageStore()
    yield
    # Shutdown
    vdb.close()
    del vdb
    del chat_assistant_factory
    del fundus_agent_factory
    del user_image_store
    logger.info("Stopping FUNDus! Data API")
