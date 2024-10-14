import base64
import io
import json
import uuid
from enum import Enum, unique
from functools import partial
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from fire import Fire
from fundus_murag.ml.dto import (
    EmbeddingsOutput,
    ImageInput,
    TextInput,
)
from fundus_murag.ml.client import FundusMLClient
from pandas import json_normalize
from PIL import Image
from pydantic import BaseModel, Field
from tqdm.auto import tqdm


@unique
class EmbeddingType(str, Enum):
    IMAGE = "image"
    TEXT = "text"

    def __str__(self):
        return self.value


@unique
class EmbeddingName(str, Enum):
    RECORD_IMAGE = "record_image"
    COLLECTION_TITLE = "collection_title"
    COLLECTION_DESCRIPTION = "collection_description"

    def __str__(self):
        return self.value


class EmbeddingDataFrameSchema(BaseModel):
    fundus_id: list[int | str] = Field(default_factory=list)
    murag_id: list[str] = Field(default_factory=list)
    embedding_type: list[EmbeddingType] = Field(default_factory=list)
    embedding_name: list[EmbeddingName] = Field(default_factory=list)
    embedding_model: list[str] = Field(default_factory=list)
    embedding: list[list[float]] = Field(default_factory=list)


def _load_dataframes(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    collections_df = pd.read_parquet(root / "collections.pq")
    records_df = pd.read_parquet(root / "records.pq")

    print(f"Loaded {len(collections_df)} collections from {root / 'collections.pq'}")
    print(f"Loaded {len(records_df)} records from {root / 'records.pq'}")

    # drop collections that are not in records
    collections_df = collections_df[
        collections_df["collection_name"].isin(records_df["collection_name"])
    ]
    print(f"Filtered {len(collections_df)} collections that are in records")

    return collections_df, records_df


def _read_image_bytes(image_path: Path) -> str:
    try:
        image = Image.open(image_path).convert("RGB")
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Could not read image from {image_path}") from e


def _generate_collection_title_embeddings(
    collections_df: pd.DataFrame,
    fundus_ml_url: str,
    batch_size: int,
) -> pd.DataFrame:
    data = EmbeddingDataFrameSchema()
    client = FundusMLClient(fundus_ml_url)

    for _, row in tqdm(
        collections_df.iterrows(),
        total=len(collections_df),
        desc="Collection Title Embeddings",
    ):
        data.fundus_id.append(row["fundus_id"])
        data.murag_id.append(row["murag_id"])
        data.embedding_type.append(EmbeddingType.TEXT)
        data.embedding_name.append(EmbeddingName.COLLECTION_TITLE)

        text_embedding_output: EmbeddingsOutput = client.compute_text_embedding(
            row["title"], None
        )  # type: ignore

        data.embedding_model.append(text_embedding_output.embedding_model)
        data.embedding.append(text_embedding_output.embeddings)  # type: ignore

    return pd.DataFrame(data.model_dump())


def _generate_collection_description_embeddings(
    collections_df: pd.DataFrame,
    fundus_ml_url: str,
    batch_size: int,
) -> pd.DataFrame:
    data = EmbeddingDataFrameSchema()
    client = FundusMLClient(fundus_ml_url)

    for _, row in tqdm(
        collections_df.iterrows(),
        total=len(collections_df),
        desc="Collection Description Embeddings",
    ):
        data.fundus_id.append(row["fundus_id"])
        data.murag_id.append(row["murag_id"])
        data.embedding_type.append(EmbeddingType.TEXT)
        data.embedding_name.append(EmbeddingName.COLLECTION_DESCRIPTION)

        text_embedding_output: EmbeddingsOutput = client.compute_text_embedding(
            row["description"], None
        )  # type: ignore

        data.embedding_model.append(text_embedding_output.embedding_model)
        data.embedding.append(text_embedding_output.embeddings)  # type: ignore

    return pd.DataFrame(data.model_dump())


def _generate_record_image_embeddings(
    records_df: pd.DataFrame,
    fundus_ml_url: str,
    batch_size: int,
    worker_id: int = 0,
) -> pd.DataFrame:
    data = EmbeddingDataFrameSchema()
    client = FundusMLClient(fundus_ml_url)

    batch = []
    for _, row in tqdm(
        records_df.iterrows(),
        total=len(records_df),
        desc="Record Image Embeddings",
        position=worker_id,
    ):
        batch.append(row.to_dict())
        if len(batch) < batch_size:
            continue

        image_bytes = []
        for b in batch:
            try:
                image_path = Path(b["image_path"])
                image_bytes.append(_read_image_bytes(image_path))
            except Exception as e:
                print(f"Could not read image from {b['image_path']}: {e}")

        image_inputs = ImageInput(image_bytes=image_bytes)
        image_embedding_outputs: EmbeddingsOutput = client._get_embeddings(
            image_inputs,
            None,
            False,
        )  # type: ignore

        for b, embedding in zip(batch, image_embedding_outputs.embeddings):
            data.fundus_id.append(b["fundus_id"])
            data.murag_id.append(b["murag_id"])
            data.embedding_type.append(EmbeddingType.IMAGE)
            data.embedding_name.append(EmbeddingName.RECORD_IMAGE)
            data.embedding_model.append(image_embedding_outputs.embedding_model)
            data.embedding.append(embedding)  # type: ignore

        batch = []

    return pd.DataFrame(data.model_dump())


def _generate_record_embeddings(
    records_df: pd.DataFrame,
    fundus_ml_url: str,
    batch_size: int,
    n_proc: int = 4,
) -> pd.DataFrame:
    if n_proc == 1:
        image_embeddings = _generate_record_image_embeddings(
            records_df, fundus_ml_url, batch_size
        )
    else:
        splits = np.array_split(records_df, n_proc)
        with Pool(n_proc) as pool:
            image_embeddings = pool.starmap(
                _generate_record_image_embeddings,
                [
                    (split, fundus_ml_url, batch_size, wid)
                    for wid, split in enumerate(splits)
                ],
            )
        image_embeddings = pd.concat(image_embeddings)

    return image_embeddings


def _generate_collection_embeddings(
    collections_df: pd.DataFrame,
    fundus_ml_url: str,
    batch_size: int,
) -> pd.DataFrame:
    title_embeddings = _generate_collection_title_embeddings(
        collections_df, fundus_ml_url, batch_size
    )
    embeddings = title_embeddings
    # description_embeddings = _generate_collection_description_embeddings(
    #     collections_df, fundus_ml_url
    # )
    # embeddings = pd.concat([title_embeddings, description_embeddings])

    embeddings = embeddings.rename(
        columns={
            "fundus_id": "collection_name",
        }
    ).reset_index(drop=True)

    return embeddings


def _get_image_path(row, record_pix_dir: Path):
    if "image_path" in row and row["image_path"] is not None:
        return row["image_path"]
    matches = list(
        (record_pix_dir / row.collection_name).rglob(
            str(
                (record_pix_dir / row.collection_name / row.image_name)
                .stem.replace("+", " ")
                .replace("%C2%A0", " ")
            )
            + "*"
        )
    )
    if len(matches) == 0:
        return None
    return matches[0]


def _create_collections_df(content_objects_dir: Path) -> pd.DataFrame:
    collection_data = {
        "collection_name": [],
        "title": [],
        "title_de": [],
        "description": [],
        "description_de": [],
    }
    for data_fn in content_objects_dir.glob("*.json"):
        collection = data_fn.stem
        with open(data_fn) as f:
            data = json.load(f)
        collection_data["collection_name"].append(collection)
        collection_data["title"].append(data["title_en"])
        collection_data["title_de"].append(data["title"])
        collection_data["description"].append(data["description_en"])
        collection_data["description_de"].append(data["description"])

    df = pd.DataFrame(collection_data)
    df["murag_id"] = df.apply(lambda x: str(uuid.uuid4()), axis=1)
    murag_id = df.pop("murag_id")
    df.insert(0, "murag_id", murag_id)
    return df


def _resolve_image_paths(
    records_df: pd.DataFrame, record_pix_dir: Path, worker_id: int = 0
) -> pd.DataFrame:
    tqdm.pandas(desc="Resolving image paths", total=len(records_df), position=worker_id)
    records_df["image_path"] = records_df.progress_apply(  # type: ignore
        partial(_get_image_path, record_pix_dir=record_pix_dir), axis=1
    )
    records_df.image_path = records_df.image_path.apply(
        lambda x: str(x) if x is not None else None
    )
    return records_df


def _create_records_df(
    collection_records_dir: Path,
    record_pix_dir: Path,
    n_proc: int = 4,
) -> pd.DataFrame:
    # read all collection record files
    collection_records = {
        fn.stem: pd.read_json(fn) for fn in collection_records_dir.glob("*.json")
    }
    for name, df in collection_records.items():
        df["collection_name"] = name
    records_df = pd.concat(collection_records.values())
    records_df = records_df[records_df["pix"].apply(len).gt(0)]
    records_df = records_df[["id", "catalogno", "collection_name", "details", "pix"]]
    print(
        f"All collections with at least one image: {len(records_df.collection_name.unique())}"
    )
    records_df["catalogno"] = records_df["catalogno"].astype(str)
    records_df = records_df.explode("pix").reset_index(drop=True)
    records_df = records_df.rename(columns={"id": "fundus_id", "pix": "image_name"})

    # Resolve image paths
    if n_proc == 1:
        _resolve_image_paths(records_df, record_pix_dir)
    else:
        splits = np.array_split(records_df, n_proc)
        with Pool(n_proc) as pool:
            records_df = pd.concat(
                pool.starmap(
                    _resolve_image_paths,
                    [(split, record_pix_dir, wid) for wid, split in enumerate(splits)],
                )
            ).reset_index(drop=True)
    found_frac = len(records_df.dropna(subset="image_path")) / len(records_df)
    records_df = records_df.dropna(subset=["image_path"])
    print(
        f"Found {found_frac:.4%} of images. Final number of records: {len(records_df)}"
    )

    # Expand details
    records_df = pd.concat(
        [records_df, json_normalize(records_df["details"]).add_prefix("details_")],  # type: ignore
        axis=1,
    ).drop("details", axis=1)

    # Add murag_id as a unique identifier because fundus_id is not unique (e.g. for multiple images per record)
    records_df["murag_id"] = records_df.apply(lambda x: str(uuid.uuid4()), axis=1)
    murag_id = records_df.pop("murag_id")
    records_df.insert(0, "murag_id", murag_id)

    return records_df


def _generate_dataframes(
    fundus_data_root: Path,
    out_p: Path,
    gen_collection_dataframes: bool,
    gen_record_dataframes: bool,
):
    record_data_dir = fundus_data_root / "record_data"
    record_pix_dir = fundus_data_root / "record_pix"
    content_objects_dir = fundus_data_root / "content_objects"
    collection_records_dir = fundus_data_root / "collection_records"
    assert fundus_data_root.exists(), f"{fundus_data_root} does not exist"
    assert record_data_dir.exists(), f"{record_data_dir} does not exist"
    assert record_pix_dir.exists(), f"{record_pix_dir} does not exist"
    assert content_objects_dir.exists(), f"{content_objects_dir} does not exist"
    assert collection_records_dir.exists(), f"{collection_records_dir} does not exist"

    if gen_collection_dataframes:
        collections_df = _create_collections_df(content_objects_dir)
        collections_df.to_parquet(out_p / "collections.pq", index=False)
        print(f"Wrote {len(collections_df)} collections to {out_p / 'collections.pq'}")

    if gen_record_dataframes:
        records_df = _create_records_df(collection_records_dir, record_pix_dir)
        records_df.to_parquet(out_p / "records.pq", index=False)
        print(f"Wrote {len(records_df)} records to {out_p / 'records.pq'}")


def _generate_embeddings(
    out_p: Path,
    fundus_ml_url: str,
    batch_size: int,
    gen_collection_embeddings: bool,
    gen_record_embeddings: bool,
    n_proc: int,
):
    collections_df, records_df = _load_dataframes(out_p)
    if gen_collection_embeddings:
        collection_embeddings = _generate_collection_embeddings(
            collections_df,
            fundus_ml_url,
            batch_size,
        )
        collection_embeddings.to_parquet(
            out_p / "collection_embeddings.pq", index=False
        )
        print(
            f"Wrote {len(collection_embeddings)} collection embeddings to {out_p / 'collection_embeddings.pq'}"
        )
    if gen_record_embeddings:
        record_embeddings = _generate_record_embeddings(
            records_df,
            fundus_ml_url,
            batch_size,
            n_proc,
        )
        record_embeddings.to_parquet(out_p / "record_embeddings.pq", index=False)
        print(
            f"Wrote {len(record_embeddings)} record embeddings to {out_p / 'record_embeddings.pq'}"
        )


def main(
    out_p: str | Path = "/ltstorage/home/7schneid/gitrepos/fundus-murag/data",
    fundus_data_root: str | Path = "/ltstorage/home/7schneid/gitrepos/fundus-json",
    fundus_ml_url: str = "http://localhost:58007",
    batch_size: int = 128,
    gen_record_dataframes: bool = True,
    gen_collection_dataframes: bool = True,
    gen_record_embeddings: bool = True,
    gen_collection_embeddings: bool = True,
    n_proc: int = 4,
):
    fundus_data_root = Path(fundus_data_root)
    out_p = Path(out_p)
    if not out_p.exists():
        raise FileNotFoundError(f"{out_p} does not exist")

    if gen_collection_dataframes or gen_record_dataframes:
        _generate_dataframes(
            fundus_data_root, out_p, gen_collection_dataframes, gen_record_dataframes
        )

    if gen_collection_embeddings or gen_record_embeddings:
        _generate_embeddings(
            out_p,
            fundus_ml_url,
            batch_size,
            gen_collection_embeddings,
            gen_record_embeddings,
            n_proc,
        )


if __name__ == "__main__":
    Fire(main)
