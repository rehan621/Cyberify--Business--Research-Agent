"""
Pydantic Structured Output Models
Task requirement: No plain text outputs — proper structured models required.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ResearchFinding(BaseModel):
    """Single research finding from an agent."""
    question:   str          = Field(description="Sub-question that was researched")
    summary:    str          = Field(description="Summarized answer with key data points")
    sources:    List[str]    = Field(default=[], description="Source URLs")
    tools_used: List[str]    = Field(default=[], description="Tools used for this finding")
    rag_used:   bool         = Field(default=False, description="Were uploaded documents used?")
    is_reliable: bool        = Field(default=True, description="Verified by verifier agent")
    note:       Optional[str] = Field(default=None, description="Verifier note")


class ResearchPlan(BaseModel):
    """Planner agent output."""
    original_query:  str       = Field(description="Original user query")
    sub_questions:   List[str] = Field(description="Broken down sub-questions")
    estimated_tools: List[str] = Field(default=[], description="Tools that will likely be needed")


class VerificationResult(BaseModel):
    """Verifier agent structured output."""
    verified_findings:   List[ResearchFinding] = Field(description="All verified findings")
    confidence_score:    float                 = Field(ge=0.0, le=1.0, description="Overall confidence 0-1")
    overall_assessment:  str                   = Field(description="Summary of verification")
    contradictions_found: bool                 = Field(default=False)
    total_sources:       int                   = Field(default=0)


class FinalReport(BaseModel):
    """Reporter agent final structured output."""
    title:            str            = Field(description="Report title")
    query:            str            = Field(description="Original research query")
    executive_summary: str           = Field(description="Brief executive summary")
    key_findings:     List[str]      = Field(description="Bullet point key findings")
    detailed_report:  str            = Field(description="Full markdown report")
    sources:          List[str]      = Field(default=[], description="All sources")
    confidence_score: float          = Field(ge=0.0, le=1.0)
    tools_used:       List[str]      = Field(default=[], description="All tools used")
    generated_at:     datetime       = Field(default_factory=datetime.utcnow)
    word_count:       int            = Field(default=0)


class ResearchStartRequest(BaseModel):
    """API request for starting research."""
    query:        str           = Field(min_length=10, description="Research query")
    workspace_id: Optional[int] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Analyze Tesla's competitors in European EV market",
                "workspace_id": None
            }
        }


class ResearchStatusResponse(BaseModel):
    """API response for research status."""
    id:               int
    query:            str
    status:           str
    report:           Optional[str]   = None
    sources:          Optional[list]  = None
    confidence_score: Optional[float] = None
    created_at:       datetime
    completed_at:     Optional[datetime] = None

    class Config:
        from_attributes = True


class ProgressResponse(BaseModel):
    """Live progress API response."""
    status:        str
    percent:       int
    current_agent: str
    current_step:  str
    current_tool:  Optional[str] = None
    logs:          List[str]     = []