from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/academy.db"
    course_materials_dir: str = ""
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    demo_mode: bool = True
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    nim_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_api_key: str = ""
    nvidia_nim_model: str = "nvidia/nemotron-3.5-lightning-30b-a3b"

    hf_token: str = ""
    hf_model: str = "meta-llama/Llama-3.1-8B-Instruct"

    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    sarvam_api_key: str = ""
    openai_realtime_model: str = "gpt-4o-realtime-preview"

    perplexity_api_key: str = ""

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = ""

    omniverse_bridge_url: str = "ws://localhost:8010/twin"
    nvcf_api_key: str = ""

    monthly_budget_usd: float = 25.0
    default_tutor_provider: str = "demo"

    @property
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def materials_path(self) -> Path:
        if self.course_materials_dir:
            path = Path(self.course_materials_dir)
            if not path.is_absolute():
                path = (Path.cwd() / path).resolve()
            if path.exists():
                return path
        return self.repo_root / "course-materials"


settings = Settings()
