from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    finnhub_api_key: str
    finnhub_base_url: str = "https://finnhub.io/api/v1"
    request_timeout: float = 10.0
    rate_limit_per_minute: int = 60

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
