import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import START, END, StateGraph
from pathlib import Path
from typing import TypedDict

client = MultiServerMCPClient(
    {
        "PDF PPT Generator": {
            "url": "http://localhost:8001/mcp", # mcpserver.py 에서 띄워진 주소와 동일 주소 !!! 
            "transport": "streamable_http",
        }
    }
)


class AgentState(TypedDict, total=False):
    markdown_text: str
    md_path: str
    pdf_path: str
    tool_result: str




async def call_text_to_markdown_tool(state: AgentState) -> AgentState:
    """markdown 저장 함수"""
    tools = await client.get_tools()
    tool_dict = {x.name: x for x in tools}
    pdf_tool = tool_dict["text_to_markdown_tool"]

    result = await pdf_tool.ainvoke(
        {"md_text": state["markdown_text"], "md_path": state["md_path"]}
    )
    return {"tool_result": result}


async def call_markdown_to_pdf_tool(state: AgentState) -> AgentState:
    """markdown 저장 함수"""
    tools = await client.get_tools()
    tool_dict = {x.name: x for x in tools}
    pdf_tool = tool_dict["markdown_to_pdf_tool"]

    result = await pdf_tool.ainvoke(
        {"md_path": state["md_path"], "pdf_path": state["pdf_path"]}
    )
    return {"tool_result": result}


async def pdfagent(final_report_text: str, md_output_path: str, pdf_output_path: str) -> AgentState:

    Path(md_output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(pdf_output_path).parent.mkdir(parents=True, exist_ok=True)
    print(f"Markdown 출력 경로: {md_output_path}")
    print(f"PDF 출력 경로: {pdf_output_path}")

    graph = StateGraph(AgentState)

    graph.add_node("call_text_to_markdown_tool", call_text_to_markdown_tool)
    graph.add_node("call_markdown_to_pdf_tool", call_markdown_to_pdf_tool)

    graph.add_edge(START, "call_text_to_markdown_tool")
    graph.add_edge("call_text_to_markdown_tool", "call_markdown_to_pdf_tool")
    graph.add_edge("call_markdown_to_pdf_tool", END)

    workflow = graph.compile()

    initial_state: AgentState = {
        "markdown_text": final_report_text,
        "md_path": str(md_output_path),
        "pdf_path": str(pdf_output_path),
    }
    final_state = await workflow.ainvoke(initial_state)


# if __name__ == "__main__":
#     final_report_text = Path("./inputtext/hybrid.md").read_text(encoding="utf-8")
#     md_output_path = "./outputmd/test55.md"
#     pdf_output_path = "./outputppt/test55.pdf"
#     # pdf_output_path.parent.mkdir(parents=True, exist_ok=True)

#     asyncio.run(pdfagent(final_report_text, md_output_path, pdf_output_path))
