from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, default="PENDING")
    logs = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    bugs = relationship("Bug", back_populates="job")

class Bug(Base):
    __tablename__ = "bugs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id"))
    test_name = Column(String, index=True)
    summary = Column(String)
    steps = Column(Text)
    actual_result = Column(Text)
    expected_result = Column(Text)
    severity = Column(String)
    screenshot_path = Column(String, nullable=True)
    video_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="NEW")
    environment = Column(Text, nullable=True)
    
    job = relationship("Job", back_populates="bugs")
