from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

# Anchor all data to knowsphere/data
ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    # LLM
    llm_api_key: str = ""
    llm_model: str = "openai/gpt-oss-120b"
    llm_base_url: str = "https://api.groq.com/openai/v1"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "knowsphere123"

    # SQLite
    sqlite_url: str = f"sqlite+aiosqlite:///{DATA_DIR.as_posix()}/knowsphere.db"

    # FAISS
    faiss_index_path: str = str(DATA_DIR / "faiss_index")

    # File uploads
    uploads_path: str = str(DATA_DIR / "uploads")

    # Auth
    secret_key: str = "supersecretkey_change_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Seeding
    seed_on_startup: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
