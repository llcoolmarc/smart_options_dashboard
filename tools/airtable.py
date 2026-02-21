from __future__ import annotations

from typing import Any, Iterable

import requests

from tools.config import get_settings


class AirtableClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.headers.update(
            {
                'Authorization': f'Bearer {self.settings.airtable_api_key}',
                'Content-Type': 'application/json',
            }
        )

    @property
    def table_url(self) -> str:
        return (
            f"{self.settings.airtable_api_base}/{self.settings.airtable_base_id}/"
            f"{self.settings.airtable_table_name}"
        )

    def create_records(self, records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        created: list[dict[str, Any]] = []
        chunk: list[dict[str, Any]] = []
        for record in records:
            chunk.append({'fields': record})
            if len(chunk) == 10:
                created.extend(self._create_chunk(chunk))
                chunk = []
        if chunk:
            created.extend(self._create_chunk(chunk))
        return created

    def _create_chunk(self, records_chunk: list[dict[str, Any]]) -> list[dict[str, Any]]:
        response = self.session.post(self.table_url, json={'records': records_chunk}, timeout=60)
        response.raise_for_status()
        return response.json().get('records', [])

    def list_records(self, *, formula: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, str] = {}
        if formula:
            params['filterByFormula'] = formula

        all_records: list[dict[str, Any]] = []
        offset = None
        while True:
            page_params = dict(params)
            if offset:
                page_params['offset'] = offset

            response = self.session.get(self.table_url, params=page_params, timeout=60)
            response.raise_for_status()
            payload = response.json()
            all_records.extend(payload.get('records', []))
            offset = payload.get('offset')
            if not offset:
                return all_records

    def update_record(self, record_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        response = self.session.patch(
            f'{self.table_url}/{record_id}',
            json={'fields': fields},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def create_content_table(self) -> dict[str, Any]:
        url = f"{self.settings.airtable_meta_base}/bases/{self.settings.airtable_base_id}/tables"
        payload = {
            'name': self.settings.airtable_table_name,
            'fields': [
                {'name': 'Ad Name', 'type': 'singleLineText'},
                {'name': 'Product', 'type': 'singleLineText'},
                {'name': 'Reference Images', 'type': 'multipleAttachments'},
                {'name': 'Image Prompt', 'type': 'multilineText'},
                {
                    'name': 'Image Model',
                    'type': 'singleSelect',
                    'options': {'choices': [{'name': 'Nano Banana Pro'}]},
                },
                {
                    'name': 'Image Status',
                    'type': 'singleSelect',
                    'options': {
                        'choices': [
                            {'name': 'Pending'},
                            {'name': 'Generated'},
                            {'name': 'Approved'},
                            {'name': 'Rejected'},
                        ]
                    },
                },
                {'name': 'Generated Image', 'type': 'multipleAttachments'},
                {'name': 'Video Prompt', 'type': 'multilineText'},
                {
                    'name': 'Video Model',
                    'type': 'singleSelect',
                    'options': {'choices': [{'name': 'Veo 3.1'}]},
                },
                {
                    'name': 'Video Status',
                    'type': 'singleSelect',
                    'options': {
                        'choices': [
                            {'name': 'Pending'},
                            {'name': 'Generated'},
                            {'name': 'Approved'},
                            {'name': 'Rejected'},
                        ]
                    },
                },
                {'name': 'Generated Video', 'type': 'multipleAttachments'},
            ],
        }

        response = self.session.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()


def get_pending_images() -> list[dict[str, Any]]:
    client = AirtableClient()
    return client.list_records(formula="{Image Status}='Pending'")


def get_approved_images() -> list[dict[str, Any]]:
    client = AirtableClient()
    return client.list_records(formula="{Image Status}='Approved'")


def get_pending_videos() -> list[dict[str, Any]]:
    client = AirtableClient()
    return client.list_records(formula="{Video Status}='Pending'")
