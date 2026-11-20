import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from supabase import create_client
load_dotenv()

from models.schemas import ProcessNoteSchema, ProcessSectionSchema
from core.validation_engine import ValidationEngine

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
NOTE_ID = 55

def main():
    print(f"Connecting to Supabase and fetching note {NOTE_ID}...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    note_res = supabase.table("process_notes").select("*").eq("id", NOTE_ID).single().execute()
    note_data = note_res.data
    print(f"Found note: {note_data['process_name']} (v{note_data['version']})")

    sec_res = supabase.table("process_sections").select("*").eq("process_note_id", NOTE_ID).execute()
    print(f"Found {len(sec_res.data)} sections.")

    sections_payload = []
    # Sort sections in 1.1 to 1.22 order
    sorted_secs = sorted(sec_res.data, key=lambda x: [int(p) for p in x["section_id"].split(".")])
    for s in sorted_secs:
        sections_payload.append(ProcessSectionSchema(
            section_id=s["section_id"],
            content=s["content"],
            structured_data=s["structured_data"]
        ))

    payload = ProcessNoteSchema(
        process_name=note_data["process_name"],
        team=note_data["team"],
        version=note_data["version"],
        subject_matter_expert=note_data.get("subject_matter_expert"),
        process_owner=note_data.get("process_owner"),
        process_champion=note_data.get("process_champion"),
        process_reviewer=note_data.get("process_reviewer"),
        process_approver=note_data.get("process_approver"),
        effective_date=note_data.get("effective_date"),
        next_review_date=note_data.get("next_review_date"),
        sections=sections_payload
    )

    print("\nInitializing ValidationEngine and executing AI validation...")
    engine = ValidationEngine()
    result = engine.run_validation(payload)

    print("\n" + "="*70)
    print("AI VALIDATION OVERALL RESULT")
    print("="*70)
    print(f"Overall Score: {result.overall_score:.2f} / 100")
    print(f"Overall Status: {result.overall_status}")
    print(f"Sections Passed: {result.sections_passed}")
    print(f"Warnings: {result.warnings}")
    print(f"Sections Needing Revision: {result.sections_needing_revision}")
    print(f"Critical Issues: {result.critical_issues}")

    print("\n" + "="*70)
    print("SAVING VALIDATION RUN & FINDINGS TO SUPABASE...")
    print("="*70)

    # Insert validation_run
    vrun_res = supabase.table("validation_runs").insert({
        "process_note_id": NOTE_ID,
        "process_name": note_data["process_name"],
        "overall_score": float(result.overall_score),
        "status": result.overall_status,
        "model_used": os.getenv("LLM_MODEL", "gemini-3.5-flash"),
        "timestamp": datetime.utcnow().isoformat()
    }).execute()
    vrun_id = vrun_res.data[0]["id"]
    print(f"Saved ValidationRun with ID={vrun_id}")

    # Prepare findings
    findings_payload = []
    for sec_res in result.section_results:
        rec_lines = list(sec_res.recommendations)
        if sec_res.questions:
            rec_lines.append("\n**Clarification Questions for Process Owner:**")
            rec_lines.extend([f"- {q}" for q in sec_res.questions])

        findings_payload.append({
            "validation_id": vrun_id,
            "process_name": note_data["process_name"],
            "section_id": sec_res.section,
            "severity": sec_res.severity,
            "status": sec_res.status,
            "score": float(sec_res.score),
            "issue": "\n".join(sec_res.issues),
            "recommendation": "\n".join(rec_lines),
            "is_cross_section": 0
        })

    for cr in result.cross_section_issues:
        cr_rec = []
        if cr.get("questions"):
            cr_rec.append("**Clarification Questions for Process Owner:**")
            cr_rec.extend([f"- {q}" for q in cr.get("questions")])

        rel = cr.get("related_sections", [])
        label = f"Cross-Section ({' & '.join(rel)})" if rel else "Cross-Section Alignment"

        findings_payload.append({
            "validation_id": vrun_id,
            "process_name": note_data["process_name"],
            "section_id": label,
            "severity": cr.get("severity", "MEDIUM"),
            "status": "NEEDS_REVISION" if cr.get("severity") == "HIGH" else "WARNING",
            "score": 0.0 if cr.get("severity") == "HIGH" else 50.0,
            "issue": cr.get("issue", ""),
            "recommendation": "\n".join(cr_rec),
            "is_cross_section": 1
        })

    if findings_payload:
        supabase.table("validation_findings").insert(findings_payload).execute()
        print(f"Saved {len(findings_payload)} findings to Supabase.")

    # Save detailed summary to JSON for local analysis
    report_data = {
        "overall_score": result.overall_score,
        "overall_status": result.overall_status,
        "sections_passed": result.sections_passed,
        "warnings": result.warnings,
        "sections_needing_revision": result.sections_needing_revision,
        "critical_issues": result.critical_issues,
        "section_results": [
            {
                "section": s.section,
                "status": s.status,
                "score": s.score,
                "severity": s.severity,
                "issues": s.issues,
                "recommendations": s.recommendations,
                "questions": s.questions
            }
            for s in result.section_results
        ],
        "cross_section_issues": result.cross_section_issues
    }
    with open("scripts/validation_analysis_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print("Detailed report written to scripts/validation_analysis_report.json")

if __name__ == "__main__":
    main()
