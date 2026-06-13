from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import ResearchState
import json
import os


def verifier_agent(state: ResearchState) -> dict:
    """
    Verifier Agent — Verifies research findings for accuracy and confidence.
    Conditional Routing:
    - Confidence >= 0.7 → Reporter
    - Confidence < 0.7  → Researcher (retry, max 2 times)
    """
    from ..memory.progress_tracker import update_progress

    revision_count = state.get("revision_count", 0)

    update_progress(
        state["research_id"],
        agent="✅ Verifier Agent",
        step="Verifying research findings...",
        tool="Fact Checker",
        percent=70,
    )

    llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

    findings_text = "\n\n".join([
        f"Q: {f['question']}\nA: {f['summary']}"
        for f in state["raw_findings"]
    ])

    messages = [
        SystemMessage(content="""You are a senior fact-checking analyst and quality assurance expert at Cyberify Research Agent.

Your role is to critically evaluate research findings before they reach the final report.

Evaluation Criteria:
1. ACCURACY — Are claims supported by credible sources? Flag any unverified statistics
2. COMPLETENESS — Are there critical gaps or missing data points?
3. CONSISTENCY — Do findings contradict each other?
4. RECENCY — Is the data current (2023-2025)? Flag outdated information
5. SPECIFICITY — Are answers vague or data-rich? Vague answers need revision

Confidence Scoring Guide:
- 0.9 - 1.0: Excellent — all findings verified, data-rich, consistent
- 0.7 - 0.9: Good — minor gaps but overall reliable
- 0.5 - 0.7: Needs revision — significant gaps or unverified claims
- 0.0 - 0.5: Poor — major issues, must revise

Respond ONLY with this exact JSON structure:
{
  "verified_findings": [
    {
      "question": "exact sub-question",
      "summary": "verified and enhanced summary",
      "is_reliable": true,
      "note": "any specific concern or validation note"
    }
  ],
  "confidence_score": 0.85,
  "overall_assessment": "2-3 sentence quality assessment",
  "needs_revision": false,
  "revision_feedback": "specific actionable improvements needed (only if confidence < 0.7, else empty string)"
}"""),
        HumanMessage(content=f"Research Findings (Attempt {revision_count + 1}):\n\n{findings_text}")
    ]

    update_progress(
        state["research_id"],
        agent="✅ Verifier Agent",
        step="Validating sources...",
        tool="OpenAI GPT-4o-mini",
        percent=78,
    )

    response = llm.invoke(messages)

    try:
        text = response.content.strip().replace("```json", "").replace("```", "")
        result = json.loads(text)
        verified         = result.get("verified_findings", state["raw_findings"])
        confidence       = float(result.get("confidence_score", 0.7))
        needs_revision   = result.get("needs_revision", False)
        revision_feedback = result.get("revision_feedback", "")
    except Exception:
        verified         = state["raw_findings"]
        confidence       = 0.7
        needs_revision   = False
        revision_feedback = ""

    # Conditional routing logic
    max_revisions = 2
    should_revise = (
        confidence < 0.7
        and needs_revision
        and revision_count < max_revisions
    )

    if should_revise:
        update_progress(
            state["research_id"],
            agent="✅ Verifier Agent",
            step=f"⚠️ Confidence {confidence:.0%} — Revision #{revision_count + 1} requested!",
            tool=None,
            percent=72,
        )
        print(f"[Verifier] Low confidence {confidence:.0%} — requesting revision #{revision_count + 1}")
    else:
        update_progress(
            state["research_id"],
            agent="✅ Verifier Agent",
            step=f"✅ Verified — Confidence: {confidence:.0%}",
            tool=None,
            percent=85,
        )

    return {
        "verified_findings": verified,
        "confidence_score":  confidence,
        "needs_revision":    should_revise,
        "revision_feedback": revision_feedback if should_revise else "",
        "current_step":      "researcher" if should_revise else "reporter",
    }