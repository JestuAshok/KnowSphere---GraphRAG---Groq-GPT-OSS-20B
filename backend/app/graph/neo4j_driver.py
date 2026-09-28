import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from neo4j import AsyncGraphDatabase, AsyncDriver
from app.core.config import get_settings

settings = get_settings()

_driver: Optional[AsyncDriver] = None
_neo4j_available: Optional[bool] = None


async def is_neo4j_available() -> bool:
    global _neo4j_available, _driver
    if _neo4j_available is not None:
        return _neo4j_available
    # Fast socket check (instant connection refused if Neo4j is not running)
    try:
        from urllib.parse import urlparse
        uri = urlparse(settings.neo4j_uri)
        host = uri.hostname or "localhost"
        port = uri.port or 7687
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=0.3,
        )
        writer.close()
        await writer.wait_closed()
    except Exception:
        _neo4j_available = False
        return False

    try:
        driver = await get_driver()
        await asyncio.wait_for(driver.verify_connectivity(), timeout=1.0)
        _neo4j_available = True
        return True
    except Exception:
        _neo4j_available = False
        return False


async def get_driver() -> AsyncDriver:
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            connection_timeout=2.0,
        )
    return _driver


async def close_driver():
    global _driver, _neo4j_available
    if _driver:
        try:
            await _driver.close()
        except Exception:
            pass
        _driver = None
    _neo4j_available = None


async def run_query(
    cypher: str,
    params: Optional[Dict[str, Any]] = None,
    database: str = "neo4j",
) -> List[Dict[str, Any]]:
    """Execute a Cypher query and return list of record dicts."""
    driver = await get_driver()
    async with driver.session(database=database) as session:
        result = await session.run(cypher, params or {})
        records = await result.data()
        return records


async def run_write_query(
    cypher: str,
    params: Optional[Dict[str, Any]] = None,
    database: str = "neo4j",
) -> List[Dict[str, Any]]:
    """Execute a write Cypher query inside a write transaction."""
    driver = await get_driver()
    async with driver.session(database=database) as session:
        result = await session.run(cypher, params or {})
        records = await result.data()
        return records
