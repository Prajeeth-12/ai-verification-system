from typing import TypedDict, List, Dict, Any, Optional, Union
from datetime import datetime
import logging
from langgraph.graph import StateGraph, END

# Service imports
from app.services.ocr_service import process_document
from app.services.document_classifier import DocumentClassifier, DocumentType
from app.services.parser_service import parse_document_text
from app.services.verification_service import verify_documents
from app.services.semantic_verification_service import semantic_verification_service

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# PART 1 — AGENT STATE
# ============================================================================

class AgentState(TypedDict):
    """Centralized state for the LangGraph multi-agent workflow."""
    # Inputs
    urls: List[str]
    
    # Intermediate Results
    ocr_results: List[Dict[str, Any]]
    parsed_docs: List[Dict[str, Any]]
    verification_result: Dict[str, Any]
    semantic_result: Dict[str, Any]
    
    # Final Outputs
    final_report: Dict[str, Any]
    report_url: Optional[str]
    
    # Workflow Metadata
    metadata: Dict[str, Any]
    errors: List[str]
    status: str  # pending, processing, completed, failed
    current_node: str

# ============================================================================
# PART 2 — AGENT NODES
# ============================================================================

def ocr_agent(state: AgentState) -> Dict[str, Any]:
    """Extracts raw text from documents with error handling."""
    logger.info("NODE_START: OCR Agent")
    results = []
    errors = []
    
    for url in state["urls"]:
        try:
            logger.info(f"OCR_AGENT: Processing {url}")
            text, metadata = process_document(url)
            results.append({
                "text": text,
                "metadata": metadata,
                "url": url,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            err_msg = f"OCR_FAILURE: {url} - {str(e)}"
            logger.error(err_msg)
            errors.append(err_msg)
            
    if not results and errors:
        return {"errors": state.get("errors", []) + errors, "status": "failed", "current_node": "ocr"}
        
    return {
        "ocr_results": results, 
        "errors": state.get("errors", []) + errors,
        "current_node": "ocr"
    }

def parser_agent(state: AgentState) -> Dict[str, Any]:
    """Classifies and parses OCR text into structured JSON."""
    logger.info("NODE_START: Parser Agent")
    parsed_docs = []
    errors = []
    
    for ocr in state.get("ocr_results", []):
        try:
            text = ocr["text"]
            doc_type, confidence, _ = DocumentClassifier.classify(text)
            
            # Use specialized parser
            result = parse_document_text(text, doc_type.value)
            
            if result.get("success"):
                # Add metadata for later stages
                result["metadata"]["document_type"] = doc_type.value
                result["metadata"]["classification_confidence"] = confidence
                parsed_docs.append(result)
            else:
                errors.append(f"PARSING_FAILED: {ocr.get('url')} - {result.get('error')}")
        except Exception as e:
            errors.append(f"PARSER_NODE_ERROR: {str(e)}")
            
    return {
        "parsed_docs": parsed_docs,
        "errors": state.get("errors", []) + errors,
        "current_node": "parser"
    }

def verification_agent(state: AgentState) -> Dict[str, Any]:
    """Performs structural and ID cross-verification."""
    logger.info("NODE_START: Verification Agent")
    try:
        parsed_docs = state.get("parsed_docs", [])
        if not parsed_docs:
            return {"errors": state.get("errors", []) + ["NO_DOCS_TO_VERIFY"], "current_node": "verifier"}
            
        result = verify_documents(parsed_docs)
        return {"verification_result": result, "current_node": "verifier"}
    except Exception as e:
        logger.error(f"VERIFICATION_NODE_ERROR: {str(e)}")
        return {"errors": state.get("errors", []) + [str(e)], "current_node": "verifier"}

def semantic_agent(state: AgentState) -> Dict[str, Any]:
    """Performs semantic consistency checks using RAG logic."""
    logger.info("NODE_START: Semantic Agent")
    try:
        parsed_docs = state.get("parsed_docs", [])
        # Conditional: skip if parsing completely failed
        if not parsed_docs:
            return {"semantic_result": {"status": "skipped", "reason": "No parsed data"}, "current_node": "semantic"}
            
        result = semantic_verification_service.verify_semantic_consistency(parsed_docs)
        return {"semantic_result": result, "current_node": "semantic"}
    except Exception as e:
        logger.error(f"SEMANTIC_NODE_ERROR: {str(e)}")
        return {"errors": state.get("errors", []) + [str(e)], "current_node": "semantic"}

def report_agent(state: AgentState) -> Dict[str, Any]:
    """Consolidates all findings into a final report structure."""
    logger.info("NODE_START: Report Agent")
    try:
        v = state.get("verification_result", {})
        s = state.get("semantic_result", {})
        
        # Calculate Unified Risk
        base_score = v.get("verification_score", 0)
        sem_score = s.get("semantic_score", 0)
        overall_score = int((base_score * 0.4) + (sem_score * 0.6))
        
        report = {
            "overall_score": overall_score,
            "risk_level": "LOW" if overall_score > 80 else "MEDIUM" if overall_score > 50 else "HIGH",
            "verification_details": v,
            "semantic_details": s,
            "flags": list(set(v.get("flags", []) + s.get("risk_flags", []))),
            "timestamp": datetime.now().isoformat(),
            "execution_metadata": {
                "nodes_executed": ["ocr", "parser", "verifier", "semantic"],
                "error_count": len(state.get("errors", []))
            }
        }
        
        return {"final_report": report, "status": "completed", "current_node": "reporter"}
    except Exception as e:
        return {"errors": state.get("errors", []) + [str(e)], "status": "failed", "current_node": "reporter"}

# ============================================================================
# PART 3 — GRAPH ORCHESTRATION
# ============================================================================

def route_after_ocr(state: AgentState):
    """Conditional routing based on OCR success."""
    if state.get("status") == "failed" or not state.get("ocr_results"):
        return END
    return "parser"

def route_after_parser(state: AgentState):
    """Conditional routing based on Parser success."""
    if not state.get("parsed_docs"):
        return "reporter" # Jump to report with failures
    return "verifier"

def create_verification_graph():
    """Builds the deterministic multi-agent workflow."""
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("ocr", ocr_agent)
    workflow.add_node("parser", parser_agent)
    workflow.add_node("verifier", verification_agent)
    workflow.add_node("semantic", semantic_agent)
    workflow.add_node("reporter", report_agent)
    
    # Define Edges with Conditional Logic
    workflow.set_entry_point("ocr")
    workflow.add_conditional_edges("ocr", route_after_ocr, {"parser": "parser", END: END})
    workflow.add_conditional_edges("parser", route_after_parser, {"verifier": "verifier", "reporter": "reporter"})
    workflow.add_edge("verifier", "semantic")
    workflow.add_edge("semantic", "reporter")
    workflow.add_edge("reporter", END)
    
    return workflow.compile()

async def run_full_orchestration(urls: List[str]) -> Dict[str, Any]:
    """Executes the complete multi-agent workflow."""
    graph = create_verification_graph()
    
    initial_state: AgentState = {
        "urls": urls,
        "ocr_results": [],
        "parsed_docs": [],
        "verification_result": {},
        "semantic_result": {},
        "final_report": {},
        "report_url": None,
        "metadata": {"start_time": datetime.now().isoformat()},
        "errors": [],
        "status": "processing",
        "current_node": "entry"
    }
    
    try:
        final_state = await graph.ainvoke(initial_state)
        return final_state
    except Exception as e:
        logger.error(f"WORKFLOW_CRITICAL_FAILURE: {str(e)}")
        return {**initial_state, "status": "failed", "errors": [str(e)]}
