import os
import asyncio
from tavily import TavilyClient
from openai import OpenAI


def run_tavily_search(key, query):
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
    return res


# def pretty_tavily_result(result):
#     print(f"🕒 Response time: {result.get('response_time', 'N/A')}s")
#     print(f"🔍 Query: {result.get('query')}")
#     print(f"💬 Answer: {result.get('answer')}\n")

#     print("📄 Top Search Results:")
#     for i, r in enumerate(result.get("results", []), 1):
#         print(f"{i}. [{r['title']}]({r['url']})")
#         print(f"   ↳ {r['content'][:200]}...")
#         print(f"   (score={r.get('score', 'N/A')})\n")


def generate_answer_with_openai(query, tavily_result, openai_key):
    """
    Tavily 검색 결과를 바탕으로 OpenAI를 사용해 상세한 답변 생성
    """
    # OpenAI 클라이언트 초기화 (환경변수에서 OPENAI_API_KEY 자동 로드)
    openai_client = OpenAI(api_key=openai_key)

    # Tavily 검색 결과에서 컨텍스트 추출
    context = ""
    for i, result in enumerate(tavily_result.get("results", []), 1):
        context += f"\n[출처 {i}] {result['title']}\n"
        context += f"URL: {result['url']}\n"
        context += f"내용: {result['content']}\n"
        context += f"관련도 점수: {result.get('score', 'N/A')}\n"
        context += "-" * 80 + "\n"

    # Tavily가 제공하는 요약이 있다면 추가
    if tavily_result.get("answer"):
        context += f"\n[Tavily 자동 요약]\n{tavily_result['answer']}\n"

    # OpenAI에 전달할 프롬프트 구성
    system_prompt = """당신은 기술 문서 분석 전문가입니다. 
제공된 검색 결과를 바탕으로 정확하고 구조화된 보고서를 작성해주세요."""

    user_prompt = f"""다음은 검색된 자료입니다:

{context}

위 자료를 바탕으로 다음 질문에 대한 상세한 보고서를 작성해주세요:
{query}

검색 결과에 해당 정보가 충분하지 않다면, 그 점을 명시하고 가능한 범위 내에서 답변해주세요. 절대 검색된 내용을 제외한 다른 내용을 추가하지 마세요
그리고 맨 아래에는 웹검색 출처 링크 정보를 명시해주세요. 
"""

    print("\n" + "=" * 80)
    print(" OpenAI로 답변 생성 중...")
    print("=" * 80 + "\n")

    # OpenAI API 호출
    response = openai_client.chat.completions.create(
        model="gpt-4o",  # 또는 "gpt-4o-mini", "gpt-4-turbo"
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=4000,
    )

    generated_answer = response.choices[0].message.content

    print(" 생성된 답변:")
    print("=" * 80)
    print(generated_answer)
    return generated_answer


# OpenAI로 답변 생성
if __name__ == "__main__":

    tavily_key = "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"
    openai_key = "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"

    query = "우리은행 비정형 데이터 자산화 시스템에서 검색 요청에서 임베딩·인덱싱·결과 제공까지의 프로세스가 2022년과 2024년 제안서에서 각각 어떻게 구성이 되었고 어떻게 변화했는가?"
    res = run_tavily_search(tavily_key, query)
    answer = generate_answer_with_openai(query, res, openai_key)
