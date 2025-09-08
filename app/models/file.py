from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum

class FileVisibility(enum.Enum):
    PRIVATE = "private"
    DEPARTMENT = "department"
    PUBLIC = "public"

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    s3_key = Column(String, unique=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    visibility = Column(Enum(FileVisibility))
    department = Column(String, index=True)
    size = Column(Integer)
    downloads = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User")

    # PDF Metadata
    pages = Column(Integer)
    author = Column(String)
    title = Column(String)
    created_date = Column(DateTime)
    creator_tool = Column(String)

    # DOC/DOCX Metadata
    paragraphs = Column(Integer)
    tables = Column(Integer)
