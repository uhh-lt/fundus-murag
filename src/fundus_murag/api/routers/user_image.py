from fastapi import APIRouter, UploadFile

from fundus_murag.data.user_image_store import UserImageStore

router = APIRouter(prefix="/data/user_image", tags=["data/user_image"])


user_image_store = UserImageStore()


@router.post(
    "/store",
    summary="Store a user provided image",
    response_model=str,
)
def store_user_image(image: UploadFile):
    image_bytes = image.file.read()
    image_id = user_image_store.store_user_image(image_bytes=image_bytes, mime=image.content_type)
    return image_id


@router.get(
    "/{image_id}",
    summary="Load a user provided image",
    response_model=str,
)
def load_user_image(image_id: str):
    base64_image = user_image_store.load_user_image(image_id, base64=True)
    return base64_image
