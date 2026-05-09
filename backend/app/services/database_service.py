import logging
from app.db.supabase import supabase

# Configure logging
logger = logging.getLogger(__name__)

def save_uploaded_document(doc_data: dict):
    """
    Persists document metadata into the 'uploaded_documents' table.
    """
    try:
        logger.info(f"Inserting metadata for document: {doc_data.get('filename')}")
        
        response = supabase.table("uploaded_documents").insert(doc_data).execute()
        
        logger.info(f"Successfully saved document metadata to database.")
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error saving to database: {str(e)}")
        raise e

def save_verification_result(doc_id: str, result: dict):
    """
    Updates the document record with verification results.
    """
    try:
        logger.info(f"Updating verification results for document ID: {doc_id}")
        
        update_data = {
            "verification_status": result.get("status", "pending"),
            "confidence_score": result.get("confidence", 0.0),
            "extracted_data": result.get("data", {})
        }
        
        response = supabase.table("uploaded_documents").update(update_data).eq("id", doc_id).execute()
        
        logger.info(f"Successfully updated verification results.")
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error updating verification results: {str(e)}")
        raise e
def get_document_by_filename(filename: str):
    """
    Retrieves document metadata by filename.
    """
    try:
        logger.info(f"Fetching metadata for filename: {filename}")
        response = supabase.table("uploaded_documents").select("*").eq("filename", filename).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error fetching document: {str(e)}")
        raise e

def save_report_metadata(report_data: dict):
    """
    Persists final report metadata into the 'verification_results' table.
    """
    try:
        logger.info(f"Saving final report metadata to database")
        
        # Map fields to discovered schema
        db_ready_data = {
            "confidence_score": report_data.get("overall_score", 0),
            "extracted_data": {
                "risk_level": report_data.get("risk_level"),
                "report_url": report_data.get("report_url"),
                "execution_metadata": report_data.get("metadata", {})
            }
        }
        
        response = supabase.table("verification_results").insert(db_ready_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error saving report metadata: {str(e)}")
        raise e
