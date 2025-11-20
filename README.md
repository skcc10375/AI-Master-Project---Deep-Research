# AI-Master-Project – Deep Research 실행 가이드

1) 가상환경 세팅

```
cd ODR_w_RAG
uv venv
source .venv/bin/activate
```


4) 가상 환경 설치
```
uv sync
```

7) Mac 기준 필수 패키지
```
brew install pandoc
brew install --cask mactex
```

9) env 파일 복사 후 key 값 입력
```
cp .env.example .env
```

## ----- MCP Servers 실행 (각각 별도 터미널 권장) -----

### Search Tool MCP Server

```
python mcp_server.py
```

### PDF Agent MCP Server

```
cd src/open_deep_research/outputagent/
python mcpserver.py
```

 → Uvicorn running on http://0.0.0.0:8001 확인

## ----- Open Deep Research (LangGraph Studio) 실행 -----

```
cd ODR_w_RAG
```

랭그래프 스튜디오 실행 명령어 

```
uvx --refresh --from "langgraph-cli[inmem]" \
  --with-editable . \
  --python 3.11 \
  langgraph dev --allow-blocking
```

## ----- LangGraph Studio 수동 설정 -----
 Manage Assistants 에서 다음 설정 수행
 - SearchAPI : None 또는 tavily
 - Enable Vectordb Search : ON
 - 저장 경로 (절대경로 필수)
   * md output path
   * pdf output path
