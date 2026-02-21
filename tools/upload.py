from __future__ import annotations

from pathlib import Path

import requests

from tools.config import get_settings


def upload_file(file_path: str | Path) -> str:
    """Upload a local file to Kie and return a public URL."""
    settings = get_settings()
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open('rb') as handle:
        files = {'file': (path.name, handle)}
        response = requests.post(
            settings.kie_upload_url,
            headers={'Authorization': f'Bearer {settings.kie_api_key}'},
            files=files,
            timeout=120,
        )

    response.raise_for_status()
    payload = response.json()
    file_url = payload.get('data', {}).get('url') or payload.get('url')
    if not file_url:
        raise ValueError(f'Unexpected Kie upload response: {payload}')
    return file_url
