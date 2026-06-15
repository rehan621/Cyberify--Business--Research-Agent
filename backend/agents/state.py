from typing import TypedDict, List, Optional, Annotated
import operator


class ResearchState(TypedDict):
    """Shared state that flows through all agents in the graph."""

    # Input
    query:        str
    user_id:      int
    research_id:  int

    # Planner output
    research_plan: List[str]

    # Researcher output
    raw_findings: Annotated[List[dict], operator.add]

    # Verifier output
    verified_findings: List[dict]
    confidence_score:  float

    # Reflection loop control
    revision_count:    int        # kitni baar researcher ne retry kiya
    needs_revision:    bool       # verifier ne revision request ki hai
    revision_feedback: Optional[str]  # verifier ka feedback

    # Reporter output
    final_report: str
    sources:      Annotated[List[str], operator.add]

    # Control flow
    current_step: str
    error:        Optional[str]