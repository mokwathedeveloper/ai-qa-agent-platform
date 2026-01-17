from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Bug(Base):
    __tablename__ = "bugs"
    
    id = Column(Integer, primary_key=True, index=True)
    test_name = Column(String, index=True)
    summary = Column(String)
    steps = Column(Text)
    actual_result = Column(Text)
    expected_result = Column(Text)
    error_signature = Column(String, index=True) # Hash of traceback/error for dup detection
    severity = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="NEW") # NEW, DUPLICATE, SUBMITTED
