# embed_from_chunk_json_simple_fixed.py
import json
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI
import yaml
from box import Box

with open("./config.yml", "r", encoding="utf-8") as f:
    cfg = Box(yaml.safe_load(f))


def embed_texts(token: str, model: str, texts: List[str]) -> List[List[float]]:
    client = OpenAI(api_key=token)
    resp = client.embeddings.create(model=model, input=texts)
    return [d.embedding for d in resp.data]


def _attach_embeddings(items: List[Dict[str, Any]], embs: List[List[float]]) -> None:
    for it, vec in zip(items, embs):
        it["dense"] = vec


def main(in_path: Path, out_path: Path, token: str, model: str):
    raw = json.loads(in_path.read_text(encoding="utf-8"))
    out: Dict[str, Any] = {}

    if isinstance(raw, dict):
        # ✅ 원래 최상위 키(보통 파일명)를 그대로 보존
        for file_key, items in raw.items():
            if not isinstance(items, list):
                raise ValueError(f"키 '{file_key}'의 값은 리스트여야 합니다.")
            texts = [it.get("content", "") for it in items]
            embs = embed_texts(token, model, texts)
            _attach_embeddings(items, embs)
            out[file_key] = items

        total_chunks = sum(len(v) for v in out.values())

    elif isinstance(raw, list):
        # 최상위 키가 없으므로 임시 키 사용
        items = raw
        texts = [it.get("content", "") for it in items]
        embs = embed_texts(token, model, texts)
        _attach_embeddings(items, embs)
        out = {"chunks": items}
        total_chunks = len(items)

    else:
        raise ValueError(
            "입력 JSON은 dict(파일명→리스트) 또는 list(청크 리스트) 형식이어야 합니다."
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 완료: {out_path} | 총 {total_chunks}개 | 모델: {model}")


if __name__ == "__main__":
    in_path = Path(
        "/Users/seohuipark/Documents/ai_master/chunking/output/2024-04-22_우리은행_비정형 데이터 자산화 시스템 2단계 구축_Ⅳ.기술부문.json"
    )
    out_path = Path("./outputs/embedding_sh_2024.json")
    main(in_path, out_path, cfg.MY_TOKEN, cfg.EMBEDDING_MODEL)
