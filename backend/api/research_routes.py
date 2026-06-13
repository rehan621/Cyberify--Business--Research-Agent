from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import asyncio

from ..database.connection import get_db, SessionLocal
from ..database.models import ResearchHistory, Workspace, User
from ..auth.jwt_handler import get_current_user

router = APIRouter(prefix="/api/research", tags=["Research"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    query: str
    workspace_id: Optional[int] = None

class ResearchResponse(BaseModel):
    id: int
    query: str
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

class ResearchDetailResponse(BaseModel):
    id: int
    query: str
    status: str
    report: Optional[str]
    sources: Optional[list]
    confidence_score: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]
    class Config:
        from_attributes = True


# ── Background Task ───────────────────────────────────────────────────────────

def run_research_task(research_id: int, query: str, user_id: int):
    db = SessionLocal()
    try:
        from ..memory.progress_tracker import init_progress, complete_progress, fail_progress

        record = db.query(ResearchHistory).filter(ResearchHistory.id == research_id).first()
        if not record:
            return

        # Progress init
        init_progress(research_id)
        record.status = "running"
        db.commit()

        # Real agents
        from ..agents.graph import run_research
        result = asyncio.run(run_research(query, user_id, research_id))

        record.report           = result.get("final_report", "No report generated.")
        record.sources          = result.get("sources", [])
        record.confidence_score = result.get("confidence_score", 0.0)
        record.status           = "completed"
        record.completed_at     = datetime.utcnow()
        db.commit()

        complete_progress(research_id)
        print(f"[Research #{research_id}] Completed ✅")

    except Exception as e:
        print(f"[Research #{research_id}] Failed ❌ — {e}")
        try:
            from ..memory.progress_tracker import fail_progress
            fail_progress(research_id, str(e))
        except:
            pass
        record = db.query(ResearchHistory).filter(ResearchHistory.id == research_id).first()
        if record:
            record.status = "failed"
            db.commit()
    finally:
        db.close()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/start", response_model=ResearchResponse, status_code=201)
def start_research(
    data: ResearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.workspace_id:
        ws = db.query(Workspace).filter(
            Workspace.id == data.workspace_id,
            Workspace.user_id == current_user.id
        ).first()
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")

    record = ResearchHistory(
        user_id=current_user.id,
        workspace_id=data.workspace_id,
        query=data.query,
        status="pending",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    background_tasks.add_task(
        run_research_task,
        research_id=record.id,
        query=data.query,
        user_id=current_user.id,
    )
    return record


@router.get("/progress/{research_id}")
def get_live_progress(
    research_id: int,
    current_user: User = Depends(get_current_user),
):
    """Live agent progress fetch karo."""
    from ..memory.progress_tracker import get_progress
    progress = get_progress(research_id)
    if not progress:
        return {
            "status": "unknown", "percent": 0,
            "current_agent": "Waiting...",
            "current_step": "",
            "current_tool": None,
            "logs": []
        }
    return progress


@router.get("/status/{research_id}", response_model=ResearchDetailResponse)
def get_research_status(
    research_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(ResearchHistory).filter(
        ResearchHistory.id == research_id,
        ResearchHistory.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Research not found")
    return record


@router.get("/history", response_model=List[ResearchDetailResponse])
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(ResearchHistory)
        .filter(ResearchHistory.user_id == current_user.id)
        .order_by(ResearchHistory.created_at.desc())
        .all()
    )


@router.delete("/{research_id}", status_code=204)
def delete_research(
    research_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(ResearchHistory).filter(
        ResearchHistory.id == research_id,
        ResearchHistory.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Research not found")
    db.delete(record)
    db.commit()


# ── Chat Message Save ─────────────────────────────────────────────────────────

class ChatMessageRequest(BaseModel):
    role:        str
    content:     str
    research_id: Optional[int] = None
    mode:        str = "general"

@router.post("/chat/save", status_code=201)
def save_chat(
    data: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save chat message to PostgreSQL with mode tracking."""
    from ..database.models import ChatMessage
    msg = ChatMessage(
        user_id=current_user.id,
        research_id=data.research_id,
        role=data.role,
        content=data.content,
        mode=data.mode,
    )
    db.add(msg)
    db.commit()
    return {"status": "saved"}


# ── Chat History Load ─────────────────────────────────────────────────────────

@router.get("/chat/history")
def get_chat_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Load previous chat messages from PostgreSQL."""
    from ..database.models import ChatMessage
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "role":        m.role,
            "content":     m.content,
            "research_id": m.research_id,
            "mode":        m.mode or "general",
            "created_at":  m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]


# ── Clear Chat History ────────────────────────────────────────────────────────

@router.delete("/chat/clear", status_code=204)
def clear_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete all chat messages for current user from PostgreSQL."""
    from ..database.models import ChatMessage
    db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).delete()
    db.commit()


# ── Clear Current Mode Chat ───────────────────────────────────────────────────

@router.delete("/chat/clear-mode", status_code=204)
def clear_mode_chat(
    research_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete chat messages for specific research or general chat from PostgreSQL."""
    from ..database.models import ChatMessage
    query = db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id)

    if research_id:
        query = query.filter(ChatMessage.research_id == research_id)
    else:
        query = query.filter(ChatMessage.research_id == None)

    query.delete()
    db.commit()


# ── Add mode column migration ─────────────────────────────────────────────────
@router.post("/chat/migrate", status_code=200)
def migrate_chat_mode(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add mode column to chat_messages if not exists."""
    try:
        db.execute(__import__('sqlalchemy').text(
            "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS mode VARCHAR(20) DEFAULT 'general'"
        ))
        db.commit()
        return {"status": "migrated"}
    except Exception as e:
        return {"status": "already exists"}