"""Vector database search tool for the Deep Research agent."""

import json
import os
from pathlib import Path
from typing import Annotated, List

import chromadb
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool
from openai import OpenAI


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
    
    # Get all JSON files in outputs directory
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
            file_ids, file_docs, file_metas, file_embs = load_preembedded(str(json_file))
            ids.extend(file_ids)
            docs.extend(file_docs)
            metas.extend(file_metas)
            embs.extend(file_embs)
            print(f"Loaded {len(file_ids)} chunks from {json_file.name}")
        except Exception as e:
            print(f"Error loading {json_file.name}: {str(e)}")
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
    distance: str = "cosine"
):
    """Index data into ChromaDB."""
    client = chromadb.PersistentClient(path=persist_dir)
    col = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": distance},
    )
    col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
    return col


def perform_embedding(token: str, model: str, text_list: List[str]) -> List[List[float]]:
    """Create embeddings for text using OpenAI."""
    client = OpenAI(api_key=token)
    resp = client.embeddings.create(model=model, input=text_list)
    embeddings = [item.embedding for item in resp.data]
    return embeddings


def retrieve(col, token: str, model: str, query_text: str, top_k: int = 4) -> List[dict]:
    """Retrieve similar documents from vector database."""
    qvec = perform_embedding(token, model, [query_text])
    res = col.query(query_embeddings=qvec, n_results=top_k)
    
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


@tool(description="Search internal documentation and knowledge base using vector similarity. Useful for finding relevant information from embedded documents.")
async def vectordb_search(
    query: str,
    top_k: Annotated[int, InjectedToolArg] = 5,
    config: RunnableConfig = None,
) -> str:
    """Search vector database for similar documents using semantic similarity.
    
    This tool searches through embedded documents stored in a vector database to find
    the most relevant information based on the query's semantic meaning.
    
    The tool loads all JSON files from the outputs directory for retrieving pre-embedded documents.

    Args:
        query: The search query to find similar documents
        top_k: Maximum number of results to return (default: 5)
        config: Runtime configuration for database and API settings

    Returns:
        Formatted string containing the most relevant documents with metadata
    """
    # Step 1: Get configuration from environment variables
    persist_dir = os.getenv("VECTORDB_PERSIST_DIR", "./chroma_db")
    collection_name = os.getenv("VECTORDB_COLLECTION", "kai_tech")
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    outputs_dir = os.getenv("VECTORDB_OUTPUTS_DIR", "./outputs")
    distance = os.getenv("VECTORDB_DISTANCE", "cosine")
    
    # Get embedding API key
    api_key = get_openai_api_key(config)
    if not api_key:
        return "Error: OpenAI API key not found. Please configure OPENAI_API_KEY environment variable."
    
    try:
        # Step 2: Load or index data
        client = chromadb.PersistentClient(path=persist_dir)
        
        # Check if collection exists, if not, create it from all JSON files in outputs directory
        try:
            collection = client.get_collection(name=collection_name)
        except Exception:
            # Collection doesn't exist, create it from all JSON files in outputs directory
            if not os.path.exists(outputs_dir):
                return f"Error: Vector database not initialized and outputs directory not found at {outputs_dir}. Please index your documents first."
            
            print(f"Initializing vector database from all JSON files in {outputs_dir}...")
            ids, docs, metas, embs = load_all_preembedded_files(outputs_dir)
            if not ids:
                return "Error: No embedded data found in any JSON files in the outputs directory."
            collection = index_to_chroma(ids, docs, metas, embs, persist_dir, collection_name, distance)
            print(f"Indexed {len(ids)} chunks into ChromaDB")
        
        # Step 3: Retrieve similar documents
        hits = retrieve(collection, api_key, embedding_model, query, top_k)
        
        # Step 4: Format the results
        if not hits:
            return "No relevant documents found in the knowledge base. Try rephrasing your query or using a different search term."
        
        formatted_output = f"Found {len(hits)} relevant document(s):\n\n"
        
        for i, hit in enumerate(hits, 1):
            metadata = hit.get("metadata", {})
            filename = metadata.get("filename", "unknown")
            page = metadata.get("page", "unknown")
            chunk = metadata.get("chunk", "unknown")
            distance = hit.get("distance")
            
            formatted_output += f"\n--- SOURCE {i}: {filename} ---\n"
            if distance is not None:
                formatted_output += f"Similarity Score: {1-distance:.4f}\n"
            formatted_output += f"Page: {page}, Chunk: {chunk}\n"
            formatted_output += f"Document ID: {hit['id']}\n\n"
            formatted_output += f"Content:\n{hit['text']}\n\n"
            formatted_output += "-" * 80 + "\n"
        
        return formatted_output
        
    except Exception as e:
        return f"Error searching vector database: {str(e)}"


def get_openai_api_key(config: RunnableConfig):
    """Get OpenAI API key from environment or config."""
    should_get_from_config = os.getenv("GET_API_KEYS_FROM_CONFIG", "false")
    if should_get_from_config.lower() == "true":
        api_keys = config.get("configurable", {}).get("apiKeys", {})
        if not api_keys:
            return None
        return api_keys.get("OPENAI_API_KEY")
    else:
        return os.getenv("OPENAI_API_KEY")

