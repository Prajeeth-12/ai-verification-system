"""
Document Schema Definitions using Pydantic.

Defines strict validation schemas for each document type with:
- Required fields
- Optional fields
- Confidence scoring
- Type validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import date

# ============================================================================
# Aadhaar Schema
# ============================================================================

class AadhaarDocument(BaseModel):
    """Aadhaar (Indian National ID) extraction schema"""
    
    full_name: Optional[str] = Field(None, description="Full name as per Aadhaar")
    aadhaar_number: Optional[str] = Field(None, description="12-digit Aadhaar number")
    date_of_birth: Optional[str] = Field(None, description="Date of birth (DD/MM/YYYY)")
    gender: Optional[str] = Field(None, description="Gender (M/F/Other)")
    address: Optional[str] = Field(None, description="Registered address")
    phone_number: Optional[str] = Field(None, description="Mobile number")
    email: Optional[str] = Field(None, description="Email address")
    
    confidence_score: float = Field(default=0.0, description="Extraction confidence (0-1)")
    required_fields_found: int = Field(default=0, description="Number of required fields extracted")
    
    class Config:
        schema_extra = {
            "example": {
                "full_name": "Prajeeth H",
                "aadhaar_number": "XXXX XXXX XXXX",
                "date_of_birth": "12/12/1990",
                "gender": "M",
                "address": "Mallapuram, Kerala",
                "phone_number": "+91-XXXXXXXXXX",
                "email": "user@example.com",
                "confidence_score": 0.95,
                "required_fields_found": 6
            }
        }

# ============================================================================
# PAN Schema
# ============================================================================

class PANDocument(BaseModel):
    """PAN (Permanent Account Number - Tax ID) extraction schema"""
    
    pan_number: Optional[str] = Field(None, description="10-character PAN code")
    full_name: Optional[str] = Field(None, description="Name of PAN holder")
    father_name: Optional[str] = Field(None, description="Father's name")
    date_of_birth: Optional[str] = Field(None, description="Date of birth (DD/MM/YYYY)")
    category: Optional[str] = Field(None, description="PAN category (Individual/HUF/etc)")
    
    confidence_score: float = Field(default=0.0, description="Extraction confidence (0-1)")
    required_fields_found: int = Field(default=0, description="Number of required fields extracted")
    
    class Config:
        schema_extra = {
            "example": {
                "pan_number": "ABCDE1234F",
                "full_name": "Prajeeth H",
                "father_name": "H Father",
                "date_of_birth": "12/12/1990",
                "category": "Individual",
                "confidence_score": 0.92,
                "required_fields_found": 5
            }
        }

# ============================================================================
# Resume Schema
# ============================================================================

class Education(BaseModel):
    """Education entry"""
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None
    cgpa: Optional[str] = None

class Experience(BaseModel):
    """Experience entry"""
    company: Optional[str] = None
    designation: Optional[str] = None
    duration: Optional[str] = None
    responsibilities: Optional[List[str]] = None

class ResumeDocument(BaseModel):
    """Resume/CV extraction schema"""
    
    full_name: Optional[str] = Field(None, description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    phone_number: Optional[str] = Field(None, description="Contact phone")
    location: Optional[str] = Field(None, description="Current location")
    summary: Optional[str] = Field(None, description="Professional summary")
    
    skills: Optional[List[str]] = Field(default_factory=list, description="List of skills")
    education: Optional[List[Education]] = Field(default_factory=list, description="Education history")
    experience: Optional[List[Experience]] = Field(default_factory=list, description="Work experience")
    certifications: Optional[List[str]] = Field(default_factory=list, description="Certifications")
    
    confidence_score: float = Field(default=0.0, description="Extraction confidence (0-1)")
    required_fields_found: int = Field(default=0, description="Number of required fields extracted")
    
    class Config:
        schema_extra = {
            "example": {
                "full_name": "Prajeeth H",
                "email": "prajeeth@example.com",
                "phone_number": "+91-9876543210",
                "location": "Mallapuram, Kerala",
                "summary": "Experienced software engineer...",
                "skills": ["Python", "FastAPI", "OCR", "AI"],
                "education": [
                    {
                        "degree": "Bachelor of Technology",
                        "institution": "University Name",
                        "year": "2021",
                        "cgpa": "8.5"
                    }
                ],
                "experience": [
                    {
                        "company": "Tech Company",
                        "designation": "Software Engineer",
                        "duration": "2 years",
                        "responsibilities": ["Built APIs", "OCR systems"]
                    }
                ],
                "certifications": ["AWS Certified"],
                "confidence_score": 0.88,
                "required_fields_found": 4
            }
        }

# ============================================================================
# Certificate Schema
# ============================================================================

class CertificateDocument(BaseModel):
    """Certificate extraction schema"""
    
    certificate_name: Optional[str] = Field(None, description="Name of certificate")
    issued_to: Optional[str] = Field(None, description="Recipient name")
    issue_date: Optional[str] = Field(None, description="Issue date")
    expiry_date: Optional[str] = Field(None, description="Expiry date (if applicable)")
    issuing_authority: Optional[str] = Field(None, description="Issuing organization")
    certificate_number: Optional[str] = Field(None, description="Certificate ID")
    
    confidence_score: float = Field(default=0.0, description="Extraction confidence (0-1)")
    required_fields_found: int = Field(default=0, description="Number of required fields extracted")
    
    class Config:
        schema_extra = {
            "example": {
                "certificate_name": "AWS Certified Solutions Architect",
                "issued_to": "Prajeeth H",
                "issue_date": "01/01/2023",
                "expiry_date": "01/01/2026",
                "issuing_authority": "Amazon Web Services",
                "certificate_number": "AWS-123456",
                "confidence_score": 0.91,
                "required_fields_found": 5
            }
        }

# ============================================================================
# Experience Letter Schema
# ============================================================================

class ExperienceLetterDocument(BaseModel):
    """Experience Letter extraction schema"""
    
    employee_name: Optional[str] = Field(None, description="Employee name")
    company_name: Optional[str] = Field(None, description="Company name")
    designation: Optional[str] = Field(None, description="Job designation")
    joining_date: Optional[str] = Field(None, description="Date of joining")
    relieving_date: Optional[str] = Field(None, description="Date of relieving/exit")
    duration: Optional[str] = Field(None, description="Total duration of employment")
    responsibilities: Optional[List[str]] = Field(default_factory=list, description="Key responsibilities")
    
    confidence_score: float = Field(default=0.0, description="Extraction confidence (0-1)")
    required_fields_found: int = Field(default=0, description="Number of required fields extracted")
    
    class Config:
        schema_extra = {
            "example": {
                "employee_name": "Prajeeth H",
                "company_name": "Tech Company Ltd",
                "designation": "Senior Software Engineer",
                "joining_date": "01/01/2020",
                "relieving_date": "31/12/2023",
                "duration": "3 years 11 months",
                "responsibilities": ["Led development team", "Built microservices"],
                "confidence_score": 0.89,
                "required_fields_found": 6
            }
        }

# ============================================================================
# Generic Document Schema
# ============================================================================

class GenericDocument(BaseModel):
    """Generic document extraction schema (fallback)"""
    
    extracted_text: str = Field(..., description="Raw extracted text")
    document_type: Optional[str] = Field(None, description="Detected document type")
    
    confidence_score: float = Field(default=0.0, description="Classification confidence (0-1)")

# ============================================================================
# Schema Mapping
# ============================================================================

DOCUMENT_SCHEMAS = {
    "aadhaar": AadhaarDocument,
    "pan": PANDocument,
    "resume": ResumeDocument,
    "certificate": CertificateDocument,
    "experience_letter": ExperienceLetterDocument,
    "unknown": GenericDocument,
}

def get_schema_for_document(document_type: str):
    """Get Pydantic schema for document type"""
    return DOCUMENT_SCHEMAS.get(document_type, GenericDocument)
