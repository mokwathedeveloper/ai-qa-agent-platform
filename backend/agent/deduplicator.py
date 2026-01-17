import hashlib
from sqlalchemy.orm import Session
from backend.database.models import Bug

def get_error_signature(test_name: str, error_message: str, traceback: str) -> str:
    """Creates a hash of the error context to identify duplicates."""
    # We strip whitespace to be robust
    raw = f"{test_name}|{error_message}|{traceback}".replace(" ", "")
    return hashlib.md5(raw.encode()).hexdigest()

def is_duplicate(db: Session, signature: str) -> bool:
    return db.query(Bug).filter(Bug.error_signature == signature).first() is not None
