import os
import logging
from supabase import create_client, Client
from typing import Set

# Initialize Supabase client
# Ensure SUPABASE_URL and SUPABASE_KEY are in your .env or environment variables
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client = None
if url and key:
    try:
        supabase = create_client(url, key)
    except Exception as e:
        logging.error(f"Failed to initialize Supabase client: {e}")

def get_processed_ids() -> Set[str]:
    """Fetch all processed email IDs from Supabase."""
    if not supabase:
        logging.warning("Supabase client not initialized. Returning empty set.")
        return set()
    
    try:
        # Fetch all rows. Supabase limits default fetch (usually 1000), 
        # but for now simple select is fine. Pagination might be needed later.
        response = supabase.table("processed_emails").select("email_id").execute()
        return {item['email_id'] for item in response.data}
    except Exception as e:
        logging.error(f"Error fetching processed IDs from Supabase: {e}")
        return set()

def add_processed_id(email_id: str):
    """Add a processed email ID to Supabase."""
    if not supabase:
        return

    try:
        supabase.table("processed_emails").insert({"email_id": email_id}).execute()
    except Exception as e:
        # Duplicate key errors happen if the ID is already there. 
        # We can log as debug or ignore.
        logging.warning(f"Error adding ID {email_id} to Supabase: {e}")
