from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_ENV_PATH = Path('.claude/.env')


def load_env(env_path: Path = DEFAULT_ENV_PATH) -> None:
    """Load variables from .claude/.env when present."""
    if env_path.exists():
        load_dotenv(env_path)


@dataclass(frozen=True)
class Settings:
    google_api_key: str
    kie_api_key: str
    airtable_api_key: str
    airtable_base_id: str
    airtable_table_name: str = 'Content'

    airtable_api_base: str = 'https://api.airtable.com/v0'
    airtable_meta_base: str = 'https://api.airtable.com/v0/meta'
    kie_upload_url: str = 'https://api.kie.ai/api/v1/files/upload'
    google_image_endpoint: str = (
        'https://generativelanguage.googleapis.com/v1beta/models/'
        'gemini-2.5-flash-image:generateContent'
    )
    google_video_endpoint: str = (
        'https://generativelanguage.googleapis.com/v1beta/models/'
        'veo-3.1-generate-preview:predictLongRunning'
    )


def get_settings() -> Settings:
    load_env()
    missing = []
    required = {
        'google_api_key': os.getenv('GOOGLE_API_KEY'),
        'kie_api_key': os.getenv('KIE_API_KEY'),
        'airtable_api_key': os.getenv('AIRTABLE_API_KEY'),
        'airtable_base_id': os.getenv('AIRTABLE_BASE_ID'),
    }
    for key, value in required.items():
        if not value:
            missing.append(key.upper())

    if missing:
        raise ValueError(
            'Missing required environment values: ' + ', '.join(sorted(missing))
        )

    return Settings(
        google_api_key=required['google_api_key'] or '',
        kie_api_key=required['kie_api_key'] or '',
        airtable_api_key=required['airtable_api_key'] or '',
        airtable_base_id=required['airtable_base_id'] or '',
        airtable_table_name=os.getenv('AIRTABLE_TABLE_NAME', 'Content'),
    )
