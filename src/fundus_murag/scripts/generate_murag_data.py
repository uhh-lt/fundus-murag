import json
import uuid
from enum import Enum, unique
from functools import partial
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from fire import Fire
from pandas import json_normalize
from pydantic import BaseModel, Field
from tqdm.auto import tqdm

from fundus_murag.data.utils import read_image_bytes
from fundus_murag.ml.client import FundusMLClient
from fundus_murag.ml.dto import (
    EmbeddingsInput,
    EmbeddingsOutput,
)


@unique
class EmbeddingType(str, Enum):
    IMAGE = "image"
    TEXT = "text"

    def __str__(self):
        return self.value


@unique
class EmbeddingName(str, Enum):
    RECORD_IMAGE = "record_image"
    RECORD_TITLE = "record_title"
    COLLECTION_TITLE = "collection_title"
    COLLECTION_DESCRIPTION = "collection_description"

    def __str__(self):
        return self.value


class BaseEmbeddingDataFrameSchema(BaseModel):
    murag_id: list[str] = Field(default_factory=list)
    embedding_type: list[EmbeddingType] = Field(default_factory=list)
    embedding_name: list[EmbeddingName] = Field(default_factory=list)
    embedding_model: list[str] = Field(default_factory=list)
    embedding: list[list[float]] = Field(default_factory=list)


class RecordsEmbeddingDataFrameSchema(BaseEmbeddingDataFrameSchema):
    fundus_id: list[int] = Field(default_factory=list)


class CollectionsEmbeddingDataFrameSchema(BaseEmbeddingDataFrameSchema):
    collection_name: list[str] = Field(default_factory=list)


def _load_dataframes(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    collections_df = pd.read_parquet(root / "collections.pq")
    records_df = pd.read_parquet(root / "records.pq")

    print(f"Loaded {len(collections_df)} collections from {root / 'collections.pq'}")
    print(f"Loaded {len(records_df)} records from {root / 'records.pq'}")

    # drop collections that are not in records
    collections_df = collections_df[collections_df["collection_name"].isin(records_df["collection_name"])]
    print(f"Filtered {len(collections_df)} collections that are in records")

    return collections_df, records_df


def _generate_collection_title_embeddings(
    collections_df: pd.DataFrame,
    fundus_ml_url: str,
) -> pd.DataFrame:
    data = CollectionsEmbeddingDataFrameSchema()
    client = FundusMLClient(fundus_ml_url)

    for _, row in tqdm(
        collections_df.iterrows(),
        total=len(collections_df),
        desc="Collection Title Embeddings",
    ):
        data.collection_name.append(row["collection_name"])
        data.murag_id.append(row["murag_id"])
        data.embedding_type.append(EmbeddingType.TEXT)
        data.embedding_name.append(EmbeddingName.COLLECTION_TITLE)

        text_embedding_output: EmbeddingsOutput = client.compute_text_embedding(row["title"], None)  # type: ignore

        data.embedding_model.append(text_embedding_output.embedding_model)
        data.embedding.append(text_embedding_output.embeddings)  # type: ignore

    return pd.DataFrame(data.model_dump())


def _generate_collection_description_embeddings(
    collections_df: pd.DataFrame,
    fundus_ml_url: str,
) -> pd.DataFrame:
    data = CollectionsEmbeddingDataFrameSchema()
    client = FundusMLClient(fundus_ml_url)

    for _, row in tqdm(
        collections_df.iterrows(),
        total=len(collections_df),
        desc="Collection Description Embeddings",
    ):
        data.collection_name.append(row["collection_name"])

        data.murag_id.append(row["murag_id"])
        data.embedding_type.append(EmbeddingType.TEXT)
        data.embedding_name.append(EmbeddingName.COLLECTION_DESCRIPTION)

        text_embedding_output: EmbeddingsOutput = client.compute_text_embedding(row["description"], None)  # type: ignore

        data.embedding_model.append(text_embedding_output.embedding_model)
        data.embedding.append(text_embedding_output.embeddings)  # type: ignore

    return pd.DataFrame(data.model_dump())


def _generate_record_image_embeddings(
    records_df: pd.DataFrame,
    fundus_ml_url: str,
    batch_size: int,
    worker_id: int = 0,
) -> pd.DataFrame:
    data = RecordsEmbeddingDataFrameSchema()
    client = FundusMLClient(fundus_ml_url)

    batch = []
    for _, row in tqdm(
        records_df.iterrows(),
        total=len(records_df),
        desc="Record Image Embeddings",
        position=worker_id,
        leave=False,
    ):
        batch.append(row.to_dict())
        if len(batch) < batch_size:
            continue

        image_bytes = []
        for b in batch:
            try:
                image_path = Path(b["image_path"])
                image_bytes.append(read_image_bytes(image_path))
            except Exception as e:
                print(f"Could not read image from {b['image_path']}: {e}")

        image_inputs = EmbeddingsInput(input_data=image_bytes, input_type="image")
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


def _generate_record_title_embeddings(
    records_df: pd.DataFrame,
    fundus_ml_url: str,
    batch_size: int,
    worker_id: int = 0,
) -> pd.DataFrame:
    data = RecordsEmbeddingDataFrameSchema()
    client = FundusMLClient(fundus_ml_url)

    batch = []
    for _, row in tqdm(
        records_df.iterrows(),
        total=len(records_df),
        desc="Record Title Embeddings",
        position=worker_id,
        leave=False,
    ):
        batch.append(row.to_dict())
        if len(batch) < batch_size:
            continue

        titles = [b["title"] for b in batch]

        title_inputs = EmbeddingsInput(input_data=titles, input_type="text")
        title_embedding_outputs: EmbeddingsOutput = client._get_embeddings(
            title_inputs,
            None,
            False,
        )  # type: ignore

        for b, embedding in zip(batch, title_embedding_outputs.embeddings):
            data.fundus_id.append(b["fundus_id"])
            data.murag_id.append(b["murag_id"])
            data.embedding_type.append(EmbeddingType.TEXT)
            data.embedding_name.append(EmbeddingName.RECORD_TITLE)
            data.embedding_model.append(title_embedding_outputs.embedding_model)
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
        image_embeddings = _generate_record_image_embeddings(records_df, fundus_ml_url, batch_size)
        title_embeddings = _generate_record_title_embeddings(records_df, fundus_ml_url, batch_size)
        embeddings = pd.concat([image_embeddings, title_embeddings])
    else:
        splits = np.array_split(records_df, n_proc)
        with Pool(n_proc) as pool:
            image_embeddings = pool.starmap(
                _generate_record_image_embeddings,
                [(split, fundus_ml_url, batch_size, wid) for wid, split in enumerate(splits)],
            )
        image_embeddings = pd.concat(image_embeddings)

        with Pool(n_proc) as pool:
            title_embeddings = pool.starmap(
                _generate_record_title_embeddings,
                [(split, fundus_ml_url, batch_size, wid) for wid, split in enumerate(splits)],
            )
        title_embeddings = pd.concat(title_embeddings)

        embeddings = pd.concat([image_embeddings, title_embeddings])

    return embeddings


def _generate_collection_embeddings(
    collections_df: pd.DataFrame,
    fundus_ml_url: str,
) -> pd.DataFrame:
    title_embeddings = _generate_collection_title_embeddings(
        collections_df,
        fundus_ml_url,
    )
    embeddings = title_embeddings

    description_embeddings = _generate_collection_description_embeddings(collections_df, fundus_ml_url)
    embeddings = pd.concat([title_embeddings, description_embeddings])

    return embeddings


def _get_image_path(row, record_pix_dir: Path):
    if "image_path" in row and row["image_path"] is not None:
        return row["image_path"]
    matches = list(
        (record_pix_dir / row.collection_name).rglob(
            str((record_pix_dir / row.collection_name / row.image_name).stem.replace("+", " ").replace("%C2%A0", " "))
            + "*"
        )
    )
    if len(matches) == 0:
        return None
    return matches[0]


def _add_contacts(contacts_dir: Path, collections_df: pd.DataFrame) -> pd.DataFrame:
    contacts_df = pd.read_json(contacts_dir / "contacts.json")
    contacts_df = contacts_df.explode("content_objects").drop(columns=["created_at", "updated_at"])

    def get_contacts(collection_name: str) -> list[dict[str, str]]:
        contacts = contacts_df[contacts_df.content_objects == collection_name]
        cds = []
        for i, contact in contacts.iterrows():
            cd = contact.to_dict()
            del cd["id"]
            del cd["content_objects"]
            cds.append(cd)
        return cds

    cdf = collections_df.copy()
    cdf["contacts"] = cdf.collection_name.apply(lambda cn: get_contacts(cn))

    return cdf


def _add_collection_fields(fields_dir: Path, collections_df: pd.DataFrame) -> pd.DataFrame:
    cdf = collections_df.copy()
    # read field jsons
    fields_dfs = {}
    for p in fields_dir.glob("*.json"):
        try:
            with p.open() as f:
                fields_dfs[p.stem.replace("_fields", "")] = pd.read_json(f)
        except Exception as e:
            print(f"Error loading {p}: {e}")

    # first stage: build fields dataframe with base information
    data = {
        "collection_name": [],
        "field_name": [],
        "csv_headers": [],
        "labels": [],
        "title_fields": [],
    }
    for k, v in fields_dfs.items():
        if k in cdf.collection_name.unique():
            if "name" not in list(v.columns) or "csv_headers" not in list(v.columns):
                print(k, v.columns)
            else:
                data["collection_name"].append(k)
                data["field_name"].append(v["name"].values)

                data["csv_headers"].append(v["csv_headers"].values)
                if "labels" in list(v.columns):
                    data["labels"].append(v["labels"].values)
                else:
                    data["labels"].append(
                        [{"de": ld, "en": le} for ld, le in zip(list(v["label_de"]), list(v["label_en"]))]
                    )

                title_fields = {}
                for _, row in v.iterrows():
                    if k == "kuzmina_archive":
                        title_fields[1] = "descr_title"
                        continue

                    pos = None
                    if "title_field_position" in row and not pd.isna(row["title_field_position"]):
                        pos = int(row["title_field_position"])
                    elif "title_field_prio" in row and not pd.isna(row["title_field_prio"]):
                        pos = int(row["title_field_prio"])

                    if pos is not None and pos >= 0:
                        title_fields[pos] = row["name"]

                data["title_fields"].append(list(title_fields.values()))
    fields_df = pd.DataFrame(data)

    # second stage: transform fields dataframe to be in a more usable format
    data = {
        "collection_name": [],
        "title_fields": [],
        "fields": [],
    }
    for _, row in fields_df.iterrows():
        data["title_fields"].append(row["title_fields"])
        data["collection_name"].append(row["collection_name"])

        fns = row["field_name"]
        labels = row["labels"]
        fields = []
        for fn, label in zip(fns, labels):
            ld, le = label["de"], label["en"]
            if (ld is None or ld == "") and (le is None or le == ""):
                continue
            fields.append(
                {
                    "name": fn,
                    "label_de": ld,
                    "label_en": le,
                }
            )
        data["fields"].append(fields)

    fields_df = pd.DataFrame(data).reset_index(drop=True)

    # merge fields into collections df
    cdf = cdf.merge(fields_df, on="collection_name", how="left")
    cdf.title_fields = cdf.title_fields.apply(lambda tf: tf if isinstance(tf, list) else [])
    cdf.fields = cdf.fields.apply(lambda tf: tf if isinstance(tf, list) else [])

    return cdf


def _create_collections_df(
    content_objects_dir: Path,
    fields_dir: Path,
    contacts_dir: Path,
) -> pd.DataFrame:
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

    collections_df = pd.DataFrame(collection_data)
    collections_df["murag_id"] = collections_df.apply(lambda x: str(uuid.uuid4()), axis=1)
    murag_id = collections_df.pop("murag_id")
    collections_df.insert(0, "murag_id", murag_id)

    collections_df = _add_contacts(contacts_dir, collections_df)
    collections_df = _add_collection_fields(fields_dir, collections_df)

    return collections_df


def _resolve_image_paths(records_df: pd.DataFrame, record_pix_dir: Path, worker_id: int = 0) -> pd.DataFrame:
    tqdm.pandas(
        desc="Resolving image paths",
        total=len(records_df),
        position=worker_id,
        leave=False,
    )
    records_df["image_path"] = records_df.progress_apply(  # type: ignore
        partial(_get_image_path, record_pix_dir=record_pix_dir), axis=1
    )
    records_df.image_path = records_df.image_path.apply(lambda x: str(x) if x is not None else None)
    return records_df


def _get_record_title(row, collections_df: pd.DataFrame) -> str:
    collection_name = row["collection_name"]
    collection = collections_df[collections_df.collection_name == collection_name].iloc[0]
    title_fields = collection.title_fields
    details = {
        k.replace("details_", ""): v for k, v in row.items() if k.startswith("details_") and v is not None and v != ""
    }

    if "Title" in details:
        title = details["Title"]
    elif "title" in details:
        title = details["title"]
    else:
        title = ""
        for field in title_fields:
            if field in details:
                title += str(details[field]) + " "

        title = title.strip()

    return title


def _create_records_df(
    collection_records_dir: Path,
    record_pix_dir: Path,
    collections_df: pd.DataFrame,
    n_proc: int = 4,
) -> pd.DataFrame:
    # read all collection record files
    collection_records = {fn.stem: pd.read_json(fn) for fn in collection_records_dir.glob("*.json")}
    for name, df in collection_records.items():
        df["collection_name"] = name
    records_df = pd.concat(collection_records.values())
    records_df = records_df[records_df["pix"].apply(len).gt(0)]
    records_df = records_df[["id", "catalogno", "collection_name", "details", "pix"]]
    print(f"All collections with at least one image: {len(records_df.collection_name.unique())}")
    records_df["catalogno"] = records_df["catalogno"].astype(str)
    records_df = records_df.explode("pix").reset_index(drop=True)
    records_df = records_df.rename(columns={"id": "fundus_id", "pix": "image_name"})
    records_df["fundus_id"] = records_df["fundus_id"].astype(int)

    # Expand details
    records_df = pd.concat(
        [records_df, json_normalize(records_df["details"]).add_prefix("details_")],  # type: ignore
        axis=1,
    ).drop("details", axis=1)

    # Add title
    records_df["title"] = records_df.apply(lambda x: _get_record_title(x, collections_df), axis=1)
    title = records_df.pop("title")
    records_df.insert(0, "title", title)

    # Resolve image paths
    if n_proc == 1:
        _resolve_image_paths(records_df, record_pix_dir)
    else:
        splits = np.array_split(records_df, n_proc * 2)
        with Pool(n_proc * 2) as pool:
            records_df = pd.concat(
                pool.starmap(
                    _resolve_image_paths,
                    [(split, record_pix_dir, wid) for wid, split in enumerate(splits)],
                )
            ).reset_index(drop=True)
    found_frac = len(records_df.dropna(subset="image_path")) / len(records_df)
    records_df = records_df.dropna(subset=["image_path"]).dropna(subset=["image_name"])
    print(f"Found {found_frac:.4%} of images. Final number of records: {len(records_df)}")

    # relative image paths
    records_df["image_path"] = records_df["image_path"].apply(lambda x: x.replace(str(record_pix_dir.parent), ""))

    # Add murag_id as a unique identifier because fundus_id is not unique (e.g. for multiple images per record)
    records_df["murag_id"] = records_df.apply(lambda x: str(uuid.uuid4()), axis=1)
    murag_id = records_df.pop("murag_id")
    records_df.insert(0, "murag_id", murag_id)

    return records_df


def _generate_dataframes(
    fundus_data_root: Path,
    out_p: Path,
    n_proc: int = 4,
):
    record_data_dir = fundus_data_root / "record_data"
    record_pix_dir = fundus_data_root / "record_pix"
    content_objects_dir = fundus_data_root / "content_objects"
    collection_records_dir = fundus_data_root / "collection_records"
    fields_dir = fundus_data_root / "fields"
    contacts_dir = fundus_data_root / "contacts"
    assert fundus_data_root.exists(), f"{fundus_data_root} does not exist"
    assert record_data_dir.exists(), f"{record_data_dir} does not exist"
    assert record_pix_dir.exists(), f"{record_pix_dir} does not exist"
    assert content_objects_dir.exists(), f"{content_objects_dir} does not exist"
    assert collection_records_dir.exists(), f"{collection_records_dir} does not exist"
    assert fields_dir.exists(), f"{fields_dir} does not exist"
    assert contacts_dir.exists(), f"{contacts_dir} does not exist"

    collections_df = _create_collections_df(content_objects_dir, fields_dir, contacts_dir)
    collections_df.to_parquet(out_p / "collections.pq", index=False)
    print(f"Wrote {len(collections_df)} collections to {out_p / 'collections.pq'}")

    records_df = _create_records_df(
        collection_records_dir,
        record_pix_dir,
        collections_df,
        n_proc,
    )
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
        )
        collection_embeddings.to_parquet(out_p / "collection_embeddings.pq", index=False)
        print(f"Wrote {len(collection_embeddings)} collection embeddings to {out_p / 'collection_embeddings.pq'}")
    if gen_record_embeddings:
        record_embeddings = _generate_record_embeddings(
            records_df,
            fundus_ml_url,
            batch_size,
            n_proc,
        )
        record_embeddings.to_parquet(out_p / "record_embeddings.pq", index=False)
        print(f"Wrote {len(record_embeddings)} record embeddings to {out_p / 'record_embeddings.pq'}")


def main(
    out_p: str | Path = "/home/7schneid/gitrepos/fundus-murag/data",
    fundus_data_root: str | Path = "/home/7schneid/gitrepos/fundus-json",
    fundus_ml_url: str = "http://localhost:58003",
    batch_size: int = 128,
    gen_dataframes: bool = True,
    gen_record_embeddings: bool = True,
    gen_collection_embeddings: bool = True,
    n_proc: int = 8,
):
    fundus_data_root = Path(fundus_data_root)
    out_p = Path(out_p)
    if not out_p.exists():
        raise FileNotFoundError(f"{out_p} does not exist")
    if gen_collection_embeddings or gen_record_embeddings:
        FundusMLClient(fundus_ml_url)  # check if server is ready

    if gen_dataframes:
        _generate_dataframes(
            fundus_data_root,
            out_p,
            n_proc,
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
