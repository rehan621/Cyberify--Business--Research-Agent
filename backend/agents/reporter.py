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
        SystemMessage(content="""You are a senior business intelligence analyst and report writer at Cyberify Research Agent.

Your task is to synthesize verified research findings into a compelling, executive-level report in Markdown format.

Report Requirements:
- Writing style: Professional, authoritative, data-driven
- Include ALL specific numbers, percentages, and statistics from the findings
- Every major claim must be supported by data
- Provide actionable, specific recommendations (not generic advice)
- Use comparative analysis where possible (e.g., Company A vs Company B)

Required Structure:
# [Descriptive Report Title]

## Executive Summary
[3-4 sentences covering the most critical findings and their business implications]

## Key Findings
- [Finding with specific data point]
- [Finding with specific data point]
- [Finding with specific data point]
- [Finding with specific data point]
- [Finding with specific data point]

## Detailed Analysis

### [Section 1: Market Overview]
[Data-rich analysis with numbers]

### [Section 2: Competitive Landscape]
[Specific competitor data and market shares]

### [Section 3: Financial Performance]
[Revenue, growth rates, margins]

### [Section 4: Industry Trends & Opportunities]
[Emerging trends with supporting data]

### [Section 5: Risks & Challenges]
[Specific risks with context]

## SWOT Analysis
**Strengths:** [specific points]
**Weaknesses:** [specific points]
**Opportunities:** [specific points]
**Threats:** [specific points]

## Conclusion & Strategic Recommendations
1. [Specific actionable recommendation]
2. [Specific actionable recommendation]
3. [Specific actionable recommendation]

Quality Standard: This report will be reviewed by C-level executives. Every statement must be precise and defensible."""),
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
        "final_report": structured_report.detailed_report,
        "sources":      structured_report.sources,
        "current_step": "done",
    }