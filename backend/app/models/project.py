import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, JSON, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=True)
    company_description = Column(String, nullable=True)
    industry = Column(String(255), nullable=True)
    products = Column(JSON, default=list)
    target_market = Column(String, nullable=True)
    competitors = Column(JSON, default=list)
    research_data = Column(JSON, default=dict)
    strategy_notes = Column(JSON, default=dict)
    status = Column(String(50), default="gathering")  # gathering, researching, strategizing, complete
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="project")
