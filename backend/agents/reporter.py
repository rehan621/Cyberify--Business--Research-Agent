from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import ResearchState
from .schemas import FinalReport
from datetime import datetime
import os


def reporter_agent(state: ResearchState) -> dict:
    """Reporter Agent — Generates the final report with Pydantic structured output."""

    from ..memory.progress_tracker import update_progress, complete_progress

    update_progress(
        state["research_id"],
        agent="📝 Reporter Agent",
        step="Generating report draft...",
        tool="OpenAI GPT-4o-mini",
        percent=90,
    )

    llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

    findings_text = "\n\n".join([
        f"**{f.get('question','')}**\n{f.get('summary','')}"
        for f in state["verified_findings"]
    ])

    # All sources + tools collect karo
    all_sources = []
    all_tools   = set()
    for f in state.get("raw_findings", []):
        for src in f.get("sources", []):
            if src and src not in all_sources:
                all_sources.append(src)
        for t in f.get("tools_used", []):
            all_tools.add(t)

    update_progress(
        state["research_id"],
        agent="📝 Reporter Agent",
        step="Generating professional research report...",
        tool="OpenAI GPT-4o-mini",
        percent=93,
    )

    messages = [
        SystemMessage(content="""You are a professional business research analyst.
Write a comprehensive, well-structured research report in Markdown format.

Structure:
# [Report Title]

## Executive Summary
[2-3 sentences overview]

## Key Findings
- Finding 1
- Finding 2
- Finding 3

## Detailed Analysis
[Comprehensive analysis with data]

## Conclusion & Recommendations
[Actionable recommendations]

Be professional, data-driven, and include specific numbers/statistics where available."""),
        HumanMessage(content=f"""
Original Query: {state['query']}
Confidence Score: {state['confidence_score']:.0%}
Tools Used: {', '.join(all_tools)}

Research Findings:
{findings_text}
""")
    ]

    response = llm.invoke(messages)
    report_text = response.content

    # Structured output banao
    key_findings = []
    for line in report_text.split("\n"):
        if line.strip().startswith("- ") and len(key_findings) < 6:
            key_findings.append(line.strip()[2:])

    # Title extract karo
    title = state["query"][:60]
    for line in report_text.split("\n"):
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # Pydantic model banao
    structured_report = FinalReport(
        title=title,
        query=state["query"],
        executive_summary=report_text[:500],
        key_findings=key_findings if key_findings else ["See detailed report below"],
        detailed_report=report_text,
        sources=all_sources,
        confidence_score=state["confidence_score"],
        tools_used=list(all_tools),
        generated_at=datetime.utcnow(),
        word_count=len(report_text.split()),
    )

    update_progress(
        state["research_id"],
        agent="📝 Reporter Agent",
        step=f"Report complete — {structured_report.word_count} words ✅",
        tool=None,
        percent=98,
    )

    complete_progress(state["research_id"])

    return {
        "final_report":     structured_report.detailed_report,
        "sources":          structured_report.sources,
        "confidence_score": structured_report.confidence_score,
        "current_step":     "done",
    }