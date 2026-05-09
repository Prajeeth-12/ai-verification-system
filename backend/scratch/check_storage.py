import sys
import os
import logging
from dotenv import load_dotenv

# Add the project root to sys.path so we can import from 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.supabase import supabase

# Load env vars
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    bucket_name = "documents"
    filename = "obc Certificate prajeeth_compressed.pdf"
    
    logger.info(f"Listing files in bucket: {bucket_name}")
    
    try:
        # List files in the bucket
        response = supabase.storage.from_(bucket_name).list()
        
        logger.info(f"Files in bucket: {[f['name'] for f in response]}")
        
        # Check if the specific file exists
        found = any(f['name'] == filename for f in response)
        if found:
            logger.info(f"File '{filename}' FOUND in storage.")
            
            # Get public URL
            public_url = supabase.storage.from_(bucket_name).get_public_url(filename)
            logger.info(f"Public URL: {public_url}")
        else:
            logger.error(f"File '{filename}' NOT FOUND in storage.")
            
    except Exception as e:
        logger.error(f"Error checking storage: {str(e)}")

if __name__ == "__main__":
    main()
