# AI-Master-Project---Deep-Research
명령어


source .venv/bin/activate

1. mcp 띄우기 : uv run vectordb_retrieval_mcp_server.py
2. OpenDeepResearch 띄우기
    1. cd odr
    2. uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev --allow-blocking

3. Manage Assistants 에서, SearchAPI ( None or tavily ) / Enable Vectordb Search  로 비교



