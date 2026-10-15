import uuid
from io import BytesIO

import cloudinary
import cloudinary.uploader
from PIL import Image, ImageOps

from config import settings

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)

PROFILE_FOLDER = "profile_pics"


def process_profile_image(content: bytes) -> str:
    with Image.open(BytesIO(content)) as original:
        img = ImageOps.exif_transpose(original)
        img = ImageOps.fit(img, (300, 300), method=Image.Resampling.LANCZOS)

        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        buf = BytesIO()
        img.save(buf, "JPEG", quality=85, optimize=True)
        buf.seek(0)

    public_id = uuid.uuid4().hex
    cloudinary.uploader.upload(buf, public_id=public_id, folder=PROFILE_FOLDER)
    return f"{public_id}.jpg"


def delete_profile_image(filename: str | None) -> None:
    if filename is None:
        return
    public_id = f"{PROFILE_FOLDER}/{filename.removesuffix('.jpg')}"
    cloudinary.uploader.destroy(public_id)