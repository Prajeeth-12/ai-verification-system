"""
Specialized Extraction Prompts for Different Document Types.

Each document type gets a custom prompt optimized for:
- Specific field extraction
- Format validation
- JSON reliability
- Accuracy improvement
"""

AADHAAR_EXTRACTION_PROMPT = """
You are an expert Aadhaar (Indian National ID) document analyst.

Extract ONLY the following structured information from the OCR text.

RULES:
- Return ONLY valid raw JSON
- NO markdown, NO code blocks, NO explanations
- For missing fields, use null
- Validate Indian format for all fields
- Extract exactly as appears (preserve case)

EXTRACT THIS SCHEMA:
{{
    "full_name": null,
    "aadhaar_number": null,
    "date_of_birth": null,
    "gender": null,
    "address": null,
    "phone_number": null,
    "email": null
}}

FIELD RULES:
- full_name: Complete name as written
- aadhaar_number: 12 digits (format: XXXX XXXX XXXX)
- date_of_birth: Format as DD/MM/YYYY
- gender: Single letter (M/F/O) or full word
- address: Full address including state
- phone_number: Extract all contact details
- email: Valid email if present

OCR TEXT:
{ocr_text}

RESPOND WITH ONLY THE JSON OBJECT.
"""

PAN_EXTRACTION_PROMPT = """
You are an expert PAN (Permanent Account Number) document analyst.

Extract ONLY the following structured information from the OCR text.

RULES:
- Return ONLY valid raw JSON
- NO markdown, NO code blocks, NO explanations
- For missing fields, use null
- PAN format: 10 characters (5 letters + 4 numbers + 1 letter)

EXTRACT THIS SCHEMA:
{{
    "pan_number": null,
    "full_name": null,
    "father_name": null,
    "date_of_birth": null,
    "category": null
}}

FIELD RULES:
- pan_number: Exactly 10 characters, uppercase
- full_name: Complete name as per document
- father_name: Father/Husband name
- date_of_birth: Format as DD/MM/YYYY
- category: Individual, HUF, Company, etc.

OCR TEXT:
{ocr_text}

RESPOND WITH ONLY THE JSON OBJECT.
"""

RESUME_EXTRACTION_PROMPT = """
You are an expert resume/CV parser and analyst.

Extract ONLY the following structured information from the OCR text.

RULES:
- Return ONLY valid raw JSON
- NO markdown, NO code blocks, NO explanations
- For missing fields, use null or empty array []
- Preserve original capitalization and spelling

EXTRACT THIS SCHEMA:
{{
    "full_name": null,
    "email": null,
    "phone_number": null,
    "location": null,
    "summary": null,
    "skills": [],
    "education": [
        {{"degree": null, "institution": null, "year": null, "cgpa": null}}
    ],
    "experience": [
        {{"company": null, "designation": null, "duration": null, "responsibilities": []}}
    ],
    "certifications": []
}}

FIELD RULES:
- full_name: Contact person name
- email: Valid email address
- phone_number: Phone with country code if present
- location: City/Country
- summary: Professional summary/objective
- skills: List of technical and soft skills
- education: Array of degrees and institutions
- experience: Array of employment records
- certifications: Professional certifications

OCR TEXT:
{ocr_text}

RESPOND WITH ONLY THE JSON OBJECT.
"""

CERTIFICATE_EXTRACTION_PROMPT = """
You are an expert certificate document analyst.

Extract ONLY the following structured information from the OCR text.

RULES:
- Return ONLY valid raw JSON
- NO markdown, NO code blocks, NO explanations
- For missing fields, use null
- Dates in DD/MM/YYYY format

EXTRACT THIS SCHEMA:
{{
    "certificate_name": null,
    "issued_to": null,
    "issue_date": null,
    "expiry_date": null,
    "issuing_authority": null,
    "certificate_number": null
}}

FIELD RULES:
- certificate_name: Name/title of certificate
- issued_to: Recipient's name
- issue_date: Certificate issue date
- expiry_date: Validity/expiry date if applicable
- issuing_authority: Organization that issued
- certificate_number: Certificate ID/code

OCR TEXT:
{ocr_text}

RESPOND WITH ONLY THE JSON OBJECT.
"""

EXPERIENCE_LETTER_EXTRACTION_PROMPT = """
You are an expert employment verification and experience letter analyst.

Extract ONLY the following structured information from the OCR text.

RULES:
- Return ONLY valid raw JSON
- NO markdown, NO code blocks, NO explanations
- For missing fields, use null or empty array []
- Dates in DD/MM/YYYY format

EXTRACT THIS SCHEMA:
{{
    "employee_name": null,
    "company_name": null,
    "designation": null,
    "joining_date": null,
    "relieving_date": null,
    "duration": null,
    "responsibilities": []
}}

FIELD RULES:
- employee_name: Employee's full name
- company_name: Employer organization name
- designation: Job title/position
- joining_date: Date of employment start
- relieving_date: Date of employment end
- duration: Total period of employment
- responsibilities: Array of key responsibilities

OCR TEXT:
{ocr_text}

RESPOND WITH ONLY THE JSON OBJECT.
"""

GENERIC_EXTRACTION_PROMPT = """
You are a document intelligence AI system.

Extract structured information from the OCR text.

RULES:
- Return ONLY valid raw JSON
- NO markdown, NO code blocks, NO explanations
- For fields you cannot identify, use null

Extract as much relevant information as possible in a structured format.

OCR TEXT:
{ocr_text}

RESPOND WITH ONLY THE JSON OBJECT:
{{
    "extracted_data": {{}},
    "notes": null
}}
"""

# Prompt mapping
DOCUMENT_PROMPTS = {
    "aadhaar": AADHAAR_EXTRACTION_PROMPT,
    "pan": PAN_EXTRACTION_PROMPT,
    "resume": RESUME_EXTRACTION_PROMPT,
    "certificate": CERTIFICATE_EXTRACTION_PROMPT,
    "experience_letter": EXPERIENCE_LETTER_EXTRACTION_PROMPT,
    "unknown": GENERIC_EXTRACTION_PROMPT,
}

def get_prompt_for_document(document_type: str) -> str:
    """Get specialized extraction prompt for document type"""
    return DOCUMENT_PROMPTS.get(document_type, GENERIC_EXTRACTION_PROMPT)
