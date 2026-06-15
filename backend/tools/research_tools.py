"""
Tool Calling Module
3 tools: Web Search (Tavily), Calculator, File Retrieval
LangChain tools format mein — agents directly call kar sakte hain.
"""

from langchain.tools import tool
from tavily import TavilyClient
import math
import os


# ── Tool 1: Web Search ────────────────────────────────────────────────────────

@tool
def web_search_tool(query: str) -> str:
    """
    Search the web for current information about any topic.
    Use this for market research, company analysis, news, and trends.
    """
    try:
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True,
        )
        results = response.get("results", [])
        if not results:
            return "No results found."

        output = []
        for r in results:
            output.append(f"Title: {r.get('title','')}\nURL: {r.get('url','')}\nContent: {r.get('content','')[:500]}")

        urls = [r.get("url", "") for r in results if r.get("url", "").startswith("http")]
        sources_section = "\nSOURCES:\n" + "\n".join(urls)

        return "\n\n---\n\n".join(output) + sources_section
    except Exception as e:
        return f"Search error: {e}"


# ── Tool 2: Calculator ────────────────────────────────────────────────────────

@tool
def calculator_tool(expression: str) -> str:
    """
    Perform mathematical calculations and financial computations.
    Examples:
    - "1500 * 0.15" → profit margin calculation
    - "sqrt(144)" → square root
    - "2500000 / 12" → monthly revenue
    - "((150 - 120) / 120) * 100" → percentage growth
    Supports: +, -, *, /, **, sqrt, log, sin, cos, tan, pi, e
    """
    try:
        # Safe math environment
        safe_env = {
            "sqrt":  math.sqrt,
            "log":   math.log,
            "log10": math.log10,
            "sin":   math.sin,
            "cos":   math.cos,
            "tan":   math.tan,
            "pi":    math.pi,
            "e":     math.e,
            "abs":   abs,
            "round": round,
            "pow":   pow,
        }
        result = eval(expression, {"__builtins__": {}}, safe_env)
        return f"Result: {result}"
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Calculation error: {e}"


# ── Tool 3: File Retrieval ────────────────────────────────────────────────────

@tool
def file_retrieval_tool(query: str, user_id: int = 0) -> str:
    """
    Search and retrieve relevant content from user's uploaded documents.
    Use this when user has uploaded PDFs, DOCX, or TXT files.
    Returns the most relevant chunks from uploaded documents.
    """
    try:
        from ..rag.rag_pipeline import search_documents
        results = search_documents(user_id=user_id, query=query, top_k=5)

        if not results:
            return "No relevant documents found. User may not have uploaded any documents."

        output = []
        for r in results:
            score = r.get("score", 0)
            output.append(
                f"[Document: {r.get('filename','')} | Relevance: {score:.0%}]\n{r.get('content','')[:600]}"
            )
        return "\n\n---\n\n".join(output)
    except Exception as e:
        return f"File retrieval error: {e}"


# ── Tool Registry ─────────────────────────────────────────────────────────────

ALL_TOOLS = [web_search_tool, calculator_tool, file_retrieval_tool]

TOOL_DESCRIPTIONS = {
    "web_search_tool":    "🔍 Web Search — Tavily se real-time information",
    "calculator_tool":    "🔢 Calculator — Mathematical & financial computations",
    "file_retrieval_tool": "📂 File Retrieval — Uploaded documents se search",
}