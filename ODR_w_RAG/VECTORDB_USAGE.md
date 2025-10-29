# 벡터디비 검색 Tool 사용 가이드

## 개요

open_deep_research에 벡터디비 검색 기능을 추가했습니다. 이 기능을 사용하면 내부 문서나 지식베이스에서 시맨틱 검색을 수행할 수 있습니다.

## 설정 방법

### 1. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 환경 변수를 설정하세요:

```bash
# .env 파일 생성 (프로젝트 루트에)
cp .env.example .env

# .env 파일 내용
VECTORDB_PERSIST_DIR=./chroma_db
VECTORDB_COLLECTION=kai_tech
EMBEDDING_MODEL=text-embedding-3-small
VECTORDB_EMBEDDING_FILE=./outputs/embedding_semantic.json
VECTORDB_DISTANCE=cosine
OPENAI_API_KEY=sk-your-key-here
```

**환경 변수 설명:**
- `VECTORDB_PERSIST_DIR`: ChromaDB 저장 경로 (기본값: ./chroma_db)
- `VECTORDB_COLLECTION`: 컬렉션 이름 (기본값: kai_tech)
- `EMBEDDING_MODEL`: 임베딩 모델 (기본값: text-embedding-3-small)
- `VECTORDB_EMBEDDING_FILE`: 임베딩된 문서 파일 경로 (기본값: ./outputs/embedding_semantic.json)
- `VECTORDB_DISTANCE`: 거리 계산 방식 (기본값: cosine)
- `OPENAI_API_KEY`: OpenAI API 키 (임베딩 생성을 위해 필요)

### 2. 검색 방법 선택

연구 에이전트를 실행할 때 다음 두 설정을 조정하여 검색 방식을 선택할 수 있습니다:

#### 검색 옵션 조합:

| `search_api` | `enable_vectordb_search` | 결과 |
|-------------|-------------------------|------|
| Tavily (또는 다른 web API) | `True` | Web 검색 + 벡터디비 검색 둘 다 사용 |
| Tavily (또는 다른 web API) | `False` | Web 검색만 사용 |
| None | `True` | 벡터디비 검색만 사용 |
| None | `False` | 검색 없음 (설정 오류) |

#### 권장 설정:
- **둘 다 사용** (기본값): `search_api=Tavily`, `enable_vectordb_search=True`
  - 웹 검색으로 최신 정보를, 벡터디비 검색으로 내부 문서를 활용
- **Web 검색만**: `search_api=Tavily`, `enable_vectordb_search=False`
- **벡터디비만**: `search_api=None`, `enable_vectordb_search=True`
  - 내부 문서만 검색할 때 유용

## 벡터디비 데이터 준비

벡터디비에 데이터를 인덱싱하기 위해서는 참고 폴더 `/Users/a11434/workspace/AI-Master-Project---Deep-Research/vectordb`의 스크립트를 사용할 수 있습니다.

### 데이터 포맷

벡터디비에 인덱싱할 JSON 파일 형식:

```json
{
  "파일명1.pdf": [
    {
      "page": 1,
      "chunk": 0,
      "content": "첫 번째 청크 내용...",
      "dense": [0.123, 0.456, ...]  # 임베딩 벡터
    },
    {
      "page": 1,
      "chunk": 1,
      "content": "두 번째 청크 내용...",
      "dense": [0.789, 0.012, ...]
    }
  ],
  "파일명2.pdf": [...]
}
```

### 임베딩 및 인덱싱

1. 텍스트를 청크로 분할 (semantic_crawler.py 등 사용)
2. 각 청크에 임베딩 생성 (`embedding.py` 사용)
3. ChromaDB에 인덱싱 (`main.py` 사용)

## 사용 예시

### Python에서 사용

```python
from langgraph.prebuilt import create_react_agent
from open_deep_research.configuration import Configuration

# 벡터디비 검색 활성화
config = Configuration(
    enable_vectordb_search=True
)

# 에이전트 실행...
```

### 설정 옵션

- `top_k`: 반환할 결과 수 (기본값: 5)
- 검색 결과에는 다음 정보가 포함됩니다:
  - 원본 파일명
  - 페이지 및 청크 번호
  - 유사도 점수
  - 문서 내용

## Tool 설명

벡터디비 검색 tool은 다음과 같이 작동합니다:

1. 입력된 쿼리를 임베딩으로 변환
2. ChromaDB에서 유사한 문서 검색
3. 상위 k개 결과를 반환 (유사도 높은 순서대로)
4. 각 결과에 메타데이터(파일명, 페이지, 청크 등) 포함

이 tool은 내부 문서 검색에 유용하며, 웹 검색과 함께 사용하면 더 풍부한 정보를 얻을 수 있습니다.

