import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

# Import the graph
from src.open_deep_research.deep_researcher import deep_researcher


async def debug_run():
    """Run the deep researcher with debug capabilities."""

    # 테스트할 질문
    question = "GPT-4와 Claude 3.5의 주요 차이점은 무엇인가요?"
    # question = "인공지능 언어모델의 사회적 영향에 대해 분석해줘."

    print("=" * 80)
    print("🔬 Deep Researcher 디버깅 모드")
    print("=" * 80)
    print(f"\n📝 질문: {question}\n")

    # 초기 메시지 구성
    messages = [HumanMessage(content=question)]

    # 설정 (컨피규레이션)
    config = {
        "model": "gpt-4o",  # 사용할 모델
        "research_model": "gpt-4o",
        "research_model_max_tokens": 16000,
        "stream": False,
        "allow_clarification": False,
        "search_api": "tavily",
        # "enable_vectordb_search": True,
        "max_researcher_iterations":2,
        "max_react_tool_calls":10,
        "max_concurrent_research_units":5
    }

    print("\n🚀 그래프 실행 시작...\n")
    print("-" * 80)

    try:
        # 추적할 주요 노드 목록
        tracking_nodes = [
            "clarify_with_user",
            "write_research_brief",
            "supervisor_subgraph",
            "lead_researcher_step",
            "scraper_step",
            "planner_step",
            "note_compression",
            "final_report_generation",
        ]

        step_count = 0

        print("\n📊 주요 노드 실행 추적:\n")

        async for event in deep_researcher.astream_events(
            {"messages": messages},
            config=RunnableConfig(configurable=config),
            version="v2",
        ):
            node_name = event.get("name", "")

            # 추적할 노드만 출력
            if not any(track_node in node_name for track_node in tracking_nodes):
                continue

            # 노드 시작
            if event["event"] == "on_chain_start":
                step_count += 1
                print(f"\n[{step_count}] 🔵 {node_name} 시작")
                print("-" * 80)

            # 노드 종료 - 출력 내용 표시
            elif event["event"] == "on_chain_end":
                print(f"✅ {node_name} 완료")

                # 출력 데이터 확인
                if "data" in event and "output" in event["data"]:
                    output = event["data"]["output"]

                    # clarify_with_user의 경우 명령어 정보 표시
                    if node_name == "clarify_with_user":
                        if isinstance(output, dict):
                            for key, value in output.items():
                                if key != "messages":
                                    print(f"📋 {key}: {value}")

                    # 메시지 출력
                    if isinstance(output, dict) and "messages" in output:
                        messages_list = output["messages"]
                        print(f"📊 전체 메시지 개수: {len(messages_list)}")

                        # 마지막 메시지 전체 내용 출력
                        if messages_list:
                            last_msg = messages_list[-1]
                            if hasattr(last_msg, "content") and last_msg.content:
                                content = str(last_msg.content)
                                print("📝 최신 메시지 전체 내용:")
                                print("-" * 40)
                                print(content)
                                print("-" * 40)

                        # 이전 메시지도 간단히 표시
                        if len(messages_list) > 1:
                            print(f"\n📚 이전 메시지들 ({len(messages_list)-1}개):")
                            for i, msg in enumerate(messages_list[:-1]):
                                if hasattr(msg, "type"):
                                    msg_preview = (
                                        str(msg.content)[:50]
                                        if hasattr(msg, "content") and msg.content
                                        else ""
                                    )
                                    print(f"   [{i+1}] {msg.type}: {msg_preview}...")
                    else:
                        # 메시지가 아닌 다른 출력도 표시
                        print(f"📦 출력 데이터: {output}")

                print("-" * 80)

            # 에러 발생
            elif event["event"] == "on_chain_error":
                print(f"\n❌ {node_name} 에러 발생")
                print("-" * 80)

        # --- 최종 결과 출력 ---
        result = await deep_researcher.ainvoke(
            {"messages": messages},
            config=RunnableConfig(configurable=config),
        )

        print("\n" + "=" * 80)
        print("✅ 모든 단계 실행 완료")
        print("=" * 80)

        if result and "messages" in result:
            final_message = result["messages"][-1]
            print("\n📄 최종 응답:")
            print("=" * 80)
            print(final_message.content)
            print("=" * 80)

    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ 에러 발생")
        print("=" * 80)
        print(f"\n에러: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # 디버깅을 위해서는 asyncio.run() 대신 asyncio.create_task()를 사용할 수도 있습니다
    asyncio.run(debug_run())
