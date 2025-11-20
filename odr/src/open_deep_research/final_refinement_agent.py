"""
Final Refinement Agent (Stable Version)

This agent refines the final report after the main research process.
Flow:
detect_missing_info → conduct_refinement_search → rewrite_final_report → detect_missing_info → END
"""

import json
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from open_deep_research.configuration import Configuration
from open_deep_research.utils import get_all_tools, get_api_key_for_model
from open_deep_research.state import AgentState
from langchain.chat_models import init_chat_model

# -----------------------------------------------------
# CONFIG
# -----------------------------------------------------

configurable_model = init_chat_model(
    configurable_fields=("model", "max_tokens", "api_key")
)

MAX_REFINEMENT_LOOPS = 1

# -----------------------------------------------------
# 1. detect_missing_info
# -----------------------------------------------------

async def detect_missing_info(state: AgentState, config):
    """Check if the report is missing topics compared to the brief."""

    configurable = Configuration.from_runnable_config(config)

    brief = state.get("research_brief", "")
    report = state.get("final_report", "")
    loops = state.get("refinement_loops", 0)

    # 🔥 Loop limit check
    if loops >= MAX_REFINEMENT_LOOPS:
        msg = f"🛑 Reached maximum refinement loops ({MAX_REFINEMENT_LOOPS}). Stopping refinement."
        return Command(
            goto=END,
            update={"messages": [AIMessage(content=msg)]},
        )

    model = configurable_model.with_config({
        "model": configurable.research_model,
        "max_tokens": 4096,
        "api_key": get_api_key_for_model(configurable.research_model, config),
    })

    prompt = f"""
You MUST return ONLY **valid JSON**.
No explanation. No natural language. No markdown. No code fences.
If you output anything other than JSON, the system will fail.

Strict rules:
- JSON must contain EXACTLY the following keys:
  - "need_additional_search"
  - "missing_topics"
  - "comment"
- "need_additional_search" must be true or false (lowercase).
- "missing_topics" must be a JSON array of strings.
- "comment" must be a simple string.
- No trailing commas, no additional fields.

Example of valid output ONLY:
{{
  "need_additional_search": true,
  "missing_topics": ["example A", "example B"],
  "comment": "short explanation"
}}

Now evaluate the completeness of the final report.

<Brief>
{brief}

<Final Report>
{report}

Respond ONLY with the JSON. Nothing else.
    """

    response = await model.ainvoke([HumanMessage(content=prompt)])

    # 🔥 JSON parsing WITH safe exit
    try:
        result = json.loads(response.content)
    except Exception:
        return Command(
            goto=END,
            update={"messages": [
                AIMessage(content="❌ JSON parsing failed. Ending refinement.")]}
        )

    # 🔥 Missing topics found → continue loop
    if result.get("need_additional_search") and result.get("missing_topics"):
        topics = result["missing_topics"]
        msg = (
            f"⚠️ Missing topics found (loop {loops+1}/{MAX_REFINEMENT_LOOPS}): "
            f"{', '.join(topics)}"
        )

        return Command(
            goto="conduct_refinement_search",
            update={
                "refinement_topics": topics,
                "refinement_loops": loops + 1,     # 중요!!
                "messages": [AIMessage(content=msg)],
            },
        )

    # 🔥 No missing topics → END
    msg = f"✅ Report sufficiently covers all areas. {result.get('comment','')}"
    return Command(
        goto=END,
        update={"messages": [AIMessage(content=msg)]},
    )


# -----------------------------------------------------
# 2. conduct_refinement_search (Option 2 version)
# -----------------------------------------------------

async def conduct_refinement_search(state: AgentState, config):
    """
    Perform supplementary research on missing topics using a controlled 2-step process:

    1) LLM picks which tools to call (vectordb_search → tavily_search)
    2) This node executes the tool calls directly (no LangGraph tool loop)
    3) LLM writes final markdown summary based on executed tool results
    """

    configurable = Configuration.from_runnable_config(config)

    topics = state.get("refinement_topics", [])

    # 🔥 Load tools
    all_tools = await get_all_tools(config)

    # 🔥 Filter allowed tools: ONLY vectordb_search, tavily_search
    allowed_tool_names = {"vectordb_search", "tavily_search"}
    allowed_tools = {t.name: t for t in all_tools if t.name in allowed_tool_names}

    if not allowed_tools:
        return Command(
            goto="rewrite_final_report",
            update={
                "refinement_notes": "⚠️ No valid search tools (vectordb_search/tavily_search) available.",
                "messages": [AIMessage(content="⚠️ Skipped search — No allowed tools found.")],
            },
        )

    # ------------------------------
    # STEP 1: Ask LLM which tools to call
    # ------------------------------
    model = (
        configurable_model.bind_tools(list(allowed_tools.values()))
        .with_config({
            "model": configurable.research_model,
            "max_tokens": configurable.research_model_max_tokens,
            "api_key": get_api_key_for_model(configurable.research_model, config),
        })
    )

    topic_list = "\n".join(f"- {t}" for t in topics)

    first_prompt = f"""
    You are performing supplementary research.

    MUST RULES:
    - You MUST call vectordb_search first for each topic.
    - If the result is insufficient, THEN call tavily_search.
    - Do NOT answer directly.
    - Do NOT include your reasoning.
    - ONLY return tool_calls (ReAct style).

    Missing Topics:
    {topic_list}

    For each topic, decide the correct sequence of tool calls.

    Return ONLY tool_calls JSON. Do not produce normal content.
    """

    first_response = await model.ainvoke([HumanMessage(content=first_prompt)])
    tool_calls = first_response.tool_calls or []

    # ------------------------------
    # STEP 2: Execute tool calls directly in THIS node
    # ------------------------------
    tool_results = []

    for call in tool_calls:
        tool_name = call["name"]
        args = call.get("args", {})

        if tool_name not in allowed_tools:
            continue

        tool = allowed_tools[tool_name]

        try:
            # tool invocation is async for MCP tools
            output = await tool.invoke(args)
        except Exception as e:
            output = f"Tool execution error: {e}"

        tool_results.append({
            "tool": tool_name,
            "args": args,
            "output": output,
        })

    # ------------------------------
    # STEP 3: Summarize findings with LLM
    # ------------------------------
    summarizer_model = configurable_model.with_config({
        "model": configurable.final_report_model,
        "max_tokens": configurable.final_report_model_max_tokens,
        "api_key": get_api_key_for_model(configurable.final_report_model, config),
    })

    summary_prompt = f"""
You are a summarization assistant.

Based SOLELY on the tool results below, 
write the supplementary research findings in clean markdown format:

{json.dumps(tool_results, indent=2)}

Format EXACTLY like:

# Supplementary Findings
## Topic A
<Clean factual summary based only on TOOL OUTPUTS>

## Topic B
<summary>

Do NOT invent information. 
Do NOT hallucinate facts not found in the tool results.
"""

    summary_response = await summarizer_model.ainvoke([HumanMessage(content=summary_prompt)])
    summary_md = summary_response.content

    # ------------------------------
    # Return summary for next node
    # ------------------------------
    return Command(
        goto="rewrite_final_report",
        update={
            "refinement_notes": summary_md,
            "messages": [AIMessage(content=f"🔍 Supplementary research completed via tool execution for: {', '.join(topics)}")],
        },
    )


# -----------------------------------------------------
# 3. rewrite_final_report
# -----------------------------------------------------

async def rewrite_final_report(state: AgentState, config):
    """Rewrite the final report by integrating supplementary findings correctly."""

    configurable = Configuration.from_runnable_config(config)

    brief = state.get("research_brief", "")
    original_report = state.get("final_report", "")
    notes = state.get("refinement_notes", "")
    loops = state.get("refinement_loops", 0)

    model = configurable_model.with_config({
        "model": configurable.final_report_model,
        "max_tokens": configurable.final_report_model_max_tokens,
        "api_key": get_api_key_for_model(configurable.final_report_model, config),
    })

    # ------------------------------
    # 🔥 강제 통합 프롬프트
    # ------------------------------
    prompt = f"""
You are an expert technical editor.
You MUST revise the final report using the NEW supplementary findings.

<Strict Integration Rules>
1. Fully integrate the supplementary findings into the correct sections.
2. DO NOT append the findings as a new separate section.
3. Merge content into the most relevant sections based on semantics.
4. Remove duplicated sentences, paragraphs, or repeated facts.
5. Preserve the original structure unless improvements are necessary.
6. Maintain a consistent tone, formatting, and markdown hierarchy.
7. Ensure the revised report fully satisfies the research brief.
8. If new findings contradict old content, prioritize the new findings.
9. DO NOT include reasoning or explanation in the output.
10. Output ONLY the final rewritten report in markdown.

<Research Brief>
{brief}

<Original Report>
{original_report}

<Supplementary Findings>
{notes}

Return ONLY the improved report in markdown.
"""

    response = await model.ainvoke([HumanMessage(content=prompt)])

    msg = (
        f"🪄 Report refined (loop {loops}/{MAX_REFINEMENT_LOOPS}). "
        f"Remaining loops: {MAX_REFINEMENT_LOOPS - loops}"
    )

    return Command(
        goto="detect_missing_info",
        update={
            "final_report": response.content,
            "refinement_loops": loops,
            "messages": [AIMessage(content=msg)],
        },
    )

# -----------------------------------------------------
# 4. Subgraph
# -----------------------------------------------------

final_refinement_builder = StateGraph(AgentState, config_schema=Configuration)

final_refinement_builder.add_node("detect_missing_info", detect_missing_info)
final_refinement_builder.add_node("conduct_refinement_search", conduct_refinement_search)
final_refinement_builder.add_node("rewrite_final_report", rewrite_final_report)

final_refinement_builder.add_edge(START, "detect_missing_info")
final_refinement_builder.add_edge("detect_missing_info", END)

final_refinement_subgraph = final_refinement_builder.compile()

__all__ = ["final_refinement_subgraph"]

