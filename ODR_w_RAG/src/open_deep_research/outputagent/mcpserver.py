from mcp.server.fastmcp import FastMCP
import os
import markdown
import pypandoc


mcp = FastMCP(
    "PDF PPT Generator",  # Name of the MCP server
    instructions="You are a PDF PPT Generator that can generate a PDF file from a given markdown document path.",  # Instructions for the LLM on how to use this tool
    host="0.0.0.0",  # Host address (0.0.0.0 allows connections from any IP)
    port=8001,  # Port number for the server
)


def md_to_pdf(md_path, pdf_path):
    # XeLaTeX 경로를 PATH에 추가 (macOS에서 MacTeX 설치 시)
    tex_bin_path = "/Library/TeX/texbin"
    if os.path.exists(tex_bin_path) and tex_bin_path not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{tex_bin_path}:{os.environ.get('PATH', '')}"

    pypandoc.convert_text(
        open(md_path, encoding="utf-8").read(),
        "pdf",
        format="md",
        outputfile=pdf_path,
        extra_args=[
            "--standalone",
            "--pdf-engine=xelatex",
            "-V",
            "mainfont=Apple SD Gothic Neo",  # macOS 기본 한글 폰트
            "-V",
            "geometry:margin=1in",
            "--toc",
        ],
    )

    return pdf_path


@mcp.prompt("agent_prompt")
def get_agent_prompt() -> str:
    """Get a prompt for the AI agent"""
    return f"""You are a helpful AI assistant that specializes in PDF PPT Generator."""


@mcp.tool("get_agent_prompt_tool")
def get_agent_prompt_tool() -> str:
    """Get a prompt for the PDF PPT Generator"""
    return get_agent_prompt()


@mcp.tool("text_to_markdown_tool")
def text_to_markdown_tool(md_text: str, md_path: str) -> str:
    """
    Save markdown text to a file.
    Args:
        md_text: The markdown text to be saved.
        md_path: The path where the markdown file will be saved.
    Returns:
        The path to the saved markdown file.
    """

    # 마크다운 텍스트를 그대로 저장 (HTML로 변환하지 않음)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    return md_path


# Add a dynamic markdown to pdf tool
@mcp.tool("markdown_to_pdf_tool")
def markdown_to_pdf_tool(md_path: str, pdf_path: str) -> str:
    """
    Generate a PDF file from a given markdown file path.
    Args:
        md_path: The path to the markdown file to be converted to PDF.
        pdf_path: The path to the output PDF file.
    Returns:
        The path to the generated PDF file.
    """
    return md_to_pdf(md_path, pdf_path)


if __name__ == "__main__":
    print("mcp remote server is running...")
    mcp.run(transport="streamable-http")

"""
uv run app/mcp_server.py
"""
