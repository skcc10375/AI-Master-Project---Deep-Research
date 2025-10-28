import os
import asyncio
from tavily import TavilyClient


query = "“2022년 우리은행 비정형 데이터 자산화 시스템 프로젝트” 에서 기술 특징 (데이터 아키텍쳐, 어플리케이션 등)과  “2024년 우리은행 비정형 데이터 자산화 시스템 프로젝트 2단계” 에서의 기술 특징을 각각 파악한 뒤 2단계에서 추가로 제시된 기술 방향을 분석하고 해당 내용을 보고서로 작성해줘"
key = "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"


# 환경변수에 API 키 넣기: export TAVILY_API_KEY="tvly-..." (mac/linux)
client = TavilyClient(api_key=key)

res = client.search(
    query=query,
    search_depth="advanced",  # "basic" | "advanced"
    max_results=8,  # 가져올 문서 수
    include_answer=True,  # 검색결과 기반 요약(LLM 생성)
    include_images=False,  # 이미지 필요시 True
    include_raw_content=False,  # 원문 전문 포함 여부
    include_image_descriptions=False,
    # days=30,  # 최근 30일로 제한(옵션)
    include_domains=[],  # 포함할 도메인 화이트리스트
    exclude_domains=[],  # 제외할 도메인 블랙리스트
)
# print(res)


def pretty_tavily_result(result):
    print(f"🕒 Response time: {result.get('response_time', 'N/A')}s")
    print(f"🔍 Query: {result.get('query')}")
    print(f"💬 Answer: {result.get('answer')}\n")

    print("📄 Top Search Results:")
    for i, r in enumerate(result.get("results", []), 1):
        print(f"{i}. [{r['title']}]({r['url']})")
        print(f"   ↳ {r['content'][:200]}...")
        print(f"   (score={r.get('score', 'N/A')})\n")


# 예시 사용
pretty_tavily_result(res)
