import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from loguru import logger
from omegaconf import OmegaConf


@dataclass
class Config:
    logging_dir: str
    logging_level: str

    fundus_records_df_file: str
    fundus_collections_df_file: str
    fundus_record_embeddings_df_file: str
    fundus_collections_embeddings_df_file: str

    dev_mode: bool
    reset_vdb_on_startup: bool

    weaviate_host: str
    weaviate_http_port: int
    weaviate_grpc_port: int

    google_application_credentials_file: str
    google_project_id: str
    google_default_location: str

    open_ai_api_key: str

    fundus_ml_url: str

    assistant_default_model: str


@lru_cache(maxsize=1)
def load_config(config_file: str | Path | None = None) -> Config:
    config = dict()
    if config_file is None:
        config_file = os.getenv("FUNDUS_CONFIG_FILE", None)
    if config_file is None:
        config_file = "config.dev.yaml"

    config_file = Path(config_file)

    if config_file is not None and config_file.exists():
        try:
            config = OmegaConf.load(config_file)
            logger.info(f"Loaded config file from {config_file}")
            config_dict = OmegaConf.to_container(config, resolve=True)
            cfg = Config(**config_dict)
        except Exception as e:
            logger.error(f"Cannot read config file! {e}")
            raise e
    else:
        raise ValueError(f"Config file not found at {config_file}")

    google_application_credentials_file = Path(cfg.google_application_credentials_file)
    if not google_application_credentials_file.exists():
        raise ValueError(
            f"Google application credentials file not found at {google_application_credentials_file}"
        )
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(
        google_application_credentials_file
    )
    os.environ["OPENAI_API_KEY"] = cfg.open_ai_api_key

    logger.info("\n" + OmegaConf.to_yaml(config))

    return cfg
