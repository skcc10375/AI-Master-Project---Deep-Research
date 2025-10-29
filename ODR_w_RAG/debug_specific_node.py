"""특정 노드를 직접 테스트하는 디버깅 스크립트.

이 스크립트를 사용하면 전체 그래프가 아닌 특정 함수만 실행해서 테스트할 수 있습니다.
각 단계마다 중단점을 설정하고 상태를 확인할 수 있습니다.
"""

import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

# Import specific nodes for debugging
from src.open_deep_research.deep_researcher import (
    clarify_with_user,
    write_research_brief,
    final_report_generation
)

# Import vector database search tool
from src.open_deep_research.vectordb_search import vectordb_search


async def test_clarify_with_user():
    """clarify_with_user 노드 테스트"""
    state = {
        "messages": [HumanMessage(content="AI의 미래에 대해 조사해줘")],
    }
    
    config = {
        "model": "gpt-4o",
        "research_model": "gpt-4o",
        "research_model_max_tokens": 16000,
        "allow_clarification": True,
    }
    
    print("🧪 clarify_with_user 노드 테스트")
    print("=" * 80)
    
    # 여기에 중단점을 설정하면 함수 호출 과정을 추적할 수 있습니다
    result = await clarify_with_user(
        state=state,
        config=RunnableConfig(configurable=config)
    )
    
    print("\n결과:", result)
    return result


async def test_write_research_brief():
    """write_research_brief 노드 테스트"""
    state = {
        "messages": [HumanMessage(content="AI의 미래에 대해 조사해줘")],
    }
    
    config = {
        "model": "gpt-4o",
        "research_model": "gpt-4o",
        "research_model_max_tokens": 16000,
    }
    
    print("🧪 write_research_brief 노드 테스트")
    print("=" * 80)
    
    # 여기에 중단점을 설정하면 함수 호출 과정을 추적할 수 있습니다
    result = await write_research_brief(
        state=state,
        config=RunnableConfig(configurable=config)
    )
    
    print("\n결과:", result)
    return result


async def test_vectordb_search():
    """vectordb_search tool 테스트"""
    
    config = {
        "research_model": "gpt-4o",
        "research_model_max_tokens": 16000,
        "enable_vectordb_search": True,
    }
    
    print("🧪 vectordb_search tool 테스트")
    print("=" * 80)
    print("검색어: HBM(High Bandwidth Memory) 시장 전망")
    print("top_k: 3")
    print("-" * 80)
    
    # 여기에 중단점을 설정하면 함수 호출 과정을 추적할 수 있습니다
    # vectordb_search는 StructuredTool이므로 ainvoke 메서드 사용
    result = await vectordb_search.ainvoke(
        {
            "query": "HBM(High Bandwidth Memory) 시장 전망",
            "top_k": 3
        },
        RunnableConfig(configurable=config)
    )
    
    print("\n검색 결과:")
    print("-" * 80)
    print(result)
    print("-" * 80)
    
    return result


async def main():
    """메인 디버깅 함수 - 여기서 중단점을 설정하면 됩니다!"""
    print("\n" + "=" * 80)
    print("🔬 Deep Researcher - 특정 노드 디버깅")
    print("=" * 80)
    
    # # 테스트 1: clarify_with_user
    # print("\n[1/3] clarify_with_user 테스트")
    # print("-" * 80)
    # # 여기에 중단점을 설정하고 F5로 실행하세요
    # await test_clarify_with_user()
    
    # print("\n\n[2/3] write_research_brief 테스트")
    # print("-" * 80)
    # # 또는 여기에 중단점을 설정하세요
    # await test_write_research_brief()
    
    print("\n\n[3/3] vectordb_search tool 테스트")
    print("-" * 80)
    # 벡터디비 검색 테스트
    await test_vectordb_search()


if __name__ == "__main__":
    # 중단점을 설정하려면:
    # 1. test_clarify_with_user() 또는 test_write_research_brief() 또는 test_vectordb_search() 함수 안에 중단점 설정
    # 2. 또는 main() 함수의 await 라인에 중단점 설정
    # 3. F5를 눌러서 "Python: Debug Specific Node" 선택
    
    # 직접 특정 함수만 테스트하려면 주석을 해제하세요
    # test_clarify_with_user()
    # test_write_research_brief()
    # test_vectordb_search()  # 벡터디비 검색만 테스트
    
    # 또는 전체를 순차적으로 실행 (main 사용)
    asyncio.run(main())

