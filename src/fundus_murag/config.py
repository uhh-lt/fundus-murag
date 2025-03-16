import os
from functools import lru_cache
from pathlib import Path

import yaml
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingConfig(BaseSettings):
    dir: str
    level: str


class DataConfig(BaseSettings):
    records_df_file: str
    collections_df_file: str
    record_embeddings_df_file: str
    collections_embeddings_df_file: str


class AppConfig(BaseSettings):
    dev_mode: bool
    reset_vdb_on_startup: bool


class WeaviateConfig(BaseSettings):
    host: str
    http_port: int
    grpc_port: int


class GoogleConfig(BaseSettings):
    project_id: str
    default_location: str
    application_credentials_file: str


class OpenAIConfig(BaseSettings):
    api_key: str


class FundusConfig(BaseSettings):
    ml_url: str


class AssistantConfig(BaseSettings):
    default_model: str


class Config(BaseSettings):
    # to load the config from environment variables with the prefix "FUNDUS_"
    model_config = SettingsConfigDict(
        env_prefix="FUNDUS_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    logging: LoggingConfig
    data: DataConfig
    app: AppConfig
    weaviate: WeaviateConfig
    google: GoogleConfig
    openai: OpenAIConfig
    fundus: FundusConfig
    assistant: AssistantConfig


@lru_cache(maxsize=1)
def load_config(config_file: str | Path | None = None) -> Config:
    if config_file is None:
        config_file = os.getenv("FUNDUS_CONFIG_FILE", None)
    if config_file is None:
        config_file = "config.dev.yaml"

    config_file = Path(config_file)

    if not config_file.exists():
        raise ValueError(f"Config file not found at {config_file}")

    try:
        with open(config_file, "r") as f:
            config_dict = yaml.safe_load(f)

        # Create config from dict
        cfg = Config.model_validate(config_dict)
        logger.info(f"Loaded config file from {config_file}")
    except Exception as e:
        logger.error(f"Cannot read config file! {e}")
        raise e

    google_application_credentials_file = Path(cfg.google.application_credentials_file)
    if not google_application_credentials_file.exists():
        raise ValueError(
            f"Google application credentials file not found at {google_application_credentials_file}"
        )
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(
        google_application_credentials_file
    )
    os.environ["OPENAI_API_KEY"] = cfg.openai.api_key

    # Log the configuration without sensitive information
    log_config = config_dict.copy()
    if "openai" in log_config and "api_key" in log_config["openai"]:
        log_config["openai"]["api_key"] = "***"
    logger.info(f"Configuration: {log_config}")

    return cfg
