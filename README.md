# ==============================
# AI-Master-Project – Deep Research
# 전체 실행 스크립트 (복붙용)
# ==============================

# 1. 프로젝트 루트로 이동
cd ODR_w_RAG

# 2. 가상환경 활성화
source .venv/bin/activate

# 3. Python 의존성 설치
uv sync

# 4. 시스템 패키지 설치 (Mac 기준)
brew install pandoc
brew install --cask mactex

# ==============================
# MCP SERVER 실행 (필수)
# 별도 터미널에서 실행 권장
# ==============================


# 5. Search Tool MCP server
python mcp_server.py

# 6. PDF Agent MCP server
cd src/open_deep_research/outputagent/
python mcpserver.py
# 성공 시: Uvicorn running on http://0.0.0.0:8001

# ==============================
# Open Deep Research 실행 (새 터미널 권장)
# ==============================

cd ODR_w_RAG

uvx --refresh --from "langgraph-cli[inmem]" \
  --with-editable . \
  --python 3.11 \
  langgraph dev --allow-blocking

# ==============================
# LangGraph Studio 설정 안내 (수동 작업)
# ==============================

# 1) Manage Assistants 진입
# 2) SearchAPI : None 또는 tavily 선택
# 3) Enable Vectordb Search 활성화
# 4) 반드시 절대경로로 저장 경로 입력
#    - md output path
#    - pdf output path
