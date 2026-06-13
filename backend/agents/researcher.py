from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from .state import ResearchState
import os
 
def researcher_agent(state: ResearchState) -> dict:
    """
    Researcher Agent with Tool Calling + Reflection Loop support.
    Executes targeted research refinement if the verifier requests a revision.
    """
    from ..memory.progress_tracker import update_progress
    from ..tools.research_tools import web_search_tool, calculator_tool, file_retrieval_tool

    revision_count   = state.get("revision_count", 0)
    needs_revision   = state.get("needs_revision", False)
    revision_feedback = state.get("revision_feedback", "")

    if needs_revision and revision_feedback:
        update_progress(
            state["research_id"],
            agent="🔍 Researcher Agent",
            step=f"🔄 Revision #{revision_count + 1} — Improving research...",
            tool=None,
            percent=30,
        )
        print(f"[Researcher] Revision #{revision_count + 1}: {revision_feedback}")
    else:
        update_progress(
            state["research_id"],
            agent="🔍 Researcher Agent",
            step="Research shuru ho rahi hai...",
            tool=None,
            percent=30,
        )

    tools     = [web_search_tool, calculator_tool, file_retrieval_tool]
    llm       = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY")).bind_tools(tools)
    llm_plain = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

    tool_map = {
        "web_search_tool":     web_search_tool,
        "calculator_tool":     calculator_tool,
        "file_retrieval_tool": file_retrieval_tool,
    }

    all_findings = []
    total = len(state["research_plan"])

    for i, sub_question in enumerate(state["research_plan"]):
        pct = 30 + int((i / total) * 35)

        update_progress(
            state["research_id"],
            agent="🔍 Researcher Agent",
            step=f"{'🔄 Re-researching' if needs_revision else 'Researching'}: {sub_question[:45]}...",
            tool="Selecting tool...",
            percent=pct,
        )

        # Revision feedback system prompt mein include karo
        revision_note = ""
        if needs_revision and revision_feedback:
            revision_note = f"\n\nIMPORTANT - Previous attempt was insufficient. Improve based on this feedback:\n{revision_feedback}"

        messages = [
            SystemMessage(content=f"""You are a senior business research analyst at Cyberify Research Agent with access to powerful tools.

Your mission is to gather comprehensive, data-rich intelligence on the given research question.

Tool Usage Strategy:
- web_search_tool: ALWAYS use first — search for latest statistics, news, and market data (2023-2025)
- calculator_tool: Use when you need to calculate growth rates, market share percentages, revenue comparisons, or any financial ratios
- file_retrieval_tool: ALWAYS check user's uploaded documents (user_id={state['user_id']}) — they may contain proprietary data

Research Standards:
- Prioritize recent data (2024-2025 preferred)
- Include specific numbers, percentages, and statistics whenever possible
- Cite the source context for key data points
- If one search is insufficient, search again with refined keywords
- Cross-reference data from multiple sources for accuracy

{revision_note}

Deliver thorough, evidence-based findings that a business executive would find actionable."""),
            HumanMessage(content=sub_question),
        ]

        tool_results = []
        sources      = []
        tools_used   = []

        for _ in range(5):
            response = llm.invoke(messages)

            if not response.tool_calls:
                messages.append(response)
                break

            messages.append(response)

            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"].copy()

                update_progress(
                    state["research_id"],
                    agent="🔍 Researcher Agent",
                    step=f"Tool executing...",
                    tool=f"{'🔍' if 'search' in tool_name else '🔢' if 'calc' in tool_name else '📂'} {tool_name}",
                    percent=pct + 5,
                )

                if tool_name == "file_retrieval_tool":
                    tool_args["user_id"] = state["user_id"]

                try:
                    result     = tool_map[tool_name].invoke(tool_args)
                    result_str = str(result)[:1500]
                except Exception as e:
                    result_str = f"Tool error: {e}"

                messages.append(ToolMessage(content=result_str, tool_call_id=tc["id"]))
                tool_results.append({"tool": tool_name, "result": result_str})
                tools_used.append(tool_name)

                if tool_name == "web_search_tool":
                    for line in result_str.split("\n"):
                        if line.startswith("URL:"):
                            url = line.replace("URL:", "").strip()
                            if url and url not in sources:
                                sources.append(url)

        # Summary
        combined = "\n\n".join([f"[{tr['tool']}]: {tr['result']}" for tr in tool_results])
        if combined:
            summary_resp = llm_plain.invoke([
                SystemMessage(content="Synthesize tool results into comprehensive research. Include specific data, numbers, statistics."),
                HumanMessage(content=f"Question: {sub_question}\n\nResults:\n{combined[:3000]}"),
            ])
            summary = summary_resp.content
        else:
            last = messages[-1]
            summary = last.content if hasattr(last, 'content') and last.content else "No data found."

        all_findings.append({
            "question":   sub_question,
            "summary":    summary,
            "sources":    sources,
            "tools_used": tools_used,
            "rag_used":   "file_retrieval_tool" in tools_used,
        })

        update_progress(
            state["research_id"],
            agent="🔍 Researcher Agent",
            step=f"✅ Finding {i+1}/{total} complete",
            tool=None,
            percent=pct + 8,
        )

    update_progress(
        state["research_id"],
        agent="🔍 Researcher Agent",
        step=f"{len(all_findings)} findings collected ✅",
        tool=None,
        percent=65,
    )

    return {
        "raw_findings":   all_findings,
        "revision_count": revision_count + (1 if needs_revision else 0),
        "needs_revision": False,
        "current_step":   "verifier",
    }