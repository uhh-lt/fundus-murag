import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml


@dataclass
class Config:
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

    fundus_ml_url: str


@lru_cache(maxsize=1)
def load_config(config_file: str | Path | None = None) -> Config:
    config = dict()
    if config_file is None:
        config_file = os.getenv("FUNDUS_CONFIG_FILE", None)
    if config_file is None:
        config_file = "config.yaml"

    config_file = Path(__file__).resolve().parent / config_file

    if config_file is not None and config_file.exists():
        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)
            print(f"Loaded config file from {config_file}")
        except Exception as e:
            print(f"Cannot read config file! {e}")
        cfg = Config(**config)

    else:
        raise ValueError(f"Config file not found at {config_file}")

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
        cfg.google_application_credentials_file
    )

    print(yaml.dump(config, indent=2))

    return cfg
