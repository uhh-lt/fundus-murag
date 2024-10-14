from pydantic import BaseModel, Field
from typing import Annotated, Literal
from annotated_types import Len

MAX_BATCH_SIZE: int = 128


class EmbeddingsInput(BaseModel):
    input_data: Annotated[list[str], Len(max_length=MAX_BATCH_SIZE)] | str = Field(
        ..., title="Either the text or base64 encoded image data"
    )
    input_type: Literal["text", "image"] = Field(..., title="Type of input data")


class EmbeddingsOutput(BaseModel):
    embeddings: list[list[float]] | list[float] = Field(..., title="Embeddings")
    embedding_model: str = Field(..., title="Embedding model")
