import json
from pathlib import Path
from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain.embeddings.base import Embeddings
from openai import OpenAI

OPENAI_URL = "https://api.openai.com/v1"
API_KEY = "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"

# ========== Embedding 모델 래퍼 ==========
class SyncOpenAIEmbeddingModel(Embeddings):
    def __init__(self, model_name: str, base_url: str, api_key: str):
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        res = client.embeddings.create(input=texts, model=self.model_name)
        return [item.embedding for item in res.data]

    def embed_query(self, text: str) -> List[float]:
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        res = client.embeddings.create(input=[text], model=self.model_name)
        return res.data[0].embedding


# ========== Chunking 함수 ==========
def perform_chunking_from_text(
    text: str,
    chunk_type: str = "recursive",
    chunk_size: int = 1024,
    chunk_overlap: int = 100,
) -> List[str]:
    """텍스트를 recursive 또는 semantic 방식으로 청킹"""
    if chunk_type == "recursive":
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        return splitter.split_text(text)

    elif chunk_type == "semantic":
        embedding_model = SyncOpenAIEmbeddingModel(
            model_name="text-embedding-3-small",
            base_url=OPENAI_URL,
            api_key=API_KEY,
        )
        splitter = SemanticChunker(embedding_model)
        chunks = splitter.split_text(text)

        if not isinstance(chunks, list):
            raise ValueError(
                f"Unexpected type returned by split_text: {type(chunks)}"
            )
        return chunks
    
    elif chunk_type == "page":
        # 페이지 단위 그대로 반환
        return [text]

    else:
        raise ValueError(f"Unsupported chunk_type: {chunk_type}")


# ========== JSON → 페이지별 텍스트 → 전체 청킹 ==========
def main():
    input_path = Path("../parsing/output/2022-11-21_(주)우리은행_우리은행 비정형 데이터 자산화 시스템 구축_Ⅳ. 기술 부문.json")
    output_path = Path("./output/2022-11-21_(주)우리은행_우리은행 비정형 데이터 자산화 시스템 구축_Ⅳ. 기술 부문.json")

    if not input_path.exists():
        raise FileNotFoundError("output.json 파일이 존재하지 않습니다.")

    pages = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                pages.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 실패: {e}")

    all_chunks = []
    global_chunk_id = 1  # 전역 청크 번호 (페이지 구분 없이 증가)

    # 페이지별 청킹 수행
    for p in pages:
        page_num = p.get("page")
        page_text = p.get("content", "").strip()
        if not page_text:
            continue

        chunks = perform_chunking_from_text(
            text=page_text,
            chunk_type="page",  # recursive, semantic, page
            chunk_size=1024,
            chunk_overlap=100,
        )

        print(f"페이지 {page_num}: {len(chunks)}개 청크 생성")

        # ✅ 전체 청크 순서대로 ID 부여
        for chunk in chunks:
            all_chunks.append({
                "page": page_num,
                "content": chunk,
                "chunk": global_chunk_id,
            })
            global_chunk_id += 1  # 증가

    print(f"\n전체 {len(all_chunks)}개 청크 생성 완료.")

    # 결과 저장
    final_output = {Path(input_path.name).with_suffix(".pdf").name: all_chunks}

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print(f"\n결과 저장 완료: {output_path}")\


if __name__ == "__main__":
    main()