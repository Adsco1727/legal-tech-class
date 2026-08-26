import json
import os
from pathlib import Path

from dpo_system.src.ooma_adapter import seed_ooma_contacts_to_db

base = Path(os.environ.get("TEMP", "."))
csv_path = base / "ooma_smoke_test.csv"
db_path = base / "ooma_smoke_test.db"

csv_path.write_text(
    "ID,Name,Email,Phone,Consent,DNC\n"
    "ooma-1,Acme Legal,ops@example.com,5550101234,1,0\n"
    "ooma-2,Do Not Call Co,noreply@example.com,5550109999,1,1\n"
    "ooma-3,Unverified Contact,hello@example.com,5550103333,0,0\n",
    encoding="utf-8",
)

result = seed_ooma_contacts_to_db(str(csv_path), str(db_path), operator_id="operator:test")
print(json.dumps(result, indent=2, default=str))
