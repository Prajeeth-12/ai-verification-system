from supabase import create_client, Client
from app.config import settings

def get_supabase() -> Client:
    """Initialize and return a Supabase client."""
    url = settings.SUPABASE_URL
    # Prioritize service role key for backend operations
    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and a valid key (SERVICE_ROLE or SUPABASE_KEY) must be set in environment")
    
    client = create_client(url, key)
    
    # Ensure buckets exist
    try:
        buckets = ["documents", "reports"]
        existing = client.storage.list_buckets()
        existing_names = [b.name for b in existing]
        
        for b in buckets:
            if b not in existing_names:
                print(f"Creating bucket: {b}")
                client.storage.create_bucket(b, options={"public": True})
    except Exception as e:
        print(f"Warning: Could not initialize buckets: {e}")
        
    return client

supabase: Client = get_supabase()
