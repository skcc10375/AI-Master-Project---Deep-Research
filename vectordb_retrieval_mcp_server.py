from mcp.server.fastmcp import FastMCP
from openai import OpenAI
import os 
from pathlib import Path
import chromadb
from typing import List
import asyncio
OPENAI_API_KEY = "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"


mcp = FastMCP(
    "VectorDBSearch",
    instructions=(
        "You provide semantic lookup over the internal vector database. "
        "Given a natural language query, return the most relevant embedded "
        "document chunks along with their metadata."
    ),
    host="0.0.0.0",
    port=8001
)

def perform_embedding(token: str, model: str, text_list: List[str]) -> List[List[float]]:
    """Create embeddings for text using OpenAI."""
    client = OpenAI(api_key=token)
    resp = client.embeddings.create(model=model, input=text_list)
    embeddings = [item.embedding for item in resp.data]
    return embeddings

def retrieve(
    col, token: str, model: str, query_text: str, top_k: int = 4
) -> List[dict]:
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


@mcp.tool(name="vectordb_search")
async def vectordb_search(query: str, top_k: int = 5) -> str:
    """Search vector database for similar documents using semantic similarity."""

    api_key = OPENAI_API_KEY

    persist_dir = Path("/Users/a11434/workspace/AI-Master-Project---Deep-Research/chroma_db").resolve()
    collection_name = "master_pjt"
    embedding_model = "text-embedding-3-small"

    try:
        client = chromadb.PersistentClient(path=str(persist_dir))
        try:
            collection = client.get_collection(name=collection_name)
        except Exception:
            return "get_collectin 에서 에러"

        hits = retrieve(collection, api_key, embedding_model, query, top_k)
        if not hits:
            return (
                "No relevant documents found in the knowledge base. "
                "Try rephrasing your query or using a different search term."
            )

        formatted_output = f"Found {len(hits)} relevant document chunk(s):\n"
        for i, hit in enumerate(hits, 1):
            metadata = hit.get("metadata", {}) or {}
            filename = metadata.get("filename", "unknown")
            page = metadata.get("page", "unknown")
            chunk = metadata.get("chunk", "unknown")
            distance_score = hit.get("distance")

            formatted_output += (
                f"\n--- SOURCE {i}: {filename} (page {page}, chunk {chunk}) ---\n"
            )
            if distance_score is not None:
                formatted_output += f"Similarity Score: {1 - distance_score:.4f}\n"
            formatted_output += f"Document ID: {hit['id']}\n"
            formatted_output += f"Chunk Location: page {page} · chunk {chunk}\n\n"
            formatted_output += "Chunk Content:\n"
            formatted_output += f"{hit['text']}\n\n"
            formatted_output += "-" * 80 + "\n"

        return formatted_output

    except Exception as exc:
        return f"Error searching vector database: {exc}"

    
if __name__ == "__main__":
    # result = asyncio.run(vectordb_search("우리은행 2022년도 벡터디비 구성"))
    # print(result)
    print("VectorDB MCP server is running on")
    mcp.run(transport="streamable-http")
    # uv run vectordb_retrieval_
    
