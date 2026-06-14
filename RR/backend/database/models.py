from sqlalchemy import (
    Column, Integer, String, Boolean, Text,
    Float, ForeignKey, DateTime, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id               = Column(Integer, primary_key=True, index=True)
    email            = Column(String(255), unique=True, nullable=False, index=True)
    username         = Column(String(100), unique=True, nullable=False)
    hashed_password  = Column(Text, nullable=False)
    is_active        = Column(Boolean, default=True)
    created_at       = Column(DateTime, default=datetime.utcnow)

    workspaces       = relationship("Workspace", back_populates="owner", cascade="all, delete")
    research_history = relationship("ResearchHistory", back_populates="user", cascade="all, delete")
    documents        = relationship("Document", back_populates="user", cascade="all, delete")
    chat_messages    = relationship("ChatMessage", back_populates="user", cascade="all, delete")


class Workspace(Base):
    __tablename__ = "workspaces"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    name        = Column(String(255), nullable=False)
    description = Column(Text)
    created_at  = Column(DateTime, default=datetime.utcnow)

    owner     = relationship("User", back_populates="workspaces")
    documents = relationship("Document", back_populates="workspace")
    research  = relationship("ResearchHistory", back_populates="workspace")


class ResearchHistory(Base):
    __tablename__ = "research_history"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=False)
    workspace_id     = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    query            = Column(Text, nullable=False)
    status           = Column(String(50), default="pending")  # pending/running/completed/failed
    report           = Column(Text)
    sources          = Column(JSON)
    confidence_score = Column(Float)
    created_at       = Column(DateTime, default=datetime.utcnow)
    completed_at     = Column(DateTime)

    user      = relationship("User", back_populates="research_history")
    workspace = relationship("Workspace", back_populates="research")
    messages  = relationship("ChatMessage", back_populates="research")


class Document(Base):
    __tablename__ = "documents"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    workspace_id  = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    filename      = Column(String(255), nullable=False)
    file_type     = Column(String(50))
    file_path     = Column(Text)
    chroma_doc_id = Column(String(255))
    uploaded_at   = Column(DateTime, default=datetime.utcnow)

    user      = relationship("User", back_populates="documents")
    workspace = relationship("Workspace", back_populates="documents")


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    thread_id       = Column(String(255), primary_key=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    checkpoint_data = Column(JSON)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    research_id = Column(Integer, ForeignKey("research_history.id"), nullable=True)
    role        = Column(String(20), nullable=False)  # user / assistant
    content     = Column(Text, nullable=False)
    mode        = Column(String(20), default="general")  # general / research / documents
    created_at  = Column(DateTime, default=datetime.utcnow)

    user     = relationship("User", back_populates="chat_messages")
    research = relationship("ResearchHistory", back_populates="messages")