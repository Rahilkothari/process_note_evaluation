import os
import sys
import json
import yaml

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from models.database import SessionLocal, ProcessSection
from sqlalchemy.orm.attributes import flag_modified

def normalize_key(k):
    return str(k).lower().replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace(".", "")

def fix_keys():
    db = SessionLocal()
    with open("config/sections.yaml", "r") as f:
        sections_config = yaml.safe_load(f).get("sections", [])
        
    config_map = {s["id"]: s.get("fields", []) for s in sections_config}
    
    sections = db.query(ProcessSection).all()
    updated = 0
    for sec in sections:
        if sec.structured_data and sec.section_id in config_map:
            fields = config_map[sec.section_id]
            norm_fields = {normalize_key(f): f for f in fields}
            
            new_data = []
            changed = False
            for row in sec.structured_data:
                new_row = {}
                for k, v in row.items():
                    norm_k = normalize_key(k)
                    if norm_k in norm_fields and norm_fields[norm_k] != k:
                        new_row[norm_fields[norm_k]] = v
                        changed = True
                    elif k in fields:
                        new_row[k] = v
                    elif norm_k == "subprocessname":
                        # We dropped Sub-Process Name, so ignore it and flag changed
                        changed = True
                    else:
                        new_row[k] = v
                new_data.append(new_row)
                
            if changed:
                sec.structured_data = new_data
                flag_modified(sec, "structured_data")
                updated += 1
                
    if updated > 0:
        db.commit()
    print(f"Updated {updated} sections.")

if __name__ == '__main__':
    fix_keys()
