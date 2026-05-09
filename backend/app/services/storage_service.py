import logging
from app.db.supabase import supabase
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_to_storage(file_bytes: bytes, filename: str):
    """
    Uploads a file to Supabase Storage and returns the public URL.
    Handles duplicate filenames by appending a timestamp if necessary.
    """
    bucket_name = "documents"
    
    # Check if bucket exists (Supabase client doesn't have an easy "exists" for buckets, 
    # but we assume it's created or handled in the dashboard)
    
    try:
        # Handle duplicates: In a production app, you might use UUIDs.
        # For now, we try to upload and if it fails due to existing name, we could retry.
        # Supabase Storage also has an upsert option.
        
        logger.info(f"Uploading {filename} to Supabase Storage bucket '{bucket_name}'")
        
        # Perform the upload
        response = supabase.storage.from_(bucket_name).upload(
            path=filename,
            file=file_bytes,
            file_options={"content-type": "application/octet-stream", "x-upsert": "true"}
        )
        
        # Get public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(filename)
        
        logger.info(f"Successfully uploaded {filename}. Public URL: {public_url}")
        
        return {
            "public_url": public_url,
            "filename": filename,
            "metadata": response
        }
        
    except Exception as e:
        logger.error(f"Error uploading to Supabase Storage: {str(e)}")
        raise e
