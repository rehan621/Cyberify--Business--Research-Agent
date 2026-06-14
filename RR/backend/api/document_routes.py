import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from ..database.connection import get_db
from ..database.models import Document, User
from ..auth.jwt_handler import get_current_user
from ..rag.rag_pipeline import add_document_to_chroma, delete_document_from_chroma

router = APIRouter(prefix="/api/documents", tags=["Documents"])

# Upload folder
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = {"pdf", "docx", "txt"}


# ── Schemas ───────────────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    workspace_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a document asset and index its content into ChromaDB vector space.
    Enforces isolated storage mapping using workspace and user IDs.
    """

    # File type check
    ext = file.filename.split(".")[-1].lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Only {', '.join(ALLOWED_TYPES)} files are allowed."
        )

    # Save file locally
    safe_name  = f"user{current_user.id}_{int(datetime.utcnow().timestamp())}_{file.filename}"
    file_path  = os.path.join(UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Create local database record
    doc = Document(
        user_id=current_user.id,
        workspace_id=workspace_id,
        filename=file.filename,
        file_type=ext,
        file_path=file_path,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Index text chunks into ChromaDB
    try:
        chroma_id = add_document_to_chroma(
            user_id=current_user.id,
            doc_id=doc.id,
            file_path=file_path,
            file_type=ext,
            filename=file.filename,
        )
        doc.chroma_doc_id = chroma_id
        db.commit()
        print(f"[Upload] {file.filename} indexed ✅")
    except Exception as e:
        print(f"[Upload] ChromaDB indexing failed: {e}")

    return doc


@router.get("/", response_model=List[DocumentResponse])
def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all document records belonging exclusively to the authenticated user."""
    return (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )


@router.delete("/{doc_id}", status_code=204)
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Purge a document from local storage, database persistence, and vector database indices."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id,
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete chunks from ChromaDB
    delete_document_from_chroma(current_user.id, doc_id)

    # Delete local structural file asset
    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()


# ── Document Search (For Chat Context) ────────────────────────────────────────

class SearchRequest(BaseModel):
    query:   str
    user_id: int
    top_k:   int = 5

class SearchResult(BaseModel):
    filename: str
    content:  str
    score:    float

class SearchResponse(BaseModel):
    results: List[SearchResult]


@router.post("/search", response_model=SearchResponse)
def search_documents_api(
    data: SearchRequest,
    current_user: User = Depends(get_current_user),
):
    """Perform a vector similarity search across a user's isolated documents for chat context."""
    from ..rag.rag_pipeline import search_documents
    results = search_documents(
        user_id=current_user.id,
        query=data.query,
        top_k=data.top_k,
    )
    return SearchResponse(results=[
        SearchResult(
            filename=r.get("filename", ""),
            content=r.get("content", ""),
            score=r.get("score", 0.0),
        )
        for r in results
    ])