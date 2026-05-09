import logging
from typing import List, Dict, Any
from datetime import datetime
import re

# Configure structured logging
logger = logging.getLogger(__name__)

def verify_documents(parsed_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Cross-checks information across multiple parsed documents to detect inconsistencies,
    fraud signals, and calculate an overall verification confidence score.
    """
    logger.info(f"VERIFICATION_START: Processing {len(parsed_documents)} documents")
    
    if not parsed_documents:
        logger.warning("VERIFICATION_EMPTY: No documents provided for verification")
        return {
            "verification_score": 0,
            "risk_level": "HIGH",
            "flags": ["NO_DOCUMENTS_PROVIDED"],
            "verified_fields": {},
            "status": "skipped"
        }

    flags = []
    verified_fields = {
        "names": set(),
        "dobs": set(),
        "ids": {}
    }
    
    # 1. Collect Data for Comparison
    comparison_data = _aggregate_document_data(parsed_documents)
    
    # 2. Perform Cross-Checks
    mismatch_stats = _cross_check_fields(comparison_data, flags, verified_fields)
    
    # 3. Detect Fraud Signals & Inconsistencies
    fraud_stats = _detect_suspicious_patterns(parsed_documents, flags)
    
    # 4. Calculate Weighted Confidence Score
    scoring_result = _calculate_confidence_score(
        doc_count=len(parsed_documents),
        flags=flags,
        mismatches=mismatch_stats,
        parsing_failures=fraud_stats["parsing_failures"]
    )
    
    # Convert sets to lists for JSON serialization
    verified_fields["names"] = list(verified_fields["names"])
    verified_fields["dobs"] = list(verified_fields["dobs"])
    
    report = {
        "verification_score": scoring_result["score"],
        "risk_level": scoring_result["risk_level"],
        "flags": flags,
        "verified_fields": verified_fields,
        "metadata": {
            "documents_processed": len(parsed_documents),
            "mismatches_detected": mismatch_stats["total"],
            "timestamp": datetime.now().isoformat()
        }
    }
    
    logger.info(f"VERIFICATION_COMPLETE: Score={report['verification_score']}, Risk={report['risk_level']}, FlagsCount={len(flags)}")
    
    return report

def _aggregate_document_data(documents: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Groups data by field type for easy comparison.
    """
    aggregated = {
        "names": [],
        "dobs": [],
        "ids": []
    }
    
    for doc in documents:
        doc_type = doc.get("metadata", {}).get("document_type", "unknown").lower()
        data = doc.get("data", {})
        
        # Collect Names (normalize for comparison)
        name = data.get("name")
        if name:
            aggregated["names"].append({
                "source": doc_type,
                "value": str(name).strip().upper(),
                "original": name
            })
            
        # Collect DOBs
        dob = data.get("dob")
        if dob:
            aggregated["dobs"].append({
                "source": doc_type,
                "value": _normalize_dob(str(dob)),
                "original": dob
            })
            
        # Collect IDs
        for id_field in ["aadhaar_number", "pan_number"]:
            if data.get(id_field):
                aggregated["ids"].append({
                    "source": doc_type,
                    "field": id_field,
                    "value": str(data[id_field]).strip()
                })
                
    return aggregated

def _cross_check_fields(data: Dict[str, List[Dict[str, Any]]], flags: List[str], verified_fields: Dict[str, Any]) -> Dict[str, int]:
    """
    Compares aggregated data to find mismatches.
    """
    stats = {"total": 0, "critical": 0}
    
    # Check Names
    if len(data["names"]) > 1:
        # Simple majority or first doc as reference (identity docs prioritized)
        # Sort so identity docs come first if possible
        priority_order = {"aadhaar": 0, "pan": 1, "certificate": 2, "resume": 3}
        sorted_names = sorted(data["names"], key=lambda x: priority_order.get(x["source"], 99))
        
        reference = sorted_names[0]
        for entry in sorted_names[1:]:
            if entry["value"] != reference["value"]:
                # Check if one is a substring of another (common for middle names)
                if reference["value"] in entry["value"] or entry["value"] in reference["value"]:
                    logger.info(f"Partial name match: {reference['value']} vs {entry['value']}")
                    verified_fields["names"].add(reference["original"])
                else:
                    flag = f"NAME_MISMATCH: '{reference['original']}' ({reference['source']}) vs '{entry['original']}' ({entry['source']})"
                    flags.append(flag)
                    logger.warning(f"DETECTION_MISMATCH: {flag}")
                    stats["total"] += 1
                    stats["critical"] += 1
            else:
                verified_fields["names"].add(reference["original"])
    elif len(data["names"]) == 1:
        verified_fields["names"].add(data["names"][0]["original"])

    # Check DOBs
    if len(data["dobs"]) > 1:
        reference = data["dobs"][0]
        for entry in data["dobs"][1:]:
            if entry["value"] != reference["value"]:
                flag = f"DOB_MISMATCH: '{reference['original']}' vs '{entry['original']}'"
                flags.append(flag)
                logger.warning(f"DETECTION_MISMATCH: {flag}")
                stats["total"] += 1
                stats["critical"] += 1
            else:
                verified_fields["dobs"].add(reference["original"])
    elif len(data["dobs"]) == 1:
        verified_fields["dobs"].add(data["dobs"][0]["original"])

    # Check Certificate Ownership
    # (If we have a name from ID and a name from Certificate, do they match?)
    # This is handled by the Name Check above if certificate was in the list.
    
    return stats

def _detect_suspicious_patterns(documents: List[Dict[str, Any]], flags: List[str]) -> Dict[str, int]:
    """
    Detects fraud signals and inconsistencies within individual documents.
    """
    stats = {"parsing_failures": 0}
    
    for doc in documents:
        doc_type = doc.get("metadata", {}).get("document_type", "unknown").lower()
        success = doc.get("success", False)
        data = doc.get("data", {})
        
        if not success:
            flags.append(f"PARSING_FAILURE: Failed to extract data from {doc_type}")
            stats["parsing_failures"] += 1
            continue
            
        # Check for missing critical fields
        if doc_type == "aadhaar" and not data.get("aadhaar_number"):
            flags.append("MISSING_IDENTITY_FIELD: Aadhaar number not found")
        elif doc_type == "pan" and not data.get("pan_number"):
            flags.append("MISSING_IDENTITY_FIELD: PAN number not found")
            
        # Logic for suspicious dates (e.g. Issue Date in future)
        issue_date = data.get("issue_date")
        if issue_date:
            try:
                # Basic check if it's a future date
                # This is simplified; real logic would parse the date properly
                if "2027" in str(issue_date) or "2028" in str(issue_date):
                    flags.append(f"SUSPICIOUS_DATE: Issue date '{issue_date}' seems to be in the future")
            except:
                pass
                
    return stats

def _calculate_confidence_score(doc_count: int, flags: List[str], mismatches: Dict[str, int], parsing_failures: int) -> Dict[str, Any]:
    """
    Calculates a weighted confidence score (0-100).
    """
    score = 100
    
    # Deductions
    score -= (mismatches["critical"] * 40)
    score -= (parsing_failures * 20)
    
    # Deduction for other flags
    other_flags = [f for f in flags if "MISMATCH" not in f and "PARSING_FAILURE" not in f]
    score -= (len(other_flags) * 10)
    
    # Bonuses
    if doc_count >= 2 and mismatches["total"] == 0 and parsing_failures == 0:
        score += 10 # Consistency bonus
        
    # Minimum score clamp
    score = max(0, min(100, score))
    
    # Risk Level
    risk_level = "LOW"
    if score < 50 or mismatches["critical"] > 0:
        risk_level = "HIGH"
    elif score < 85 or flags:
        risk_level = "MEDIUM"
        
    return {"score": int(score), "risk_level": risk_level}

def _normalize_dob(dob_str: str) -> str:
    """
    Attempts to normalize date strings for comparison.
    """
    # Remove non-alphanumeric and spaces
    clean = re.sub(r'[^a-zA-Z0-9]', '', dob_str)
    return clean.lower()
