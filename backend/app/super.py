import uuid
from fastapi import UploadFile, File, HTTPException, FastAPI
from app.config import supabase  # Import your Supabase client
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
    Uploads a file to Supabase Storage using a signed URL and returns the public URL.
    """
    # Step 1: Create a signed upload URL
    signed_url_response = supabase.storage.from_(
        BUCKET
    ).create_signed_upload_url(path=filename)

    if not signed_url_response or "token" not in signed_url_response:
        raise HTTPException(
            status_code=500, detail="Failed to generate signed URL"
        )

    token = signed_url_response["token"]

    # Step 2: Upload the file using the signed URL
    response = supabase.storage.from_(BUCKET).upload_to_signed_url(
        path=filename,
        token=token,
        file=content,  # Only required parameters
    )

    if not response:
        raise HTTPException(status_code=500, detail="Failed to upload file")

    # Step 3: Generate the public URL
    public_url = supabase.storage.from_(BUCKET).get_public_url(path=filename)

    return public_url


@app.post("/upload-cover-image")
async def upload_cover_image(cover_image: UploadFile = File(...)):
    """
    Uploads a cover image to Supabase Storage and returns the public URL.
    """
    if not cover_image:
        raise HTTPException(status_code=400, detail="No cover image provided")

    # Read the file content
    content = await cover_image.read()
    size = len(content)

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

    return {
        "message": "Cover image uploaded successfully",
        "filename": filename,
        "url": public_url,  # Returning the public URL
    }
