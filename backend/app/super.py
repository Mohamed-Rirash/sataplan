import uuid
from fastapi import UploadFile, File, HTTPException, status, FastAPI
from app.config import (
    supabase,
)  # Import your Supabase client and bucket name
import magic

KB = 1024
MB = 1024 * KB

SUPPORTED_IMAGE_FORMATS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

app = FastAPI()

BUCKET = "cover-images"


async def supabase_upload_signed(
    content: bytes, filename: str, content_type: str
):
    """
    Uploads a file to Supabase Storage using a signed URL.
    """
    # Step 1: Create a signed upload URL
    signed_url_response = supabase.storage.from_(
        BUCKET
    ).create_signed_upload_url(
        path=filename,
    )
    if not signed_url_response or "token" not in signed_url_response:
        raise HTTPException(
            status_code=500, detail="Failed to generate signed URL"
        )

    token = signed_url_response["token"]

    # Step 2: Upload the file using the signed URL
    response = supabase.storage.from_(BUCKET).upload_to_signed_url(
        path=filename,
        token=token,
        file=content,
        options={
            "content-type": content_type,
            "cache-control": "3600",
            "upsert": "false",
        },
    )
    return response


@app.post("/upload-profile-image")
async def upload_profile_image(profile_image: UploadFile = File(...)):
    """
    Uploads a profile image to Supabase Storage using a signed URL.
    """
    if not profile_image:
        raise HTTPException(status_code=400, detail="No profile image provided")

    # Read the file content
    content = await profile_image.read()
    size = len(content)

    # Validate file size
    if size > 1 * MB:
        raise HTTPException(
            status_code=400, detail="Profile image is too large"
        )

    # Validate file format
    format = profile_image.content_type
    if format not in SUPPORTED_IMAGE_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported image format")

    # Validate file type using magic
    file_type = magic.from_buffer(content, mime=True)
    if file_type not in SUPPORTED_IMAGE_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported image format")

    # Generate a unique filename
    file_extension = SUPPORTED_IMAGE_FORMATS[format]
    filename = f"profile-images/{uuid.uuid4()}.{file_extension}"

    # Upload to Supabase Storage using a signed URL
    await supabase_upload_signed(
        content=content, filename=filename, content_type=format
    )

    return {
        "message": "Profile image uploaded successfully",
        "filename": filename,
    }
