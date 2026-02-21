from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import requests

from tools.airtable import AirtableClient
from tools.config import get_settings
from tools.upload import upload_file
from tools.utils import log_step


def _generate_image_bytes(prompt: str, reference_urls: list[str] | None = None) -> bytes:
    settings = get_settings()
    parts: list[dict[str, Any]] = [{'text': prompt}]
    if reference_urls:
        parts.extend({'file_data': {'file_uri': url}} for url in reference_urls)

    response = requests.post(
        f'{settings.google_image_endpoint}?key={settings.google_api_key}',
        json={'contents': [{'parts': parts}]},
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    candidates = payload.get('candidates', [])
    for candidate in candidates:
        for part in candidate.get('content', {}).get('parts', []):
            inline_data = part.get('inlineData')
            if inline_data and inline_data.get('data'):
                return base64.b64decode(inline_data['data'])

    raise ValueError(f'No image bytes in response: {payload}')


def generate_batch(records: list[dict[str, Any]], *, output_dir: str = 'artifacts/images') -> list[str]:
    client = AirtableClient()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    updated_ids: list[str] = []
    for record in records:
        record_id = record['id']
        fields = record.get('fields', {})
        prompt = fields.get('Image Prompt', '')
        reference_attachments = fields.get('Reference Images', [])
        reference_urls = [att['url'] for att in reference_attachments if att.get('url')]

        log_step(f'Generating image for {record_id}')
        image_bytes = _generate_image_bytes(prompt, reference_urls)
        image_path = out / f'{record_id}.png'
        image_path.write_bytes(image_bytes)

        public_url = upload_file(image_path)
        client.update_record(
            record_id,
            {
                'Generated Image': [{'url': public_url}],
                'Image Status': 'Generated',
            },
        )
        updated_ids.append(record_id)

    return updated_ids
