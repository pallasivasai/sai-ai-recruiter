from io import BytesIO
from pathlib import Path
from docx import Document
from pypdf import PdfReader
def extract_resume_text(filename:str,data:bytes)->str:
    ext=Path(filename).suffix.lower()
    if ext==".pdf": return "\n".join(p.extract_text() or "" for p in PdfReader(BytesIO(data)).pages).strip()
    if ext==".docx":
        doc=Document(BytesIO(data)); parts=[p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows: parts.append(" | ".join(cell.text for cell in row.cells))
        return "\n".join(parts).strip()
    if ext==".txt": return data.decode("utf-8",errors="replace").strip()
    raise ValueError("Supported resume formats: PDF, DOCX and TXT.")
