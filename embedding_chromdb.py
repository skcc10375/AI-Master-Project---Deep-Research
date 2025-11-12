import json
from pathlib import Path
from typing import List
import chromadb


def load_preembedded(path: str):
    """
    Load pre-embedded data from JSON file.
    Returns (ids, docs, metas, embs) for ChromaDB indexing.
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


def load_all_preembedded_files(outputs_dir: str):
    """
    Load pre-embedded data from all JSON files in outputs directory.
    Returns (ids, docs, metas, embs) for ChromaDB indexing.
    """
    ids, docs, metas, embs = [], [], [], []

    outputs_path = Path(outputs_dir)
    if not outputs_path.exists():
        print(f"Warning: Outputs directory {outputs_dir} does not exist")
        return ids, docs, metas, embs

    json_files = list(outputs_path.glob("*.json"))
    if not json_files:
        print(f"Warning: No JSON files found in {outputs_dir}")
        return ids, docs, metas, embs

    print(f"Found {len(json_files)} JSON files in {outputs_dir}")

    for json_file in json_files:
        print(f"Loading embeddings from {json_file.name}...")
        try:
            file_ids, file_docs, file_metas, file_embs = load_preembedded(
                str(json_file)
            )
            ids.extend(file_ids)
            docs.extend(file_docs)
            metas.extend(file_metas)
            embs.extend(file_embs)
            print(f"Loaded {len(file_ids)} chunks from {json_file.name}")
        except Exception as exc:  # pragma: no cover - logging only
            print(f"Error loading {json_file.name}: {exc}")
            continue

    print(f"Total loaded: {len(ids)} chunks from {len(json_files)} files")
    return ids, docs, metas, embs


def index_to_chroma(
    ids: List[str],
    docs: List[str],
    metas: List[dict],
    embs: List[List[float]],
    persist_dir: str,
    collection_name: str,
    distance: str = "cosine",
):
    """Index data into ChromaDB."""
    client = chromadb.PersistentClient(path=persist_dir)
    col = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": distance},
    )
    if ids:
        col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
    return col


json_path = "/Users/a11434/workspace/AI-Master-Project---Deep-Research/embedded_json_outputs"
db_path = "/Users/a11434/workspace/AI-Master-Project---Deep-Research/chroma_db"
collection_name = "master_pjt"
distance = "cosine"

ids, docs, metas, embs = load_all_preembedded_files(str(json_path))
collection = index_to_chroma(ids, docs, metas, embs, str(db_path), collection_name, distance)