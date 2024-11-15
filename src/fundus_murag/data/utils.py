import base64
import io
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger
from PIL import Image


def unicode_escape_str(s: str) -> str:
    # see https://stackoverflow.com/a/52461149
    return (
        s.encode("latin-1").decode("unicode_escape").encode("latin-1").decode("utf-8")
    )


def read_image_bytes(image_path: Path) -> str:
    try:
        image = Image.open(image_path).convert("RGB")
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        raise FileNotFoundError(f"Could not read image from {image_path}") from e


def array_to_list(x):
    if isinstance(x, np.ndarray):
        return x.tolist()
    return x


def replace_none_with_empty_string_in_dict(d):
    return {k: ("" if v is None else v) for k, v in d.items()}


def replace_none_in_list_of_dicts(lst):
    return [replace_none_with_empty_string_in_dict(d) for d in lst]


def load_fundus_records_df(
    fundus_records_df_file: str | Path, dev_mode: bool = True
) -> pd.DataFrame:
    fundus_records_df_file = Path(fundus_records_df_file)
    if not fundus_records_df_file.exists():
        raise FileNotFoundError(
            f"Cannot find FUNDus Records at {fundus_records_df_file.absolute()}"
        )
    logger.info(f"Loading FUNDus Records from {fundus_records_df_file} ...")
    records_df = pd.read_parquet(str(fundus_records_df_file))
    logger.info(
        f"Loaded FUNDus Records with {len(records_df)} records from {fundus_records_df_file}!"
    )

    if dev_mode:
        logger.info("Using DataFrame in dev mode!")
        records_df = (
            records_df.groupby("collection_name")
            .sample(n=20, random_state=42, replace=True)
            .reset_index(drop=True)
            .drop_duplicates()
        )
        logger.info(f"Using a sample of {len(records_df)} records!")

    records_df["fundus_id"] = records_df["fundus_id"].astype(int)
    records_df = records_df.map(array_to_list)

    return records_df


def load_fundus_record_embeddings_df(
    records_df: pd.DataFrame,
    fundus_record_embeddings_df_file: str | Path,
    dev_mode: bool = True,
) -> pd.DataFrame:
    fundus_record_embeddings_df_file = Path(fundus_record_embeddings_df_file)
    if not fundus_record_embeddings_df_file.exists():
        raise FileNotFoundError(
            f"Cannot find FUNDus Record Embeddings at {fundus_record_embeddings_df_file.absolute()}"
        )
    logger.info(
        f"Loading FUNDus Record Embeddings from {fundus_record_embeddings_df_file} ..."
    )
    record_embeddings_df = pd.read_parquet(str(fundus_record_embeddings_df_file))
    logger.info(
        f"Loaded FUNDus Record Embeddings with {len(record_embeddings_df)} records from {fundus_record_embeddings_df_file}!"
    )

    if dev_mode:
        if records_df is None:
            raise ValueError(
                "Cannot load record embeddings in dev mode without loading the records DataFrame first!"
            )
        logger.info("Using DataFrame in dev mode!")
        record_embeddings_df = record_embeddings_df[
            record_embeddings_df["fundus_id"].isin(records_df["fundus_id"])
        ]
        logger.info(f"Using a sample of {len(record_embeddings_df)} record embeddings!")

    record_embeddings_df["fundus_id"] = record_embeddings_df["fundus_id"].astype(int)

    return record_embeddings_df


def load_fundus_collections_df(
    records_df: pd.DataFrame,
    fundus_collections_df_file: str | Path,
    drop_empty: bool = True,
) -> pd.DataFrame:
    fundus_collections_df_file = Path(fundus_collections_df_file)
    if not fundus_collections_df_file.exists():
        raise FileNotFoundError(
            f"Cannot find FUNDus Collections DataFrame at {fundus_collections_df_file.absolute()}"
        )
    logger.info(f"Loading FUNDus Collections from {fundus_collections_df_file} ...")
    collections_df = pd.read_parquet(fundus_collections_df_file)
    logger.info(
        f"Loaded FUNDus Collections with {len(collections_df)} records from {fundus_collections_df_file}!"
    )

    # drop collections that are not in records, i.e., have no associated records and are empty
    if drop_empty:
        collections_df = collections_df[
            collections_df["collection_name"].isin(records_df["collection_name"])
        ]
        print(f"Filtered {len(collections_df)} collections that are in records")

    collections_df = collections_df.map(array_to_list)

    collections_df["contacts"] = collections_df["contacts"].apply(
        replace_none_in_list_of_dicts
    )
    collections_df["fields"] = collections_df["fields"].apply(
        replace_none_in_list_of_dicts
    )

    return collections_df


def load_fundus_collection_embeddings_df(
    fundus_collections_embeddings_df_file: str | Path,
) -> pd.DataFrame:
    fundus_collections_embeddings_df_file = Path(fundus_collections_embeddings_df_file)
    if not fundus_collections_embeddings_df_file.exists():
        raise FileNotFoundError(
            f"Cannot find FUNDus Collection Embeddings DataFrame at {fundus_collections_embeddings_df_file.absolute()}"
        )
    logger.info(
        f"Loading FUNDus Collection Embeddings from {fundus_collections_embeddings_df_file} ..."
    )
    collection_embeddings_df = pd.read_parquet(fundus_collections_embeddings_df_file)
    logger.info(
        f"Loaded FUNDus Collection Embeddings with {len(collection_embeddings_df)} records from {fundus_collections_embeddings_df_file}!"
    )

    return collection_embeddings_df
