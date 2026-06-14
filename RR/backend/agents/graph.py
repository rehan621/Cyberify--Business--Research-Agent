from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import ResearchState
from .planner import planner_agent
from .researcher import researcher_agent
from .verifier import verifier_agent
from .reporter import reporter_agent


# ── Conditional Routing ───────────────────────────────────────────────────────

def route_after_verifier(state: ResearchState) -> str:
    """
    Conditional Routing:
    - needs_revision = True  → researcher (reflection loop)
    - needs_revision = False → reporter
    """
    if state.get("needs_revision", False):
        revision_count = state.get("revision_count", 0)
        print(f"[Router] ⚠️ Low confidence — Revision #{revision_count + 1} → Researcher")
        return "researcher"
    else:
        confidence = state.get("confidence_score", 0)
        print(f"[Router] ✅ Confidence {confidence:.0%} → Reporter")
        return "reporter"


# ── Build Graph ───────────────────────────────────────────────────────────────

def build_research_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("planner",    planner_agent)
    graph.add_node("researcher", researcher_agent)
    graph.add_node("verifier",   verifier_agent)
    graph.add_node("reporter",   reporter_agent)

    graph.set_entry_point("planner")

    graph.add_edge("planner",    "researcher")
    graph.add_edge("researcher", "verifier")

    graph.add_conditional_edges(
        "verifier",
        route_after_verifier,
        {
            "researcher": "researcher",
            "reporter":   "reporter",
        }
    )

    graph.add_edge("reporter", END)

    # MemorySaver — in-session memory
    memory = MemorySaver()
    print("[Graph] ✅ LangGraph compiled with MemorySaver + PostgreSQL persistence")
    return graph.compile(checkpointer=memory)


research_graph = build_research_graph()


def save_checkpoint_to_postgres(research_id: int, user_id: int, state: dict):
    """Save the final state to PostgreSQL for stateful persistent memory."""
    try:
        from ..database.connection import SessionLocal
        from ..database.models import Checkpoint
        from datetime import datetime

        db = SessionLocal()
        thread_id = f"research_{research_id}_user_{user_id}"

        # Extract only the key fields required for storage
        checkpoint_data = {
            "query":            state.get("query", ""),
            "research_plan":    state.get("research_plan", []),
            "confidence_score": state.get("confidence_score", 0),
            "revision_count":   state.get("revision_count", 0),
            "sources":          state.get("sources", [])[:10],
            "saved_at":         datetime.utcnow().isoformat(),
        }

        record = db.query(Checkpoint).filter(Checkpoint.thread_id == thread_id).first()
        if record:
            record.checkpoint_data = checkpoint_data
            record.updated_at      = datetime.utcnow()
        else:
            record = Checkpoint(
                thread_id=thread_id,
                user_id=user_id,
                checkpoint_data=checkpoint_data,
            )
            db.add(record)

        db.commit()
        print(f"[Memory] 💾 Checkpoint saved to PostgreSQL: {thread_id}")
        db.close()
    except Exception as e:
        print(f"[Memory] PostgreSQL save error: {e}")


async def run_research(query: str, user_id: int, research_id: int) -> dict:
    """Execute the research graph pipeline with memory configuration."""

    # Load previous user memory context
    try:
        from ..memory.checkpointer import get_user_memory
        user_memory = get_user_memory(user_id)
        prev_count  = len(user_memory.get("previous_queries", []))
        if prev_count:
            print(f"[Memory] Found {prev_count} previous queries for user {user_id}")
    except Exception:
        pass

    initial_state: ResearchState = {
        "query":             query,
        "user_id":           user_id,
        "research_id":       research_id,
        "research_plan":     [],
        "raw_findings":      [],
        "verified_findings": [],
        "confidence_score":  0.0,
        "revision_count":    0,
        "needs_revision":    False,
        "revision_feedback": None,
        "final_report":      "",
        "sources":           [],
        "current_step":      "planner",
        "error":             None,
    }

    config = {
        "configurable": {
            "thread_id": f"research_{research_id}_user_{user_id}"
        }
    }

    final_state = research_graph.invoke(initial_state, config=config)

    # Save checkpoint to PostgreSQL database
    save_checkpoint_to_postgres(research_id, user_id, final_state)

    return final_state