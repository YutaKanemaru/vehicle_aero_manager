"""Reset all error-status Runs back to pending."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("UPDATE runs SET status='pending', error_message=NULL WHERE status='error'"))
    conn.commit()
    print(f"Reset {result.rowcount} runs to pending")
