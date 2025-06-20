from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    company = Column(String(255))
    location = Column(String(255))
    salary = Column(String(255))
    description = Column(Text)
    source = Column(String(50))
    posted_at = Column(DateTime(timezone=True), nullable=True)
    scraped_at = Column(DateTime(timezone=True), default=datetime.utcnow)