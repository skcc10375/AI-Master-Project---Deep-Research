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

    print("context", context)
    print()
    print()
    try:
        system_prompt = """
            당신은 한국어 기술 문서 보조자입니다.
            주어진 컨텍스트를 근거로 간결하고 정확하게 답하세요.
            근거가 없으면 모른다고 답하세요.
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

    file_path = "./outputs/embedding_test1.json"  # 실제 파일 경로 지정>
    with open("./config.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        config = Box(config)

    # 1) 인덱싱/적재
    print("========== Indexing start")
    ids, docs, metas, embs = load_preembedded(file_path)
    if not ids:
        raise SystemExit("입력 JSON에 적재할 벡터가 없습니다.")
    col = index_to_chroma(ids, docs, metas, embs)

    # 2) Retrieval
    print("========== Retrieval start")
    query_text = "HBM(High Bandwidth Memory) 시장 전망을 알려줘 "
    retrieve_k = 3

    hits = retrieve(
        col, config.MY_TOKEN, config.EMBEDDING_MODEL, query_text, retrieve_k
    )

    # 3) Generation
    print("========== Generation start")
    llm_output = generate_answer_from_hits(query_text, hits)
    print("query_text : ", query_text)
    print("llm_output : ", llm_output)
