from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

import requests


def wait_for(
    fn: Callable[[], dict[str, Any]],
    *,
    is_done: Callable[[dict[str, Any]], bool],
    timeout_s: int = 300,
    interval_s: int = 5,
) -> dict[str, Any]:
    """Generic polling helper for async provider jobs."""
    start = time.time()
    while True:
        payload = fn()
        if is_done(payload):
            return payload
        if time.time() - start > timeout_s:
            raise TimeoutError(f'Operation timed out after {timeout_s}s')
        time.sleep(interval_s)


def download_file(url: str, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, timeout=90)
    response.raise_for_status()
    output.write_bytes(response.content)
    return output


def log_step(message: str) -> None:
    print(f'[creative-engine] {message}')
