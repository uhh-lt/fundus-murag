# import debugpy
# debugpy.listen(58688)

import base64
import io
import os

import litserve as ls
import torch

# we use relative imports here because this needs to run inside docker
from dto import (
    EmbeddingsInput,
    EmbeddingsOutput,
)
from loguru import logger
from PIL import Image
from transformers import BatchFeature, SiglipModel, SiglipProcessor

FUNDUS_ML_DEV_MODE = int(os.environ.get("FUNDUS_ML_DEV_MODE", 1))

MODEL_NAME = "google/siglip-so400m-patch14-384"
TORCH_DTYPE = torch.bfloat16


class SigLipLitAPI(ls.LitAPI):
    def setup(self, device: str):
        self.device: str = device
        logger.info(f"Using device: {device}")
        self.model = SiglipModel.from_pretrained(
            MODEL_NAME,
            attn_implementation="flash_attention_2",
            torch_dtype=TORCH_DTYPE,
            device_map=device,
        )
        self.processor = SiglipProcessor.from_pretrained(MODEL_NAME)

    def decode_request(self, request: EmbeddingsInput) -> dict[str, list | None]:
        if request.input_type == "text":
            text = request.input_data if isinstance(request.input_data, list) else [request.input_data]
            image = None
        elif request.input_type == "image":
            image_data = request.input_data if isinstance(request.input_data, list) else [request.input_data]
            image = [Image.open(io.BytesIO(base64.b64decode(b64))) for b64 in image_data]
            text = None
        else:
            raise ValueError("Invalid request type")

        return {"image": image, "text": text}

    def _compute_text_embedding(self, text_features: BatchFeature) -> torch.Tensor:
        with torch.no_grad():
            text_emb = self.model.get_text_features(**text_features.to(self.device))
        return text_emb

    def _compute_image_embedding(self, image_features: BatchFeature) -> torch.Tensor:
        with torch.no_grad():
            img_emb = self.model.get_image_features(**image_features.to(self.device, dtype=TORCH_DTYPE))
        return img_emb

    def predict(self, inputs: dict[str, list | None]) -> torch.Tensor:
        images = inputs["image"]
        texts = inputs["text"]

        if images is None and texts is None:
            raise ValueError("No input data provided")
        elif images is not None and texts is not None:
            raise ValueError("Cannot process both image and text data at the same time")
        elif images is not None and len(images) > 0:
            image_features = self.processor(
                images=images,
                padding="max_length",
                return_tensors="pt",
            )  # type: ignore
            embs = self._compute_image_embedding(image_features)
        elif texts is not None and len(texts) > 0:
            texts = self.processor(
                text=texts,
                padding="max_length",
                return_tensors="pt",
                truncation=True,
            )  # type: ignore
            embs = self._compute_text_embedding(texts)
        else:
            raise ValueError("Invalid input data")

        return embs

    def encode_response(self, outputs: torch.Tensor) -> EmbeddingsOutput:
        return EmbeddingsOutput(
            embeddings=outputs.tolist(),
            embedding_model=MODEL_NAME,
        )


if __name__ == "__main__":
    if FUNDUS_ML_DEV_MODE == 0:
        workers_per_device = 2
    else:
        workers_per_device = 1

    port = 8000
    logger.info(f"Starting server on port {port}")
    logger.info(f"Workers per device: {workers_per_device}")

    api = SigLipLitAPI()
    server = ls.LitServer(
        api,
        accelerator="cuda",
        api_path="/embed",
        workers_per_device=workers_per_device,
    )
    server.run(port=port)
