# run_single_query.py
# pip install -U langchain langgraph langsmith tavily-python python-dotenv

import sys

sys.path.append("./src")

import os, json, asyncio, uuid, pathlib, datetime as dt
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from open_deep_research.deep_researcher import (
    deep_researcher_builder,
    deep_researcher_with_pdf_builder,
)
from langchain.schema import HumanMessage, AIMessage

# source .venv/bin/activate
# # Install dependencies and start the LangGraph server
# uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev --allow-blocking
# uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev --allow-blocking

# ---- 0) 환경 변수 로드 (.env 사용 시) ----
load_dotenv()

# ---- 1) 실험 파라미터: 기존 run_evaluate.py와 동일하게 ----
enable_ppt_generation = True
enable_vectordb_search = True

max_structured_output_retries = 3
allow_clarification = False
max_concurrent_research_units = 5  # default 10
search_api = "tavily"  # 일관성 유지
max_researcher_iterations = 4  # default 6
max_react_tool_calls = 5  # default 10
summarization_model = "openai:gpt-5"
summarization_model_max_tokens = 8192  # default 8192
research_model = "openai:gpt-5"  # 예시. 필요시 claude 등으로 교체
research_model_max_tokens = 8000  # default 10000
compression_model = "openai:gpt-5"
compression_model_max_tokens = 8000  # default 10000
final_report_model = "openai:gpt-5"
final_report_model_max_tokens = 8000  # default 10000

# ---- 2) 결과 저장 디렉터리 ----
OUTDIR = pathlib.Path("outputs")
OUTDIR.mkdir(parents=True, exist_ok=True)


def serialize_messages(obj):
    if isinstance(obj, list):
        return [serialize_messages(o) for o in obj]
    elif isinstance(obj, dict):
        return {k: serialize_messages(v) for k, v in obj.items()}
    elif isinstance(obj, HumanMessage):
        return {"type": "human", "content": obj.content}
    elif isinstance(obj, AIMessage):
        return {"type": "ai", "content": obj.content}
    else:
        return obj


def _now_tag():
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


async def run_single(question: str):
    # 3) 그래프 빌드 (메모리 체크포인터 사용)
    builder = (
        deep_researcher_with_pdf_builder
        if enable_ppt_generation
        else deep_researcher_builder
    )
    graph = builder.compile(checkpointer=MemorySaver())

    run_tag = _now_tag()

    # 4) 그래프 설정(configurable) 구성 — 기존 코드 그대로
    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4()),
            "enable_vectordb_search": enable_vectordb_search,
            "max_structured_output_retries": max_structured_output_retries,
            "allow_clarification": allow_clarification,
            "max_concurrent_research_units": max_concurrent_research_units,
            "search_api": search_api,
            "max_researcher_iterations": max_researcher_iterations,
            "max_react_tool_calls": max_react_tool_calls,
            "summarization_model": summarization_model,
            "summarization_model_max_tokens": summarization_model_max_tokens,
            "research_model": research_model,
            "research_model_max_tokens": research_model_max_tokens,
            "compression_model": compression_model,
            "compression_model_max_tokens": compression_model_max_tokens,
            "final_report_model": final_report_model,
            "final_report_model_max_tokens": final_report_model_max_tokens,
        }
    }

    # PDF 생성이 활성화된 경우 출력 경로를 설정에 주입
    pdf_path = None
    if enable_ppt_generation:
        pdf_path = OUTDIR / f"{run_tag}_report.pdf"
        config["configurable"]["pdf_output_path"] = str(pdf_path)

    # 5) 단일 쿼리 실행
    inputs = {"messages": [{"role": "user", "content": question}]}
    final_state = await graph.ainvoke(inputs, config)

    # 6) 산출물 추출(견고하게): 최종 보고서 텍스트와 전체 상태 저장
    report_text = None

    # 구현체마다 키가 다를 수 있어 방어적으로 접근
    for key in ["final_report", "report", "final", "output", "answer"]:
        if key in final_state and isinstance(final_state[key], (str, dict, list)):
            if isinstance(final_state[key], str):
                report_text = final_state[key]
                break
            # dict/list인 경우 text 가능성 탐색
            if isinstance(final_state[key], dict) and "content" in final_state[key]:
                report_text = final_state[key]["content"]
                break
            if (
                isinstance(final_state[key], list)
                and final_state[key]
                and isinstance(final_state[key][0], dict)
            ):
                maybe = final_state[key][0].get("content")
                if isinstance(maybe, str):
                    report_text = maybe
                    break

    # messages안 마지막 assistant 메시지에서 꺼내기(백업 플랜)
    if report_text is None and "messages" in final_state:
        msgs = final_state["messages"]
        if isinstance(msgs, list):
            for m in reversed(msgs):
                if m.get("role") in ("assistant", "system"):
                    content = m.get("content")
                    if isinstance(content, str):
                        report_text = content
                        break

    # 7) 파일로 저장
    base = OUTDIR / f"{run_tag}"
    json_path = str(base) + ".json"
    md_path = str(base) + ".md"

    with open(json_path, "w", encoding="utf-8") as f:
        print(final_state)
        json.dump(
            serialize_messages(final_state),
            f,
            ensure_ascii=False,
            indent=4,
            default=str,
        )

    if report_text:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report_text)

    print(f"[OK] 전체 상태: {json_path}")
    if report_text:
        print(f"[OK] 최종 보고서(텍스트): {md_path}")
    else:
        print("[WARN] report_text를 추출하지 못했습니다. JSON에서 직접 확인하세요.")

    pdf_result = final_state.get("pdf_generation_result")
    if enable_ppt_generation:
        if pdf_result:
            print(f"[INFO] PDF 상태: {pdf_result}")
        else:
            print(
                f"[WARN] PDF 결과가 상태에 없습니다. 설정된 출력 경로: {config['configurable'].get('pdf_output_path')}"
            )


if __name__ == "__main__":
    # 여기만 바꿔서 원하는 쿼리로 테스트
    # query = "SK hynix 2024년 원료 투입액 중 상위 3개 항목의 금액과 각 원료의 공급 시장 전망에 대해 분석해줘"
    # query = "반도체 요소 기술별로 한국과 미국 공동 협력 등록 특허 건수에 대한 자료가 있다면 찾아서 정확한 결과 알려줘"
    # query = "2024년 한국 인공지능 산업 실태를 조사하고 싶은데, 인공지능 모델 개발에 있어 사용하는 도구 형태 비중을 파악한 설문조사와 결과가 있다면 정리해서 보고서로 작성해줘 "
    query = "“2022년 우리은행 비정형 데이터 자산화 시스템 프로젝트” 에서 기술 특징 (데이터 아키텍쳐, 어플리케이션 등)과  “2024년 우리은행 비정형 데이터 자산화 시스템 프로젝트 2단계” 에서의 기술 특징 (데이터 아키텍쳐, 어플리케이션 등) 을 각각 파악한 뒤 2단계에서 추가로 제시된 기술 방향을 분석하고 해당 내용을 보고서로 작성해줘"
    asyncio.run(run_single(query))