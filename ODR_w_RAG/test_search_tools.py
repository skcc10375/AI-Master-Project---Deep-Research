"""벡터디비 검색과 웹 검색을 테스트하는 독립 스크립트."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.open_deep_research.vectordb_search import vectordb_search
from src.open_deep_research.utils import tavily_search

os.environ["TAVILY_API_KEY"]="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"

async def test_vectordb_search():
    """벡터디비 검색 테스트"""
    print("\n" + "=" * 80)
    print("🔍 벡터디비 검색 테스트")
    print("=" * 80)
    print("검색어: HBM(High Bandwidth Memory) 시장 전망")
    print("top_k: 3")
    print("-" * 80)
    
    try:
        # vectordb_search는 StructuredTool이므로 ainvoke 사용
        result = await vectordb_search.ainvoke(
            {
                "query": "HBM(High Bandwidth Memory) 시장 전망",
                "top_k": 3
            },
            {"configurable": {}}
        )
        
        print("\n검색 결과:")
        print("-" * 80)
        print(result)
        print("-" * 80)
        
        return result
        
    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")
        return None


async def test_tavily_search():
    """Tavily 웹 검색 테스트"""
    print("\n" + "=" * 80)
    print("🌐 Tavily 웹 검색 테스트")
    print("=" * 80)
    print("검색어: ['AI의 미래']")
    print("max_results: 3")
    print("-" * 80)
    
    try:
        result = await tavily_search.ainvoke(
            {
                "queries": ["AI의 미래"],
                "max_results": 3
            },
            {"configurable": {}}
        )
        
        print("\n검색 결과:")
        print("-" * 80)
        print(result[:1000] + "..." if len(result) > 1000 else result)
        print("-" * 80)
        
        return result
        
    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")
        return None


async def test_combined_search():
    """벡터디비 + 웹 검색 조합 테스트"""
    print("\n" + "=" * 80)
    print("🔗 벡터디비 + 웹 검색 조합 테스트")
    print("=" * 80)
    print("검색어: '메모리 시장 동향'")
    print("-" * 80)
    
    results = {}
    
    # 1. 벡터디비 검색
    print("\n[1/2] 벡터디비에서 검색...")
    try:
        vectordb_result = await vectordb_search.ainvoke(
            {
                "query": "메모리 시장 동향",
                "top_k": 2
            },
            {"configurable": {}}
        )
        results['vectordb'] = vectordb_result
        print("✅ 벡터디비 검색 완료")
    except Exception as e:
        print(f"❌ 벡터디비 검색 실패: {str(e)}")
        results['vectordb'] = None
    
    # 2. 웹 검색 (API key 확인 후)
    print("\n[2/2] 웹에서 검색...")
    if not os.getenv("TAVILY_API_KEY"):
        print("⚠️  TAVILY_API_KEY가 없어 웹 검색을 건너뜁니다.")
        results['web'] = None
    else:
        try:
            web_result = await tavily_search.ainvoke(
                {
                    "queries": ["메모리 시장 동향"],
                    "max_results": 2
                },
                {"configurable": {}}
            )
            results['web'] = web_result
            print("✅ 웹 검색 완료")
        except Exception as e:
            print(f"❌ 웹 검색 실패: {str(e)}")
            results['web'] = None
    
    # 3. 결과 요약
    print("\n" + "=" * 80)
    print("📊 검색 결과 요약")
    print("=" * 80)
    
    if results['vectordb']:
        print("\n✅ 벡터디비 검색 성공")
        print(f"   결과 길이: {len(results['vectordb'])} 문자")
    else:
        print("\n❌ 벡터디비 검색 실패")
    
    if results['web']:
        print("\n✅ 웹 검색 성공")
        print(f"   결과 길이: {len(results['web'])} 문자")
    else:
        print("\n⚠️  웹 검색 건너뜀 (TAVILY_API_KEY 없음 또는 실패)")
    
    return results


async def main():
    """메인 테스트 함수"""
    print("\n" + "=" * 80)
    print("🧪 검색 도구 테스트")
    print("=" * 80)
    print("\n테스트할 항목을 선택하세요:")
    print("1. 벡터디비 검색만")
    print("2. 웹 검색만 (Tavily)")
    print("3. 둘 다 테스트 (순차)")
    print("4. 조합 검색 (같은 쿼리로 둘 다)")
    
    choice = input("\n선택 (1-4): ").strip()
    
    if choice == "1":
        await test_vectordb_search()
    elif choice == "2":
        await test_tavily_search()
    elif choice == "3":
        await test_vectordb_search()
        await test_tavily_search()
    elif choice == "4":
        await test_combined_search()
    else:
        print("잘못된 선택입니다. 기본 테스트를 실행합니다.")
        await test_combined_search()


if __name__ == "__main__":
    # 벡터디비 검색만 테스트하려면:
    # asyncio.run(test_vectordb_search())
    
    # 전체 메뉴 실행
    asyncio.run(main())

