import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db
from app.graph.neo4j_driver import get_driver, close_driver, is_neo4j_available
from app.graph.embedded_graph import get_embedded_graph
from app.retrieval.embedder import load_index, warmup_embedder

# Import all routers
from app.api import auth, stats, ask, chat, graph, documents, insights, entities, datasources

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # Startup
    print("[KnowSphere] Initializing...")

    # Init SQLite
    await init_db()
    print("[KnowSphere] SQLite initialized.")

    # Init Graph backend
    try:
        if await is_neo4j_available():
            print("[KnowSphere] Neo4j connected.")
        else:
            print("[KnowSphere] Neo4j not detected; using Embedded Graph Engine (NetworkX).")
    except Exception as e:
        print(f"[KnowSphere] Neo4j check: {e}")

    # Initialize embedded graph store
    store = get_embedded_graph()
    print(f"[KnowSphere] Embedded Graph Store active ({len(store.nodes_data)} nodes, {len(store.edges_data)} edges).")

    # Load FAISS index & warmup embedding model in background
    try:
        load_index()
        asyncio.create_task(asyncio.to_thread(warmup_embedder))
        print("[KnowSphere] FAISS index loaded & embedding model warmup scheduled.")
    except Exception as e:
        print(f"[KnowSphere] FAISS load error: {e}")

    # Auto-seed on first run
    if settings.seed_on_startup:
        try:
            from seed_data import main as run_seed
            await run_seed()
        except Exception as e:
            print(f"[KnowSphere] Seed error: {e}")

    print("[KnowSphere] Ready!")
    yield

    # Shutdown
    await close_driver()
    print("[KnowSphere] Shutdown complete.")


app = FastAPI(
    title="KnowSphere API",
    description="GraphRAG-Based Corporate Knowledge Explorer",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(stats.router)
app.include_router(ask.router)
app.include_router(chat.router)
app.include_router(graph.router)
app.include_router(documents.router)
app.include_router(insights.router)
app.include_router(entities.router)
app.include_router(datasources.router)


@app.get("/")
async def root():
    return {
        "app": "KnowSphere",
        "version": "1.0.0",
        "description": "GraphRAG-Based Corporate Knowledge Explorer",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
