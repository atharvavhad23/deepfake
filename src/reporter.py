import os
import time
from pathlib import Path
from typing import Optional
from fpdf import FPDF


class ForensicPDF(FPDF):
    def header(self):
        # Header banner (Deep Navy Blue)
        self.set_fill_color(15, 32, 67)
        self.rect(0, 0, 210, 40, 'F')
        
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 12, 'NEXASHIELD DIGITAL FORENSICS UNIT', align='C', new_x="LMARGIN", new_y="NEXT")
        
        self.set_font('Helvetica', 'B', 11)
        self.cell(0, 6, 'DIGITAL EVIDENCE VERIFICATION CERTIFICATE', align='C', new_x="LMARGIN", new_y="NEXT")
        
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 4, 'LAW ENFORCEMENT PRE-TRIAL DEEPFAKE AUDIT RECORD - CONFIDENTIAL', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(10)
        
    def footer(self):
        # Footer at the bottom
        self.set_y(-20)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, 'CONFIDENTIAL DIGITAL METRICS REPORT - VERIFIED BY NEXASHIELD DUAL-STREAM PIPELINE', align='C', new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 5, f'Page {self.page_no()}', align='C')

class ForensicReportGenerator:
    """
    Forensic report generator engine using fpdf2 to produce pre-trial legal
    evidence documents detailing deepfake validation analysis.
    """
    def __init__(self, output_dir: str = "data/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        file_name: str,
        file_size_kb: float,
        sha256_hash: str,
        authenticity_score: float,
        classification: str,
        heatmap_image_path: str,
        timestamp: Optional[str] = None
    ) -> Path:
        """
        Compiles analytical metrics and images into a structured A4 single-page PDF document.
        """
        if timestamp is None:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            
        pdf = ForensicPDF()
        pdf.add_page()
        pdf.set_y(45) # Start content below header banner
        
        # 1. Metadata Block Table
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 8, '1. EVIDENCE CHAIN OF CUSTODY INFORMATION', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        
        pdf.set_font('Helvetica', 'B', 9)
        metadata = [
            ("Target File Name:", file_name),
            ("Source File Size:", f"{file_size_kb:.2f} KB"),
            ("Analysis Timestamp:", timestamp),
            ("SHA-256 Integrity Signature:", sha256_hash),
        ]
        
        # Draw metadata fields
        for key, val in metadata:
            pdf.set_font('Helvetica', 'B', 9)
            pdf.cell(55, 6, key, border=1, fill=False)
            pdf.set_font('Helvetica', '', 9)
            pdf.cell(135, 6, val, border=1, new_x="LMARGIN", new_y="NEXT")
            
        pdf.ln(6)
        
        # 2. Verdict Output Block
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 8, '2. CLASSIFICATION AUDIT VERDICT', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        
        is_manipulated = (classification.upper() == "FAKE")
        confidence_percent = (1.0 - authenticity_score) * 100 if is_manipulated else authenticity_score * 100
        
        if is_manipulated:
            pdf.set_fill_color(255, 204, 204) # Light Red
            pdf.set_text_color(153, 0, 0)     # Dark Red
            verdict_text = f"ALERT: GENERATIVE MANIPULATION DETECTED ({confidence_percent:.2f}% Anomaly Rating)"
        else:
            pdf.set_fill_color(204, 255, 204) # Light Green
            pdf.set_text_color(0, 102, 0)     # Dark Green
            verdict_text = f"VERDICT: SYSTEM SHIELD ACTIVE - PRISTINE/REAL MEDIA ({confidence_percent:.2f}% Authenticity Score)"
            
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 10, verdict_text, fill=True, border=1, align='C', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)
        
        # 3. Embed Heatmap Visual Evidence
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 8, '3. EXPLAINABILITY BIOMETRIC ANOMALY VISUALIZATION', new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font('Helvetica', '', 8)
        pdf.multi_cell(0, 4, "The map below illustrates localized anomaly activations generated using Grad-CAM. Hotspots (red/orange zones) represent regions where spatial irregularities and generative boundary peaks deviated significantly from authentic biometric patterns.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        # Insert Heatmap Image (centered)
        if os.path.exists(heatmap_image_path):
            # Place image keeping aspect ratio
            pdf.image(heatmap_image_path, x=65, y=pdf.get_y(), w=80)
            pdf.ln(82) # Move down below image height
        else:
            pdf.set_font('Helvetica', 'I', 9)
            pdf.cell(0, 8, "[Grad-CAM Heatmap Image Not Available]", align='C', new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            
        # 4. Chain of Custody & Integrity Statement
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 8, '4. CHAIN OF CUSTODY & INTEGRITY STATEMENT', new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 8)
        pdf.multi_cell(0, 4, "This verification certificate guarantees that the analyzed media file matches the specified cryptographic SHA-256 hash. The digital file's hash was calculated immediately upon ingestion, ensuring complete preservation of custody and data integrity. No post-collection modifications or edits have been introduced to the original payload during processing.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        
        # 5. Signatures Block
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(95, 5, "Analyzing Forensic Specialist:", new_x="RMARGIN", new_y="LAST")
        pdf.cell(95, 5, "Verifying Cyber Cell Authority:", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(8)
        pdf.cell(95, 5, "________________________________", new_x="RMARGIN", new_y="LAST")
        pdf.cell(95, 5, "________________________________", new_x="LMARGIN", new_y="NEXT")
        
        # Save file to directory
        pdf_filename = f"forensic_report_{sha256_hash[:16]}.pdf"
        output_path = self.output_dir / pdf_filename
        pdf.output(str(output_path))
        
        return output_path
