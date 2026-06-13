from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import ResearchState
import json
import os


def planner_agent(state: ResearchState) -> dict:
    """Planner Agent — breaks down the main query into specific sub-questions.."""

    # Progress update
    from ..memory.progress_tracker import update_progress
    update_progress(
        state["research_id"],
        agent="🧠 Planner Agent",
        step="Query analyzing...",
        tool="Query Analyzer",
        percent=10,
    )

    print(f"[Planner] Planning research for: {state['query']}")

    llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

    messages = [
        SystemMessage(content="""You are an expert business research strategist working for Cyberify Research Agent.

Your job is to analyze the user's research query and decompose it into 3-5 highly specific, actionable sub-questions that will guide a thorough investigation.

Guidelines:
- Each sub-question must target a distinct aspect (market size, competitors, financials, trends, risks)
- Questions must be specific enough to yield data-rich answers via web search
- Prioritize questions that will uncover quantitative data (numbers, percentages, market share)
- Order questions logically: context first, then specifics, then analysis
- Avoid vague or overlapping questions

Respond ONLY with a valid JSON array of strings. No explanation, no markdown, no extra text.

Example output:
["What is the current market size and projected growth rate of X industry?", "Who are the top 5 competitors in X market and what are their market shares?", "What were the revenue and profit figures for key players in X in 2023-2024?", "What are the emerging trends and technologies disrupting X industry?", "What are the major risks and regulatory challenges facing X market?"]
"""),
        HumanMessage(content=f"Research query: {state['query']}")
    ]

    update_progress(
        state["research_id"],
        agent="🧠 Planner Agent",
        step="Research plan creating...",
        tool="OpenAI GPT-4o-mini",
        percent=20,
    )

    response = llm.invoke(messages)

    try:
        text = response.content.strip().replace("```json", "").replace("```", "")
        plan = json.loads(text)
    except Exception:
        plan = [state["query"]]

    update_progress(
        state["research_id"],
        agent="🧠 Planner Agent",
        step=f"Plan ready — {len(plan)} sub-questions",
        tool=None,
        percent=25,
    )

    print(f"[Planner] Created {len(plan)} sub-questions")
    return {"research_plan": plan, "current_step": "researcher"}