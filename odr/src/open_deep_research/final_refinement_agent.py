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

MAX_REFINEMENT_LOOPS = 3

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
    You must return **ONLY valid JSON**.
    No natural language. No prefix. No suffix. No code fences.

    Strictly output a JSON object with exactly these keys:

    {{
    "need_additional_search": boolean,
    "missing_topics": array of strings,
    "comment": string
    }}

    Now evaluate:

    <Brief>
    {brief}

    <Final Report>
    {report}

    ONLY OUTPUT THE JSON. DO NOT SAY ANYTHING ELSE.
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
# 2. conduct_refinement_search
# -----------------------------------------------------

async def conduct_refinement_search(state: AgentState, config):
    """Perform supplementary research on missing topics."""

    configurable = Configuration.from_runnable_config(config)

    topics = state.get("refinement_topics", [])
    tools = await get_all_tools(config)

    if not tools:
        return Command(
            goto="rewrite_final_report",
            update={
                "refinement_notes": "⚠️ No tools available for supplementary search.",
                "messages": [AIMessage(content="⚠️ Skipped search — No tools available.")],
            },
        )

    model = (
        configurable_model.bind_tools(tools)
        .with_config({
            "model": configurable.research_model,
            "max_tokens": configurable.research_model_max_tokens,
            "api_key": get_api_key_for_model(configurable.research_model, config),
        })
    )

    queries = "\n".join(f"- {t}" for t in topics)
    prompt = f"""
You are a research assistant conducting supplementary searches.
For each topic below, provide concise, factual summaries.

Missing Topics:
{queries}

Return a single markdown section like:

# Supplementary Findings
## [Topic]
<concise factual summary>
"""

    response = await model.ainvoke([HumanMessage(content=prompt)])

    return Command(
        goto="rewrite_final_report",
        update={
            "refinement_notes": response.content,
            "messages": [
                AIMessage(content=f"🔍 Supplementary findings collected for: {', '.join(topics)}")
            ],
        },
    )


# -----------------------------------------------------
# 3. rewrite_final_report
# -----------------------------------------------------

async def rewrite_final_report(state: AgentState, config):
    """Rewrite the report with refined information."""

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

    prompt = f"""
You are a professional report rewriting assistant.
Integrate the supplementary findings into the final report, ensuring:

- Structure remains consistent and well-organized  
- No duplicated sections  
- The writing tone remains consistent  
- The revised report fully satisfies the research brief

<Research Brief>
{brief}

<Original Final Report>
{original_report}

<Supplementary Findings>
{notes}

Return the complete improved report in clean markdown.
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
            "refinement_loops": loops,        # 중요!! loop state 유지
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
final_refinement_builder.add_edge("detect_missing_info", "conduct_refinement_search")
final_refinement_builder.add_edge("conduct_refinement_search", "rewrite_final_report")
final_refinement_builder.add_edge("rewrite_final_report", "detect_missing_info")
final_refinement_builder.add_edge("detect_missing_info", END)

final_refinement_subgraph = final_refinement_builder.compile()

__all__ = ["final_refinement_subgraph"]

