import os
import io
import yaml
from docx import Document
from fpdf import FPDF
from models.database import ProcessNote

def load_sections_config():
    try:
        with open("config/sections.yaml", "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {"sections": []}

def get_section_name(sections_config, section_id):
    for sec in sections_config.get("sections", []):
        if sec.get("id") == section_id:
            return sec.get("name")
    return "Unknown Section"

def generate_docx(note: ProcessNote) -> io.BytesIO:
    doc = Document()
    doc.add_heading(f"Process Note: {note.process_name}", 0)
    
    doc.add_paragraph(f"Team: {note.team}")
    doc.add_paragraph(f"Version: {note.version}")
    doc.add_paragraph(f"Status: {note.status}")
    doc.add_paragraph(f"SME: {note.subject_matter_expert}")
    doc.add_paragraph(f"Process Owner: {note.process_owner}")
    doc.add_paragraph(f"Effective Date: {note.effective_date}")
    
    doc.add_page_break()
    
    config = load_sections_config()
    
    def get_sort_key(s):
        try:
            return [int(x) for x in s.section_id.split('.')]
        except ValueError:
            return [999]
            
    # Sort sections correctly numerically (e.g. 1.10 after 1.9)
    sorted_sections = sorted(note.sections, key=get_sort_key)
    
    for section in sorted_sections:
        sec_name = get_section_name(config, section.section_id)
        doc.add_heading(f"{section.section_id} {sec_name}", level=1)
        
        if section.content:
            doc.add_paragraph(section.content)
            
        if section.structured_data:
            if isinstance(section.structured_data, list) and len(section.structured_data) > 0:
                headers = list(section.structured_data[0].keys())
                table = doc.add_table(rows=1, cols=len(headers))
                table.style = 'Table Grid'
                hdr_cells = table.rows[0].cells
                for i, header in enumerate(headers):
                    hdr_cells[i].text = str(header)
                
                for row_data in section.structured_data:
                    row_cells = table.add_row().cells
                    for i, header in enumerate(headers):
                        row_cells[i].text = str(row_data.get(header, ""))
                        
        doc.add_paragraph() # Add spacing
        
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream

class CustomPDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 12)
        self.cell(0, 10, "Process Note Document", align="C")
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

def generate_pdf(note: ProcessNote) -> io.BytesIO:
    def safe_str(s):
        if s is None:
            return ""
        return str(s).encode('latin-1', 'replace').decode('latin-1')
        
    pdf = CustomPDF()
    pdf.add_page()
    
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, safe_str(f"Process Note: {note.process_name}"), ln=True)
    
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 8, safe_str(f"Team: {note.team}"), ln=True)
    pdf.cell(0, 8, safe_str(f"Version: {note.version}"), ln=True)
    pdf.cell(0, 8, safe_str(f"Status: {note.status}"), ln=True)
    pdf.cell(0, 8, safe_str(f"SME: {note.subject_matter_expert}"), ln=True)
    pdf.cell(0, 8, safe_str(f"Process Owner: {note.process_owner}"), ln=True)
    pdf.cell(0, 8, safe_str(f"Effective Date: {note.effective_date}"), ln=True)
    pdf.ln(10)
    
    def get_sort_key(s):
        try:
            return [int(x) for x in s.section_id.split('.')]
        except ValueError:
            return [999]
            
    config = load_sections_config()
    sorted_sections = sorted(note.sections, key=get_sort_key)
    
    for section in sorted_sections:
        sec_name = get_section_name(config, section.section_id)
        pdf.set_font("helvetica", "B", 14)
        pdf.multi_cell(0, 10, safe_str(f"{section.section_id} {sec_name}"))
        
        pdf.set_font("helvetica", "", 11)
        if section.content:
            pdf.multi_cell(0, 8, safe_str(section.content))
            pdf.ln(5)
            
        if section.structured_data and isinstance(section.structured_data, list) and len(section.structured_data) > 0:
            headers = list(section.structured_data[0].keys())
            
            pdf.set_font("helvetica", "", 9)
            try:
                with pdf.table() as table:
                    header_row = table.row()
                    for header in headers:
                        header_row.cell(safe_str(str(header)))
                    
                    for row_data in section.structured_data:
                        data_row = table.row()
                        for header in headers:
                            val = str(row_data.get(header, ""))
                            data_row.cell(safe_str(val))
            except Exception as e:
                pdf.multi_cell(0, 8, safe_str(f"(Table rendering failed: {str(e)})"))
            pdf.ln(5)
            
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return io.BytesIO(pdf_bytes)
