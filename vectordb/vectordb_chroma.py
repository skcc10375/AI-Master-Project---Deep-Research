import json
from pathlib import Path
from typing import List, Dict, Any
import argparse
from openai import OpenAI
import chromadb
import requests
import yaml
from box import Box

with open("config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
    config = Box(config)


# -------- 적재할 임베딩 데이터 로드 --------
def load_preembedded(path: str):
    """
    입력 JSON을 읽어 각 청크를 (id, document, metadata, embedding)로 평탄화.
    id: "{filename}::chunk::{chunk}"
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    ids, docs, metas, embs = [], [], [], []
    for fname, chunks in raw.items():
        for ch in chunks:
            pid = ch.get("page")
            cid = ch.get("chunk")
            text = ch.get("content") or ""
            vec = ch.get("dense") or []

            if not vec:
                continue
            ids.append(f"{fname}::chunk::{cid}")
            docs.append(text)
            metas.append(
                {
                    "filename": fname,
                    "page": pid,
                    "chunk": cid,
                }
            )
            embs.append(vec)
    return ids, docs, metas, embs


# -------- 인덱싱/적재 --------
def index_to_chroma(
    ids: List[str],
    docs: List[str],
    metas: List[Dict[str, Any]],
    embs: List[List[float]],
):
    client = chromadb.PersistentClient(path=config.PERSIST_DIR)
    col = client.get_or_create_collection(
        name=config.COLLECTION,
        metadata={"hnsw:space": config.DISTANCE},  # 코사인/유클리드/내적
    )
    # 필요 시 기존 동일 id 삭제 가능: col.delete(ids=ids)
    col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
    print(
        f"[OK] Indexed {len(ids)} chunks into Chroma @ {config.PERSIST_DIR}/{config.COLLECTION}"
    )
    return col


# (추가) 쿼리 임베딩
def perform_embedding(
    token: str, model: str, text_list: List[str]
) -> List[List[float]]:
    client = OpenAI(api_key=token)
    resp = client.embeddings.create(model=model, input=text_list)
    embeddings = [item.embedding for item in resp.data]
    return embeddings


# (추가) 답변 생성
def create_chat_messages(system_prompt, user_input):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]


def generation_answer_from_llm(system_prompt, user_input):
    client = OpenAI(api_key=config.MY_TOKEN)
    messages = create_chat_messages(system_prompt, user_input)
    res = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=messages,
        # temperature=0.7,
        # top_p=0.8,
        # presence_penalty=1.5,
    )
    return res
