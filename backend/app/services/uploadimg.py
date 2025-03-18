import uuid
import magic
from fastapi import HTTPException

from app.super import supabase_upload_signed


KB = 1024
MB = 1024 * KB
MAX_FILE_SIZE = 1 * MB  # 1MB limit
SUPPORTED_IMAGE_FORMATS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


async def Uploader(cover_image):
    # Read the file content
    content = await cover_image.read()
    size = len(content)

    # image_url = upload_cover_image(cover_image)
    if not cover_image:
        raise HTTPException(status_code=400, detail="No cover image provided")

    # Validate file size (Max 5MB)
    if size > 5 * MB:
        raise HTTPException(status_code=400, detail="Cover image is too large")

        # Validate file format
    format = cover_image.content_type
    if format not in SUPPORTED_IMAGE_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported image format")

    # Validate file type using magic
    file_type = magic.from_buffer(content, mime=True)
    if file_type not in SUPPORTED_IMAGE_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported image format")

    # Generate a unique filename
    file_extension = SUPPORTED_IMAGE_FORMATS[format]
    filename = f"{uuid.uuid4()}.{file_extension}"

    # Upload to Supabase Storage and get the URL
    public_url = await supabase_upload_signed(
        content=content, filename=filename, content_type=format
    )
    return public_url
