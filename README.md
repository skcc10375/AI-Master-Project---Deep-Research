# AI-Master-Project---Deep-Research

### pdf agent 실행방법 

[ 필요 패키지 설치 ] 
 
1. pypandoc
   - pyproject.toml에 추가완료 
   - uv sync 로 알아서 프로젝트 의존성으로 설치됨 

2. Pandoc 설치
   - brew install pandoc

3. XeLaTeX 설치 (MacTeX 포함) --> 엄청 오래걸림 ㅠ
   - brew install --cask mactex

[ MCPserver 별도로 띄우기 (필수 !!!!!)] 

4. 가상환경 실행 
   - cd ODR_w_RAG 
   - source .venv/bin/activate

5. mcpserver.py 파일 실행 
   - (ODR_w_RAG) cd src/open_deep_research/outputagent/
   - cd python mcpserver.py
   - Uvicorn running on http://0.0.0.0:8001 뜨면 성공 ! 


[ 그 후 기존대로 langgraph studio 실행 ] 
   - uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev --allow-blocking
   - generate_pdf_report 노드 추가된 그래프 확인 가능 
   - New assistant 에서 저장 경로 설정 (반드시 로컬 절대 경로로 설정 !!!!!!) 
     - md output path : markdown 저장 경로
     - pdf output path : pdf 저장 경로 
