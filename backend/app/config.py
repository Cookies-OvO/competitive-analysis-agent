import os
from pydantic_settings import BaseSettings

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    # LLM
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"

    # Web
    host: str = "0.0.0.0"
    port: int = 8000

    # Embedding
    embedding_model: str = "BAAI/bge-small-zh-v1.5"

    # Database
    database_url: str = f"sqlite+aiosqlite:///{_BACKEND_DIR}/data/products.db"

    # FAISS
    rival_index_dir: str = f"{_BACKEND_DIR}/data/faiss_rival"
    improve_index_dir: str = f"{_BACKEND_DIR}/data/faiss_improve"

    # Business
    deep_dive_threshold: int = 60

    model_config = {
        "env_file": f"{_BACKEND_DIR}/.env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
