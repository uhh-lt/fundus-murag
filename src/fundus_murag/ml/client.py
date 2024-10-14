import time
from typing import Literal, TYPE_CHECKING

import numpy as np
import requests

if TYPE_CHECKING:
    import torch

from fundus_murag.ml.dto import EmbeddingsInput, EmbeddingsOutput
from fundus_murag.singleton_meta import SingletonMeta


class FundusMLClient(metaclass=SingletonMeta):
    def __init__(self, fundus_ml_url: str | None = None):
        if fundus_ml_url is not None:
            self._fundus_ml_url = fundus_ml_url
        else:
            from fundus_murag.config.config import load_config

            config = load_config()
            self._fundus_ml_url = config.fundus_ml_url
        self._wait_for_ready()

    def _wait_for_ready(self, s: int = 30) -> None:
        while s > 0:
            if self._is_ready():
                return
            time.sleep(1)
            s -= 1
        raise TimeoutError("Fundus ML is not ready!")

    def _is_ready(self) -> bool:
        try:
            return requests.get(f"{self._fundus_ml_url}/health").status_code == 200
        except Exception:
            return False

    def compute_image_embedding(
        self,
        base64_image: str,
        return_tensor: Literal["pt", "np"] | None = "np",
    ) -> "EmbeddingsOutput | np.ndarray | torch.Tensor":
        """
        Get the embedding of an image.

        Args:
            base64_image (str): The base64 encoded image data.
            return_tensor (Literal["pt", "np"], optional): The type of tensor to return. Defaults to "np".

        Returns:
            `EmbeddingsOutput` | np.ndarray | torch.Tensor: The embeddings of the image
        """
        input = EmbeddingsInput(input_data=base64_image, input_type="image")
        return self._get_embeddings(input, return_tensor, squeeze=True)

    def compute_text_embedding(
        self,
        text: str,
        return_tensor: Literal["pt", "np"] | None = "np",
    ) -> "EmbeddingsOutput | np.ndarray | torch.Tensor":
        """
        Get the embedding of a text.

        Args:
            text (str): The text.
            return_tensor (Literal["pt", "np"], optional): The type of tensor to return. Defaults to "np".

        Returns:
            `EmbeddingsOutput` | np.ndarray | torch.Tensor: The embeddings of the text
        """
        input = EmbeddingsInput(input_data=text, input_type="text")
        return self._get_embeddings(input, return_tensor, squeeze=True)

    def _get_embeddings(
        self,
        input: EmbeddingsInput,
        return_tensor: Literal["pt", "np"] | None = "np",
        squeeze: bool = True,
    ) -> "EmbeddingsOutput | np.ndarray | torch.Tensor":
        response = requests.post(
            f"{self._fundus_ml_url}/embed", json=input.model_dump()
        )
        response.raise_for_status()
        response_json = response.json()
        emb = EmbeddingsOutput.model_validate(response_json)

        if return_tensor == "pt":
            import torch

            emb = torch.tensor(emb.embeddings)
            if squeeze:
                emb = emb.squeeze()
        elif return_tensor == "np":
            emb = np.array(emb.embeddings)
            if squeeze:
                emb = emb.squeeze()
        else:
            if (
                squeeze
                and len(emb.embeddings) == 1
                and isinstance(emb.embeddings[0], list)
            ):
                emb.embeddings = emb.embeddings[0]

        return emb
