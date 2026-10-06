from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Real env vars win over .env; extra="ignore" because .env also holds keys for other services.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str

    vault_path: Path
    vault_ref: str
    vault_fetch: bool

    # Webhook (SPEC §15); see .env.example.
    webhook_secret: str
    webhook_seen_deliveries: int

    # Vault structure rules (D-006); see .env.example.
    vault_folder_types: dict[str, str]
    vault_default_note_type: str
    vault_excluded_dirs: set[str]
    vault_stripped_fences: set[str]

    # Chunker; see .env.example.
    chunk_max_chars: int
    chunk_merge_below_chars: int
    chunk_overlap_chars: int
    stub_min_chars: int
    chunk_metadata_headings: list[str]

    # Embeddings; see .env.example.
    embedding_model: str
    embedding_model_file: str
    embedding_pooling: str
    embedding_dim: int
    embedding_batch_size: int
    embedding_cache_dir: str
    embedding_query_prefix: str


settings = Settings()
