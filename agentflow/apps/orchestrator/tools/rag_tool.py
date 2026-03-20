import os
from langchain_openai import OpenAIEmbeddings
from db.postgres import get_db

embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")


async def retrieve_context(query: str, top_k: int = 5) -> str:
    """Retrieve relevant context from pgvector store."""
    query_embedding = await embeddings_model.aembed_query(query)

    async with get_db() as conn:
        rows = await conn.fetch(
            """
            SELECT content, 1 - (embedding <=> $1::vector) AS similarity
            FROM embeddings
            ORDER BY embedding <=> $1::vector
            LIMIT $2
            """,
            str(query_embedding), top_k
        )

    if not rows:
        return "No relevant context found."

    return "\n\n".join([f"[similarity: {row['similarity']:.2f}]\n{row['content']}" for row in rows])


async def store_embedding(content: str, metadata: dict = None):
    """Store a document chunk with its embedding."""
    embedding = await embeddings_model.aembed_query(content)

    async with get_db() as conn:
        await conn.execute(
            "INSERT INTO embeddings (content, embedding, metadata) VALUES ($1, $2::vector, $3)",
            content, str(embedding), metadata or {}
        )
