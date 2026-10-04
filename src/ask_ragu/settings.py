from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Real env vars win over .env; extra="ignore" because .env also holds keys for other services.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str

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


settings = Settings()
