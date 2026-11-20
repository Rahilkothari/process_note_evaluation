import os
import io
import re
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple
import yaml
import pdfplumber
import docx
from models.database import ProcessNote, ProcessSection
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

def load_sections_config() -> List[Dict[str, Any]]:
    try:
        with open("config/sections.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f).get("sections", [])
    except Exception:
        return []

SECTION_KEYWORDS = {
    "1.1": ["approval matrix", "approval", "approver", "sign-off"],
    "1.2": ["change history", "document history", "amendment", "version history"],
    "1.3": ["review cycle", "review frequency", "next review"],
    "1.4": ["related documents", "related document", "policies", "reference"],
    "1.5": ["performance parameters", "kpi", "key performance", "metrics", "target"],
    "1.6": ["coverage", "scope", "in-scope", "out-of-scope", "boundaries"],
    "1.7": ["start point", "entry criteria", "initiation", "trigger"],
    "1.8": ["end point", "exit criteria", "conclusion", "closure"],
    "1.9": ["introduction", "background", "context", "vision", "mission"],
    "1.10": ["objective", "goals", "purpose", "aim"],
    "1.11": ["flowchart", "process flow", "diagram", "workflow"],
    "1.12": ["process description", "detailed steps", "activity", "procedure", "sub-steps"],
    "1.13": ["raci matrix", "raci", "responsible", "accountable"],
    "1.14": ["business rules", "business rule", "governance rules", "policies"],
    "1.15": ["exception", "change management", "deviation", "mitigation"],
    "1.16": ["risk management", "risk", "mitigation", "controls"],
    "1.17": ["compliance management", "compliance", "regulatory", "audit"],
    "1.18": ["data archival", "retention", "storage", "archival"],
    "1.19": ["abbreviations", "acronyms", "definitions", "glossary"],
    "1.20": ["best practices", "best practice", "recommendations"],
    "1.21": ["innovations", "innovation", "improvements", "novel"],
    "1.22": ["sipoc", "supplier", "inputs", "outputs", "customer"]
}

class DocumentImporter:
    def __init__(self):
        self.sections_config = load_sections_config()
        self.sections_by_id = {s["id"]: s for s in self.sections_config}

    def import_document(
        self,
        file_bytes: bytes,
        filename: str,
        process_name: str,
        team_name: str,
        version: str = "1.0",
        user_id: int = None,
        db: Session = None
    ) -> ProcessNote:
        """Imports a PDF or DOCX file, extracts all sections, and saves to database."""
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            parsed_sections = self._parse_pdf(file_bytes)
        elif ext in [".docx", ".doc"]:
            parsed_sections = self._parse_docx(file_bytes)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Please upload a .pdf or .docx file.")

        # Create ProcessNote record
        doc_uuid = str(uuid.uuid4())
        new_note = ProcessNote(
            document_id=doc_uuid,
            process_name=process_name.strip() if process_name else os.path.splitext(filename)[0].replace("_", " "),
            team=team_name.strip() if team_name else "Operations",
            version=version.strip() if version else "1.0",
            status="DRAFT",
            document_type="PROCESS_NOTE",
            created_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Pull metadata from Approval Matrix (1.1) if available
        appr_data = parsed_sections.get("1.1", {}).get("structured_data", [])
        if appr_data:
            for row in appr_data:
                role = str(row.get("Role", "")).lower()
                name = str(row.get("Name", "")).strip()
                if not name or name.lower() in ["n/a", "none"]:
                    continue
                if "owner" in role:
                    new_note.process_owner = name
                elif "approver" in role:
                    new_note.process_approver = name
                elif "reviewer" in role:
                    new_note.process_reviewer = name
                elif "champion" in role:
                    new_note.process_champion = name
                elif "sme" in role or "expert" in role:
                    new_note.subject_matter_expert = name

        # Pull Review Cycle (1.3) dates if available
        rev_data = parsed_sections.get("1.3", {}).get("structured_data", [])
        if rev_data and isinstance(rev_data, list) and len(rev_data) > 0:
            row0 = rev_data[0]
            new_note.effective_date = str(row0.get("Effective Date", "")).strip() or None
            new_note.next_review_date = str(row0.get("Next Review Date", "")).strip() or None

        db.add(new_note)
        db.flush()

        # Create all 22 ProcessSection records
        sec_records = []
        for sec_cfg in self.sections_config:
            sid = sec_cfg["id"]
            sec_type = sec_cfg["type"]
            data = parsed_sections.get(sid, {})
            content = data.get("content")
            s_data = data.get("structured_data")

            # Fallback if section wasn't in the document: create clean empty or default
            if not content and not s_data:
                if sec_type == "table":
                    s_data = sec_cfg.get("default_rows", [])
                elif sec_type == "flowchart":
                    content = (
                        "flowchart TD\n"
                        f"    Start([Process Start: {new_note.process_name}]) --> Step1[\"1. Process Initiation\"]\n"
                        "    Step1 --> End([Process Complete])"
                    )
                else:
                    content = ""

            ps = ProcessSection(
                process_note_id=new_note.id,
                process_name=new_note.process_name,
                section_id=sid,
                content=content,
                structured_data=s_data
            )
            sec_records.append(ps)

        new_note.sections = sec_records
        db.commit()
        db.refresh(new_note)
        return new_note

    def _parse_pdf(self, file_bytes: bytes) -> Dict[str, Dict[str, Any]]:
        """Extracts text and tables from PDF and categorizes into the 22 sections."""
        all_text_pages = []
        all_tables = []

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                txt = page.extract_text() or ""
                all_text_pages.append(txt)
                tbls = page.extract_tables()
                if tbls:
                    for t in tbls:
                        all_tables.append({"page": page_num + 1, "table": t})

        full_doc_text = "\n\n".join(all_text_pages)
        return self._structure_raw_document(full_doc_text, all_tables)

    def _parse_docx(self, file_bytes: bytes) -> Dict[str, Dict[str, Any]]:
        """Extracts paragraphs and tables from DOCX and categorizes into the 22 sections."""
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_doc_text = "\n\n".join(paragraphs)

        all_tables = []
        for idx, t in enumerate(doc.tables):
            table_rows = []
            for r in t.rows:
                cells = [c.text.strip().replace("\n", " ") for c in r.cells]
                table_rows.append(cells)
            if table_rows:
                all_tables.append({"table_idx": idx, "table": table_rows})

        return self._structure_raw_document(full_doc_text, all_tables)

    def _structure_raw_document(self, full_text: str, tables_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Categorizes raw text blocks and tables into the 22 sections."""
        sections_data: Dict[str, Dict[str, Any]] = {}

        # 1. Map Tables to Table Sections
        assigned_tables = set()
        for sec_cfg in self.sections_config:
            sid = sec_cfg["id"]
            if sec_cfg["type"] != "table":
                continue

            expected_fields = sec_cfg.get("fields", [])
            sec_name_keywords = SECTION_KEYWORDS.get(sid, [])

            best_match_table = None
            best_match_score = 0
            best_t_idx = -1

            for t_idx, t_entry in enumerate(tables_list):
                if t_idx in assigned_tables:
                    continue
                raw_table = t_entry["table"]
                if not raw_table or len(raw_table) < 2:
                    continue

                header = [str(c).strip().lower() for c in raw_table[0]]
                # Header keyword overlap score
                field_score = 0
                for ef in expected_fields:
                    ef_low = ef.lower()
                    if any(ef_low in h or h in ef_low for h in header):
                        field_score += 2

                # Name keyword score
                for kw in sec_name_keywords:
                    if any(kw in h for h in header):
                        field_score += 3

                if field_score > best_match_score:
                    best_match_score = field_score
                    best_match_table = raw_table
                    best_t_idx = t_idx

            if best_match_table and best_match_score >= 2:
                assigned_tables.add(best_t_idx)
                structured_rows = self._table_to_dicts(best_match_table, expected_fields)
                sections_data[sid] = {"type": "table", "content": None, "structured_data": structured_rows}

        # 2. Extract Text Sections (Scope 1.6, Intro 1.9, Objective 1.10, etc.)
        for sid in ["1.6", "1.9", "1.10", "1.11"]:
            cfg = self.sections_by_id.get(sid, {})
            keywords = SECTION_KEYWORDS.get(sid, [])
            extracted_text = self._extract_section_text(full_text, sid, keywords)
            if extracted_text:
                if cfg.get("type") == "flowchart":
                    sections_data[sid] = {"type": "flowchart", "content": extracted_text, "structured_data": None}
                else:
                    sections_data[sid] = {"type": "text", "content": extracted_text, "structured_data": None}

        # 3. For any remaining table sections that didn't match via strict header overlap,
        # assign remaining unassigned tables in sequential order
        remaining_table_secs = [
            s["id"] for s in self.sections_config
            if s["type"] == "table" and s["id"] not in sections_data
        ]
        unassigned_tables = [
            t["table"] for i, t in enumerate(tables_list)
            if i not in assigned_tables and len(t["table"]) >= 2
        ]

        for sid, tbl in zip(remaining_table_secs, unassigned_tables):
            exp_fields = self.sections_by_id[sid].get("fields", [])
            s_rows = self._table_to_dicts(tbl, exp_fields)
            sections_data[sid] = {"type": "table", "content": None, "structured_data": s_rows}

        return sections_data

    def _table_to_dicts(self, raw_table: List[List[str]], expected_fields: List[str]) -> List[Dict[str, Any]]:
        """Converts raw 2D list into list of dicts matching expected fields."""
        if not raw_table or len(raw_table) < 2:
            return []

        header = [str(c).strip() for c in raw_table[0]]
        rows = raw_table[1:]

        # Build column index mapping from table header to expected field
        col_map = {}
        for ef in expected_fields:
            ef_clean = re.sub(r'[^a-z0-9]', '', ef.lower())
            for c_idx, h in enumerate(header):
                h_clean = re.sub(r'[^a-z0-9]', '', h.lower())
                if ef_clean in h_clean or h_clean in ef_clean:
                    col_map[ef] = c_idx
                    break

        dict_rows = []
        for r in rows:
            if not any(r):
                continue
            row_dict = {}
            for ef_idx, ef in enumerate(expected_fields):
                if ef in col_map and col_map[ef] < len(r):
                    val = str(r[col_map[ef]]).strip()
                elif ef_idx < len(r):
                    val = str(r[ef_idx]).strip()
                else:
                    val = ""
                row_dict[ef] = val
            dict_rows.append(row_dict)

        return dict_rows

    def _extract_section_text(self, full_text: str, section_id: str, keywords: List[str]) -> str:
        """Finds paragraphs under section headings like '1.9 Introduction' or 'Introduction'."""
        lines = full_text.splitlines()
        capturing = False
        captured_lines = []

        # Patterns like: "1.9 Introduction", "1.9. Introduction", "Section 1.9", "Introduction:"
        header_patterns = [
            re.compile(rf'^\s*(?:section\s*)?{re.escape(section_id)}[\s\.:\t]+([^\n]+)', re.IGNORECASE),
        ]
        for kw in keywords:
            header_patterns.append(re.compile(rf'^\s*(?:{re.escape(section_id)})?[\s\.:\t]*{re.escape(kw)}[\s\.:\t]*$', re.IGNORECASE))

        # Stop pattern: another numbered section header like "1.10", "1.11", etc.
        stop_pattern = re.compile(r'^\s*(?:section\s*)?1\.\d+[\s\.:\t]+', re.IGNORECASE)

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if capturing and captured_lines and captured_lines[-1] != "":
                    captured_lines.append("")
                continue

            # Check if this line starts our target section
            if not capturing:
                for hp in header_patterns:
                    if hp.search(stripped):
                        capturing = True
                        break
                continue

            # If currently capturing, check if we hit the next section
            if capturing:
                if stop_pattern.match(stripped) and not any(hp.search(stripped) for hp in header_patterns):
                    break
                # Filter out table of contents lines
                if "....." in stripped or ". . ." in stripped:
                    continue
                captured_lines.append(stripped)

        res = "\n".join(captured_lines).strip()
        # Fallback keyword slice if regex didn't capture
        if not res or len(res.split()) < 5:
            for kw in keywords[:2]:
                idx = full_text.lower().find(kw.lower())
                if idx != -1:
                    snippet = full_text[idx:idx+1500]
                    # Cut off at next section header
                    parts = re.split(r'\n\s*1\.\d+', snippet)
                    if parts:
                        res = parts[0].replace(kw, "").strip().lstrip(":- \t\n")
                        break
        return res

document_importer = DocumentImporter()
