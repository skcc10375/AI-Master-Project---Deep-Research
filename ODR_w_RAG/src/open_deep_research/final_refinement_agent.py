"""
Final Refinement Agent (with loop limit)

This agent refines the final report after the main research process.
It:
  1. Detects missing or insufficiently covered topics.
  2. Conducts additional web searches using available tools.
  3. Rewrites the report with the new information.
  4. Loops until the report sufficiently covers all required areas or the loop limit is reached.

Flow:
detect_missing_info → conduct_refinement_search → rewrite_final_report → detect_missing_info → END
"""

import json
import asyncio
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from open_deep_research.configuration import Configuration
from open_deep_research.utils import (
    get_all_tools,
    get_api_key_for_model,
)
from open_deep_research.state import AgentState
from langchain.chat_models import init_chat_model

# Initialize configurable chat model
configurable_model = init_chat_model(configurable_fields=("model", "max_tokens", "api_key"))

# ==============================================================
# CONFIG
# ==============================================================
# 기본 반복 횟수 제한
MAX_REFINEMENT_LOOPS = 3


# ==============================================================
# 1. Detect Missing Information
# ==============================================================

async def detect_missing_info(state: AgentState, config):
    """Compare brief and report to identify missing or weakly covered topics."""
    configurable = Configuration.from_runnable_config(config)
    brief = state.get("research_brief", "")
    report = state.get("final_report", "")
    loops = state.get("refinement_loops", 0)

    # ✅ 루프 제한 검사
    if loops >= MAX_REFINEMENT_LOOPS:
        msg = f"🛑 Maximum refinement loops ({MAX_REFINEMENT_LOOPS}) reached. Stopping refinement process."
        return Command(
            goto=END,
            update={
                "messages": [AIMessage(content=msg)],
            },
        )

    model = configurable_model.with_config({
        "model": configurable.research_model,
        "max_tokens": 10000,
        "api_key": get_api_key_for_model(configurable.research_model, config),
    })

    prompt = f"""
You are a critical reviewer.
Compare the research brief and the final report.
Identify whether the report sufficiently covers all areas.

<Brief>
{brief}

<Final Report>
{report}

Return JSON with:
{{
  "need_additional_search": bool,
  "missing_topics": [list of strings],
  "comment": string
}}
"""
    response = await model.ainvoke([HumanMessage(content=prompt)])

    try:
        result = json.loads(response.content)
    except Exception:
        result = {"need_additional_search": False, "missing_topics": [], "comment": "Parsing error."}

    if result["need_additional_search"] and result["missing_topics"]:
        msg = (
            f"⚠️ Missing topics detected (loop {loops+1}/{MAX_REFINEMENT_LOOPS}): {', '.join(result['missing_topics'])}\n"
            f"Comment: {result['comment']}\nProceeding to supplementary search."
        )
        return Command(
            goto="conduct_refinement_search",
            update={
                "refinement_topics": result["missing_topics"],
                "refinement_loops": loops + 1,
                "messages": [AIMessage(content=msg)],
            },
        )
    else:
        msg = f"✅ Report sufficiently covers all necessary areas. {result['comment']}"
        return Command(
            goto=END,
            update={"messages": [AIMessage(content=msg)]},
        )


# ==============================================================
# 2. Conduct Supplementary Search
# ==============================================================

async def conduct_refinement_search(state: AgentState, config):
    """Perform additional searches on missing or weakly covered topics."""
    configurable = Configuration.from_runnable_config(config)
    topics = state.get("refinement_topics", [])
    tools = await get_all_tools(config)

    if not tools:
        return Command(
            goto="rewrite_final_report",
            update={
                "refinement_notes": "⚠️ No tools available for refinement search.",
                "messages": [AIMessage(content="⚠️ Skipping search — no tools available.")],
            },
        )

    research_model = (
        configurable_model.bind_tools(tools)
        .with_config({
            "model": configurable.research_model,
            "max_tokens": configurable.research_model_max_tokens,
            "api_key": get_api_key_for_model(configurable.research_model, config),
        })
    )

    queries = "\n".join(f"- {t}" for t in topics)
    prompt = f"""
You are a research assistant performing supplementary information searches.
Gather concise, factual summaries about these missing topics:

{queries}

Return a compact but informative summary suitable for integrating into the final report.
"""

    response = await research_model.ainvoke([HumanMessage(content=prompt)])

    return Command(
        goto="rewrite_final_report",
        update={
            "refinement_notes": response.content,
            "messages": [
                AIMessage(content=f"🔍 Supplementary data collected for refinement topics: {', '.join(topics)}")
            ],
        },
    )


# ==============================================================
# 3. Rewrite Final Report
# ==============================================================

async def rewrite_final_report(state: AgentState, config):
    """Rewrite the final report by integrating new findings."""
    configurable = Configuration.from_runnable_config(config)

    brief = state.get("research_brief", "")
    original_report = state.get("final_report", "")
    notes = state.get("refinement_notes", "")

    model = configurable_model.with_config({
        "model": configurable.final_report_model,
        "max_tokens": configurable.final_report_model_max_tokens,
        "api_key": get_api_key_for_model(configurable.final_report_model, config),
    })

    prompt = f"""
You are a report rewriting assistant.
Improve and expand the following final report by integrating the supplementary findings,
ensuring it fully aligns with the research brief.

<Research Brief>
{brief}

<Original Final Report>
{original_report}

<Supplementary Findings>
{notes}

Return the improved full report in well-structured markdown.
"""

    response = await model.ainvoke([HumanMessage(content=prompt)])
    rewritten = response.content

    loops = state.get("refinement_loops", 0)
    remaining = MAX_REFINEMENT_LOOPS - loops

    msg = (
        f"🪄 Final report refined and updated (loop {loops}/{MAX_REFINEMENT_LOOPS})."
        f" Remaining refinement chances: {remaining}."
    )

    return Command(
        goto="detect_missing_info",
        update={
            "final_report": rewritten,
            "messages": [AIMessage(content=msg)],
        },
    )


# ==============================================================
# 4. Subgraph Construction
# ==============================================================

final_refinement_builder = StateGraph(AgentState, config_schema=Configuration)

final_refinement_builder.add_node("detect_missing_info", detect_missing_info)
final_refinement_builder.add_node("conduct_refinement_search", conduct_refinement_search)
final_refinement_builder.add_node("rewrite_final_report", rewrite_final_report)

# Workflow edges
final_refinement_builder.add_edge(START, "detect_missing_info")
final_refinement_builder.add_edge("detect_missing_info", "conduct_refinement_search")
final_refinement_builder.add_edge("conduct_refinement_search", "rewrite_final_report")
final_refinement_builder.add_edge("rewrite_final_report", "detect_missing_info")
final_refinement_builder.add_edge("detect_missing_info", END)

# Compile subgraph
final_refinement_subgraph = final_refinement_builder.compile()


# ==============================================================
# Export
# ==============================================================

__all__ = ["final_refinement_subgraph"]
