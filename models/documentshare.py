from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from models.user import Base

class DocumentShare(Base):
    __tablename__ = "document_shares"
    id = Column(Integer, primary_key=True)
    shared_by_user_id = Column(Integer)
    shared_to_user_id = Column(Integer)
    document_path = Column(String)
    document_type = Column(String)
    shared_at = Column(DateTime, default=datetime.now)
    status = Column(String, default="active")