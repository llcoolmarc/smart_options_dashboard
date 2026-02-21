from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from tools.airtable import AirtableClient
from tools.config import get_settings
from tools.upload import upload_file
from tools.utils import log_step, wait_for


def _start_video_job(prompt: str, start_frame_url: str) -> str:
    settings = get_settings()
    payload = {
        'instances': [
            {
                'prompt': prompt,
                'image': {'uri': start_frame_url},
            }
        ]
    }
    response = requests.post(
        f'{settings.google_video_endpoint}?key={settings.google_api_key}',
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    operation_name = data.get('name')
    if not operation_name:
        raise ValueError(f'No operation name returned: {data}')
    return operation_name


def _fetch_operation(operation_name: str) -> dict[str, Any]:
    settings = get_settings()
    url = f'https://generativelanguage.googleapis.com/v1beta/{operation_name}?key={settings.google_api_key}'
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    return response.json()


def _extract_video_url(operation_payload: dict[str, Any]) -> str:
    result = operation_payload.get('response', {})
    video = result.get('video', {})
    uri = video.get('uri') or result.get('uri')
    if not uri:
        raise ValueError(f'Video URI missing: {operation_payload}')
    return uri


def generate_videos(records: list[dict[str, Any]], *, output_dir: str = 'artifacts/videos') -> list[str]:
    client = AirtableClient()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    updated_ids: list[str] = []
    for record in records:
        record_id = record['id']
        fields = record.get('fields', {})
        prompt = fields.get('Video Prompt', '')
        generated_images = fields.get('Generated Image', [])
        if not generated_images:
            log_step(f'Skipping {record_id}: no Generated Image')
            continue

        start_frame_url = generated_images[0]['url']
        op_name = _start_video_job(prompt, start_frame_url)
        log_step(f'Polling video job {op_name}')

        completed = wait_for(
            lambda: _fetch_operation(op_name),
            is_done=lambda payload: payload.get('done', False),
            timeout_s=900,
            interval_s=15,
        )
        remote_video_url = _extract_video_url(completed)
        local_path = out / f'{record_id}.mp4'
        local_path.write_bytes(requests.get(remote_video_url, timeout=180).content)

        public_url = upload_file(local_path)
        client.update_record(
            record_id,
            {
                'Generated Video': [{'url': public_url}],
                'Video Status': 'Generated',
            },
        )
        updated_ids.append(record_id)

    return updated_ids
