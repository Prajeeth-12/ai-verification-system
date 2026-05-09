import os
import logging
from datetime import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from app.db.supabase import supabase
from app.services.database_service import save_report_metadata

# Configure logging
logger = logging.getLogger(__name__)

def generate_and_upload_report(workflow_state: Dict[str, Any]) -> str:
    """
    Generates a professional PDF report from workflow results, uploads it to Supabase Storage,
    and persists metadata in the database.
    """
    try:
        logger.info("REPORT_GENERATION: Starting process")
        
        report_data = workflow_state.get("final_report", {})
        temp_filename = f"report_{int(datetime.now().timestamp())}.pdf"
        temp_path = os.path.join("app/uploads", temp_filename)
        
        # 1. Create PDF using ReportLab Platypus
        doc = SimpleDocTemplate(temp_path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=20,
            textColor=colors.HexColor("#1A237E")
        )
        elements.append(Paragraph("AI Verification Intelligence Report", title_style))
        elements.append(Spacer(1, 12))
        
        # Summary Section
        elements.append(Paragraph("Executive Summary", styles['Heading2']))
        summary_data = [
            ["Metric", "Value"],
            ["Overall Score", f"{report_data.get('overall_score', 0)}/100"],
            ["Risk Level", report_data.get('risk_level', 'UNKNOWN')],
            ["Status", workflow_state.get('status', 'Completed')],
            ["Timestamp", report_data.get('timestamp', '')]
        ]
        
        t = Table(summary_data, colWidths=[150, 300])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E8EAF6")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#1A237E")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        elements.append(t)
        elements.append(Spacer(1, 20))
        
        # Detailed Scores
        elements.append(Paragraph("Verification Analysis", styles['Heading2']))
        v_details = report_data.get("verification_details", {})
        s_details = report_data.get("semantic_details", {})
        
        detail_data = [
            ["Dimension", "Score", "Confidence"],
            ["Structural Verification", f"{v_details.get('verification_score', 0)}", "High"],
            ["Semantic Consistency", f"{s_details.get('semantic_score', 0)}", "Weighted"],
        ]
        
        dt = Table(detail_data, colWidths=[150, 150, 150])
        dt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F5F5F5")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        elements.append(dt)
        elements.append(Spacer(1, 20))
        
        # Risk Flags
        elements.append(Paragraph("Identified Risk Flags", styles['Heading2']))
        flags = report_data.get("flags", [])
        if not flags:
            elements.append(Paragraph("No critical risks identified.", styles['Normal']))
        else:
            for flag in flags:
                elements.append(Paragraph(f"• {flag}", styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # Semantic Matches
        elements.append(Paragraph("Semantic Evidence Support", styles['Heading2']))
        matches = report_data.get("semantic_matches", [])
        if not matches:
            elements.append(Paragraph("No direct semantic matches found across documents.", styles['Normal']))
        else:
            for match in matches:
                elements.append(Paragraph(f"• {match}", styles['Normal']))
                
        # Build PDF
        doc.build(elements)
        
        # 2. Upload to Supabase Storage
        logger.info(f"REPORT_UPLOAD: Uploading {temp_filename} to Supabase")
        with open(temp_path, 'rb') as f:
            storage_response = supabase.storage.from_("reports").upload(
                temp_filename, 
                f, 
                file_options={"content-type": "application/pdf"}
            )
            
        report_url = supabase.storage.from_("reports").get_public_url(temp_filename)
        
        # 3. Persist Metadata
        db_data = {
            "overall_score": report_data.get("overall_score"),
            "risk_level": report_data.get("risk_level"),
            "report_url": report_url,
            "metadata": workflow_state.get("execution_metadata", {}),
            "created_at": datetime.now().isoformat()
        }
        save_report_metadata(db_data)
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        logger.info(f"REPORT_COMPLETE: Report URL: {report_url}")
        return report_url
        
    except Exception as e:
        logger.error(f"REPORT_GENERATION_FAILED: {str(e)}")
        raise e
