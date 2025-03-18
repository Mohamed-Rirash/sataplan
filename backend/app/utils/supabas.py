from app.config import supabase, BUCKET
from fastapi import HTTPException

BUCKET = "cover-images"
print(f"###########################{BUCKET}")


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
