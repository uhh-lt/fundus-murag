import io
from pathlib import Path
from uuid import uuid4

from loguru import logger
from PIL import Image

from fundus_murag.config import load_config
from fundus_murag.data.utils import encode_image
from fundus_murag.singleton_meta import SingletonMeta


class UserImageStore(metaclass=SingletonMeta):
    def __init__(self):
        config = load_config()
        self._images_root = Path(config.data.user_image_dir)
        self._images_root.mkdir(parents=True, exist_ok=True)
        self._supported_image_formats = ["jpg", "jpeg", "png"]
        self._user_images: dict[str, Path] = {}

    def _read_user_images(self):
        for ext in self._supported_image_formats:
            for image_path in self._images_root.glob(f"*.{ext}"):
                self._user_images[image_path.stem] = image_path
        logger.info(f"Read {len(self._user_images)} user images from {self._images_root} ...")

    def load_user_image(self, image_id: str, base64: bool = False) -> Image.Image | str:
        if image_id not in self._user_images:
            raise FileNotFoundError(f"Cannot find user image with ID {image_id}!")
        image_path = self._user_images[image_id]
        image = Image.open(image_path)
        if base64:
            base64_data = encode_image(image)
            image = f"data:image/jpeg;base64,{base64_data}"

        return image

    def store_user_image(self, image_bytes: bytes, mime: str | None) -> str:
        uuid = str(uuid4())
        if mime not in ["image/jpeg", "image/jpg", "image/png"]:
            raise ValueError("Invalid image format! Supported formats are: jpg, jpeg, png")
        ext = mime.split("/")[-1]
        ofn = self._images_root / f"{uuid}.{ext}"
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image.save(ofn)
            self._user_images[uuid] = ofn
            logger.info(f"Stored user provided image at {ofn}")
            return uuid
        except Exception as e:
            logger.error(f"Failed to store user provided image: {e}")
            raise e
