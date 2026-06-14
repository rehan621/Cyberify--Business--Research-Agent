"""
Stateful Memory — PostgreSQL Checkpointer
Task requirement: Memory must persist across sessions using PostgreSQL.
Saves: conversation history, research state, user preferences
"""

import os
import json
from datetime import datetime
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()


class PostgreSQLCheckpointer:
    """
    LangGraph-compatible checkpointer using PostgreSQL.
    Saves full research state per thread_id.
    """

    def __init__(self, db_session_factory):
        self.SessionLocal = db_session_factory

    def get(self, config: dict) -> dict | None:
        """Fetch the saved state of a specific thread."""
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return None

        db = self.SessionLocal()
        try:
            from ..database.models import Checkpoint
            record = db.query(Checkpoint).filter(
                Checkpoint.thread_id == thread_id
            ).first()

            if record and record.checkpoint_data:
                print(f"[Memory] ✅ Restored state for thread: {thread_id}")
                return record.checkpoint_data
            return None
        except Exception as e:
            print(f"[Memory] Get error: {e}")
            return None
        finally:
            db.close()

    def put(self, config: dict, checkpoint: dict, metadata: dict = None) -> dict:
        """Save the current state to PostgreSQL."""
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return config

        db = self.SessionLocal()
        try:
            from ..database.models import Checkpoint

            # Extract user ID from thread_id
            # Format: research_{id}_user_{user_id}
            user_id = 0
            parts = thread_id.split("_")
            if "user" in parts:
                idx = parts.index("user")
                user_id = int(parts[idx + 1]) if idx + 1 < len(parts) else 0

            record = db.query(Checkpoint).filter(
                Checkpoint.thread_id == thread_id
            ).first()

            if record:
                record.checkpoint_data = checkpoint
                record.updated_at = datetime.utcnow()
            else:
                record = Checkpoint(
                    thread_id=thread_id,
                    user_id=user_id,
                    checkpoint_data=checkpoint,
                )
                db.add(record)

            db.commit()
            print(f"[Memory] 💾 State saved for thread: {thread_id}")
        except Exception as e:
            print(f"[Memory] Put error: {e}")
            db.rollback()
        finally:
            db.close()

        return config

    def list(self, config: dict) -> list:
        """List the history of a specific thread."""
        return []


def get_user_memory(user_id: int) -> dict:
    """
    Fetch comprehensive memory for a user:
    - Previous research queries
    - Research results
    - Preferences
    """
    from ..database.connection import SessionLocal
    from ..database.models import ResearchHistory, ChatMessage

    db = SessionLocal()
    try:
        # Previous research
        research_history = db.query(ResearchHistory).filter(
            ResearchHistory.user_id == user_id,
            ResearchHistory.status == "completed"
        ).order_by(ResearchHistory.created_at.desc()).limit(10).all()

        # Recent chat messages
        chat_history = db.query(ChatMessage).filter(
            ChatMessage.user_id == user_id
        ).order_by(ChatMessage.created_at.desc()).limit(20).all()

        memory = {
            "previous_queries": [r.query for r in research_history],
            "research_summaries": [
                {
                    "id": r.id,
                    "query": r.query,
                    "confidence": r.confidence_score,
                    "date": r.created_at.isoformat() if r.created_at else None,
                }
                for r in research_history[:5]
            ],
            "chat_history": [
                {"role": m.role, "content": m.content[:200]}
                for m in reversed(chat_history[:10])
            ],
            "total_researches": len(research_history),
        }

        print(f"[Memory] Loaded {len(research_history)} past researches for user {user_id}")
        return memory

    except Exception as e:
        print(f"[Memory] Error loading user memory: {e}")
        return {}
    finally:
        db.close()


def save_chat_message(user_id: int, research_id: int | None, role: str, content: str):
    """Save a chat message to PostgreSQL."""
    from ..database.connection import SessionLocal
    from ..database.models import ChatMessage

    db = SessionLocal()
    try:
        msg = ChatMessage(
            user_id=user_id,
            research_id=research_id,
            role=role,
            content=content,
        )
        db.add(msg)
        db.commit()
    except Exception as e:
        print(f"[Memory] Chat save error: {e}")
        db.rollback()
    finally:
        db.close()