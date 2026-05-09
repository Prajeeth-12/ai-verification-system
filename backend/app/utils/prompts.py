def get_parsing_prompt(doc_type, text):
    """
    Returns a specialized prompt for document parsing based on document type.
    """
    base_prompt = "You are an AI specialized in document parsing. Extract the information from the following OCR text and return it strictly as a JSON object."
    
    prompts = {
        "aadhaar": """
            Extract: full_name, date_of_birth, gender, aadhaar_number, address.
            Return JSON only.
        """,
        "pan": """
            Extract: full_name, father_name, date_of_birth, pan_number.
            Return JSON only.
        """,
        "resume": """
            Extract: full_name, email, phone, skills (list), education (list of dicts with degree, institution), experience (list of dicts with company, role, duration).
            Return JSON only.
        """,
        "certificate": """
            Extract: certificate_name, issued_to, issued_by, date_of_issue.
            Return JSON only.
        """,
        "experience_letter": """
            Extract: employee_name, company_name, designation, duration_from, duration_to.
            Return JSON only.
        """
    }
    
    specific_instructions = prompts.get(doc_type, "Extract all relevant key-value pairs.")
    
    return f"{base_prompt}\n\nDocument Type: {doc_type}\nInstructions: {specific_instructions}\n\nOCR Text:\n{text}\n\nJSON Output:"
