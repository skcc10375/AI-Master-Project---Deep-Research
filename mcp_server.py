from mcp.server.fastmcp import FastMCP
from openai import OpenAI
import os 
from pathlib import Path
import chromadb
from typing import List
import asyncio
import pypandoc

OPENAI_API_KEY = "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"


mcp = FastMCP(
    "VectorDBSearch_MarkdownToPDF",
    instructions=(
        "You provide semantic lookup over the internal vector database. "
        "Given a natural language query, return the most relevant embedded "
        "document chunks along with their metadata."
        "Convert Markdown to PDF format and save the result file."
    ),
    host="0.0.0.0",
    port=8002
)

    
@mcp.tool(name="vectordb_search")
async def vectordb_search(query: str, top_k: int = 5) -> str:
    """Search vector database for similar documents using semantic similarity."""

    api_key = OPENAI_API_KEY

    persist_dir = Path("/Users/a11492/Desktop/boot_camp/AI-Master-Project---Deep-Research/chroma_db").resolve()
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

