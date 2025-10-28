from vectordb_chroma import (
    load_preembedded,
    index_to_chroma,
    perform_embedding,
    generation_answer_from_llm,
)
import yaml
from box import Box
from typing import List, Dict, Any


# -------- Retrieval --------
def retrieve(col, token, model, query_text: str, top_k: int = 4):
    # 문서벡터는 이미 DB에 있음 → 쿼리만 임베딩
    qvec = perform_embedding(token, model, [query_text])
    res = col.query(query_embeddings=qvec, n_results=top_k)
    # 출력 정리
    hits = []
    for i in range(len(res["ids"][0])):
        hits.append(
            {
                "id": res["ids"][0][i],
                "text": res["documents"][0][i],
                "metadata": res["metadatas"][0][i],
                "distance": res["distances"][0][i] if "distances" in res else None,
            }
        )
    return hits


# ------- Generation ------


def generate_answer_from_hits(query: str, hits: List[Dict[str, Any]]) -> str:
    """
    OPENAI_API_KEY가 있으면 LLM으로 생성.
    없으면 상위 컨텍스트를 붙여 간단 추출형 답변을 반환.
    """
    context_blocks = []
    for h in hits:
        md = h.get("metadata", {})
        header = f"[{md.get('filename')}, chunk={md.get('chunk')}]"
        context_blocks.append(f"{header}\n{h['text']}")
    context = "\n\n---\n\n".join(context_blocks) if context_blocks else "(no context)"

    print("------- context", context)
    print()
    print()
    try:
        system_prompt = """
당신은 한국어 기술 문서 보조자입니다.

[역할]
- 당신은 사용자가 제공하는 문서 요약·질의응답을 도와주는 전문가입니다.
- 답변 시 반드시 ‘사용자가 제공한 컨텍스트(context)’만을 근거로 삼아야 합니다.

[핵심 원칙]
1. 제공된 context 내 정보만 사용하십시오. 
   - 외부 지식, 상식, 추측, 과거 학습 정보는 절대 사용하지 않습니다.
   - 문서에 근거가 없으면 “문서에 해당 근거가 없습니다.”라고 답합니다.
2. 문서 표현과 수치를 그대로 사용하십시오. 임의 요약·의역·가정은 금지합니다.
3. 상충되는 내용이 있으면 모두 제시하고, 차이점을 명확히 설명하십시오.
4. context가 너무 길어 요약된 형태로 주어지더라도, 그 요약 내에서만 판단하십시오.
5. 답변은 간결하고 정확하게, 존댓말로 작성하십시오.

[출력 형식]
- 답변: 문서 근거 기반으로 3~6문장 또는 불릿 3~6개 이내
- 근거: 문서에서 인용한 구절 1~3개 (각 인용은 30자 이내)
- 근거_위치: [filename:{filename}, page:{page}, chunk:{chunk}] 형식으로 표기
- 한줄요약: 핵심 결론 1문장

[행동 규칙]
- 질문이 모호하면, 답하기 전에 한 번만 명확화 질문을 하십시오.
- 표가 요구되면 문서의 실제 항목만 포함하고 순서를 유지하십시오.
- context 외부 내용을 유추하거나 보충하지 마십시오.
- 문서 범위를 벗어난 질문에는 다음과 같이 답하십시오:
  “문서에 해당 근거가 없습니다. 이 문서가 다루는 범위는 기술부문(아키텍처, 인프라, S/W, 구축계획)입니다.”

[응답 언어]
- 한국어, 존댓말, 불필요한 서술 금지, 사실 중심.
"""
        user_prompt = f"""
            질문\n{query}\n\n"
            컨텍스트\n{context}\n\n"
            위 컨텍스트를 우선적으로 사용해 답하세요
            """
        resp = generation_answer_from_llm(
            system_prompt=system_prompt, user_input=user_prompt
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"LLM 모델 호출 실패 - Error : {e}"


if __name__ == "__main__":

    # file_path = "./outputs/embedding_2022-11-21_(주)우리은행_우리은행 비정형 데이터 자산화 시스템 구축_Ⅳ. 기술 부문.json"  # 실제 파일 경로 지정>
    file_path = "./outputs/embedding_2024-04-22_우리은행_비정형 데이터 자산화 시스템 2단계 구축_Ⅳ.기술부문.json"
    with open("./config.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        config = Box(config)

    # 1) 인덱싱/적재
    print("\n========== Indexing start")
    ids, docs, metas, embs = load_preembedded(file_path)
    if not ids:
        raise SystemExit("입력 JSON에 적재할 벡터가 없습니다.")
    col = index_to_chroma(ids, docs, metas, embs)

    # 2) Retrieval
    print("\n========== Retrieval start")
    query_text = "시스템의 확장성(Scalability)은 어떤 방식으로 확보되나요? as-of 2024"
    retrieve_k = 3

    hits = retrieve(
        col, config.MY_TOKEN, config.EMBEDDING_MODEL, query_text, retrieve_k
    )

    # 3) Generation
    print("\n========== Generation start")
    llm_output = generate_answer_from_hits(query_text, hits)
    print("\n========== QA start")
    print("query_text : ", query_text)
    print("llm_output : ", llm_output)
