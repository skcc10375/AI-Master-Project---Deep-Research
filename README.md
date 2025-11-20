# AI-Master-Project – Deep Research 실행 가이드

cd ODR_w_RAG
source .venv/bin/activate

uv sync

* Mac 기준 필수 패키지
brew install pandoc
brew install --cask mactex

# ----- MCP Servers 실행 (각각 별도 터미널 권장) -----

* Search Tool MCP Server
python mcp_server.py

* PDF Agent MCP Server
cd src/open_deep_research/outputagent/
python mcpserver.py
 → Uvicorn running on http://0.0.0.0:8001 확인

# ----- Open Deep Research (LangGraph Studio) 실행 -----

1) cd ODR_w_RAG

2) 실행 명령어 : uvx --refresh --from "langgraph-cli[inmem]" \
  --with-editable . \
  --python 3.11 \
  langgraph dev --allow-blocking

# ----- LangGraph Studio 수동 설정 -----
 Manage Assistants 에서 다음 설정 수행
 - SearchAPI : None 또는 tavily
 - Enable Vectordb Search : ON
 - 저장 경로 (절대경로 필수)
   * md output path
   * pdf output path
