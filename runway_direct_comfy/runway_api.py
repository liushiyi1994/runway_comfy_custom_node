from __future__ import annotations

import base64
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import requests


RUNWAY_API_BASE_URL = "https://api.dev.runwayml.com/v1"
RUNWAY_API_VERSION = "2024-11-06"
DEFAULT_MODEL = "gen4.5"
VALID_MODELS = ("gen4.5",)
VALID_RATIOS = ("1280:720", "720:1280")
MIN_DURATION_SECONDS = 2
MAX_DURATION_SECONDS = 10
MAX_SEED = 4294967295


class RunwayApiError(RuntimeError):
    """Base error for direct Runway API node failures."""


class RunwayTaskFailed(RunwayApiError):
    """Raised when Runway marks a task as failed or canceled."""


class RunwayTaskTimeout(RunwayApiError):
    """Raised when a Runway task does not finish before the timeout."""


@dataclass(frozen=True)
class RunwayConfig:
    api_key: str
    base_url: str = RUNWAY_API_BASE_URL
    api_version: str = RUNWAY_API_VERSION
    request_timeout_seconds: int = 120


def get_api_key(env: Mapping[str, str] | None = None) -> str:
    env = os.environ if env is None else env
    api_key = (env.get("RUNWAYML_API_SECRET") or "").strip()
    if not api_key:
        raise RunwayApiError(
            "RUNWAYML_API_SECRET is not set. Set it before launching ComfyUI."
        )
    return api_key


def build_headers(api_key: str, api_version: str = RUNWAY_API_VERSION) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "X-Runway-Version": api_version,
        "Content-Type": "application/json",
    }


def image_bytes_to_data_uri(image_bytes: bytes, mime_type: str = "image/png") -> str:
    if not image_bytes:
        raise RunwayApiError("Image bytes are empty.")
    return f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"


def build_image_to_video_payload(
    *,
    prompt: str,
    prompt_image_uri: str,
    ratio: str,
    duration: int,
    model: str = DEFAULT_MODEL,
    seed: int | None = None,
) -> dict[str, Any]:
    prompt = (prompt or "").strip()
    if not prompt:
        raise RunwayApiError("Runway prompt must be non-empty.")
    if len(prompt) > 1000:
        raise RunwayApiError("Runway prompt must be 1000 characters or fewer.")
    if model not in VALID_MODELS:
        raise RunwayApiError(f"Unsupported Runway model '{model}'.")
    if ratio not in VALID_RATIOS:
        raise RunwayApiError(
            f"Unsupported Runway ratio '{ratio}'. Use one of: {', '.join(VALID_RATIOS)}."
        )
    if not isinstance(duration, int) or not (
        MIN_DURATION_SECONDS <= duration <= MAX_DURATION_SECONDS
    ):
        raise RunwayApiError(
            f"Runway duration must be an integer from {MIN_DURATION_SECONDS} to {MAX_DURATION_SECONDS} seconds."
        )
    if not prompt_image_uri.startswith("data:image/") and not prompt_image_uri.startswith(
        "http"
    ):
        raise RunwayApiError("promptImage must be an image data URI or URL.")
    if seed is not None and (seed < 0 or seed > MAX_SEED):
        raise RunwayApiError(f"Runway seed must be between 0 and {MAX_SEED}.")

    payload: dict[str, Any] = {
        "model": model,
        "promptText": prompt,
        "promptImage": prompt_image_uri,
        "ratio": ratio,
        "duration": duration,
    }
    if seed:
        payload["seed"] = int(seed)
    return payload


def start_image_to_video(config: RunwayConfig, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(
        f"{config.base_url}/image_to_video",
        headers=build_headers(config.api_key, config.api_version),
        json=payload,
        timeout=config.request_timeout_seconds,
    )
    return parse_runway_response(response)


def get_task(config: RunwayConfig, task_id: str) -> dict[str, Any]:
    response = requests.get(
        f"{config.base_url}/tasks/{task_id}",
        headers=build_headers(config.api_key, config.api_version),
        timeout=config.request_timeout_seconds,
    )
    return parse_runway_response(response)


def parse_runway_response(response: requests.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError as exc:
        text = response.text[:2000]
        raise RunwayApiError(f"Runway returned non-JSON response: {text}") from exc

    if not response.ok:
        raise RunwayApiError(
            f"Runway API HTTP {response.status_code}: {format_runway_error(data)}"
        )
    if not isinstance(data, dict):
        raise RunwayApiError("Runway API returned an unexpected response shape.")
    return data


def format_runway_error(data: dict[str, Any]) -> str:
    if "message" in data:
        return str(data["message"])
    if "error" in data:
        return str(data["error"])
    return str(data)[:2000]


def wait_for_task(
    config: RunwayConfig,
    task_id: str,
    *,
    timeout_seconds: int = 900,
    poll_interval_seconds: int = 10,
) -> dict[str, Any]:
    if timeout_seconds < 1:
        raise RunwayApiError("timeout_seconds must be at least 1.")
    if poll_interval_seconds < 1:
        raise RunwayApiError("poll_interval_seconds must be at least 1.")

    deadline = time.monotonic() + timeout_seconds
    last_task: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        last_task = get_task(config, task_id)
        status = str(last_task.get("status", "")).upper()
        if status == "SUCCEEDED":
            return last_task
        if status in {"FAILED", "CANCELED", "CANCELLED"}:
            raise RunwayTaskFailed(f"Runway task {task_id} ended with status {status}: {last_task}")
        time.sleep(poll_interval_seconds)

    raise RunwayTaskTimeout(
        f"Timed out after {timeout_seconds}s waiting for Runway task {task_id}. Last task: {last_task}"
    )


def extract_task_output_url(task: dict[str, Any]) -> str:
    status = str(task.get("status", "")).upper()
    if status != "SUCCEEDED":
        raise RunwayApiError(f"Runway task is not succeeded yet. Current status: {status or 'UNKNOWN'}.")

    output = task.get("output")
    if not isinstance(output, list) or not output or not isinstance(output[0], str):
        raise RunwayApiError("Runway task succeeded but did not include an output video URL.")
    return output[0]


def make_output_path(
    *,
    output_dir: str | os.PathLike[str],
    filename_prefix: str,
    task_id: str,
    extension: str = ".mp4",
    now: str | None = None,
) -> Path:
    safe_prefix = sanitize_filename_part(filename_prefix) or "runway"
    timestamp = now or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    task_suffix = sanitize_filename_part(task_id)[:8] or "task"
    extension = extension if extension.startswith(".") else f".{extension}"
    return Path(output_dir) / f"{safe_prefix}_{timestamp}_{task_suffix}{extension}"


def sanitize_filename_part(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value).strip())
    value = value.replace("..", "_").strip("._-")
    value = re.sub(r"_+", "_", value)
    return value


def download_file(url: str, output_path: str | os.PathLike[str]) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as response:
        if not response.ok:
            raise RunwayApiError(
                f"Failed to download Runway output HTTP {response.status_code}: {response.text[:1000]}"
            )
        with output_path.open("wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)
    return output_path


def generate_image_to_video(
    *,
    image_bytes: bytes,
    prompt: str,
    output_dir: str | os.PathLike[str],
    filename_prefix: str = "runway",
    model: str = DEFAULT_MODEL,
    ratio: str = "1280:720",
    duration: int = 5,
    seed: int | None = None,
    timeout_seconds: int = 900,
    poll_interval_seconds: int = 10,
    env: Mapping[str, str] | None = None,
) -> tuple[Path, str]:
    api_key = get_api_key(env)
    config = RunwayConfig(api_key=api_key)
    payload = build_image_to_video_payload(
        prompt=prompt,
        prompt_image_uri=image_bytes_to_data_uri(image_bytes),
        model=model,
        ratio=ratio,
        duration=duration,
        seed=seed,
    )
    start_task = start_image_to_video(config, payload)
    task_id = start_task.get("id")
    if not task_id or not isinstance(task_id, str):
        raise RunwayApiError(f"Runway start response did not include a task id: {start_task}")

    task = wait_for_task(
        config,
        task_id,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )
    output_url = extract_task_output_url(task)
    output_path = make_output_path(
        output_dir=output_dir,
        filename_prefix=filename_prefix,
        task_id=task_id,
    )
    return download_file(output_url, output_path), task_id
