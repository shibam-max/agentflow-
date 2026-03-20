import os
from contextlib import asynccontextmanager
import asyncpg

_pool = None


async def init_db():
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=os.getenv("DATABASE_URL", "postgresql://agentflow:localpass@localhost:5432/agentflow"),
        min_size=5,
        max_size=20,
        command_timeout=30,
    )


@asynccontextmanager
async def get_db():
    async with _pool.acquire() as conn:
        yield conn
