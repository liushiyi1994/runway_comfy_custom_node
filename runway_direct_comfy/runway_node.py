from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .runway_api import (
    DEFAULT_MODEL,
    MAX_IMAGE_DATA_URI_BYTES,
    VALID_MODELS,
    VALID_RATIOS,
    RunwayApiError,
    generate_image_to_video,
    image_bytes_to_data_uri,
)


RUNWAY_PROMPT_IMAGE_MIME_TYPE = "image/jpeg"
JPEG_QUALITY_STEPS = (92, 86, 80, 74, 68, 62, 56, 50)
IMAGE_DOWNSCALE_FACTOR = 0.85
MIN_PROMPT_IMAGE_ASPECT_RATIO = 0.5
MAX_PROMPT_IMAGE_ASPECT_RATIO = 2.0
MIN_ENCODED_IMAGE_DIMENSION = 64


class RunwayImageToVideoDirectNode:
    """ComfyUI node that sends one IMAGE input to Runway's direct API."""

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict[str, Any]]:
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": (
                    "STRING",
                    {
                        "default": "Animate this image with subtle natural motion and a slow cinematic camera move.",
                        "multiline": True,
                    },
                ),
                "model": (list(VALID_MODELS), {"default": DEFAULT_MODEL}),
                "ratio": (list(VALID_RATIOS), {"default": "1280:720"}),
                "duration": ("INT", {"default": 5, "min": 2, "max": 10, "step": 1}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 4294967295}),
                "filename_prefix": ("STRING", {"default": "runway"}),
                "timeout_seconds": ("INT", {"default": 900, "min": 30, "max": 3600, "step": 10}),
                "poll_interval_seconds": ("INT", {"default": 10, "min": 2, "max": 120, "step": 1}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("video_path", "task_id")
    FUNCTION = "generate"
    CATEGORY = "Runway/Direct API"
    OUTPUT_NODE = True

    def generate(
        self,
        image,
        prompt: str,
        model: str = DEFAULT_MODEL,
        ratio: str = "1280:720",
        duration: int = 5,
        seed: int = 0,
        filename_prefix: str = "runway",
        timeout_seconds: int = 900,
        poll_interval_seconds: int = 10,
    ) -> tuple[str, str]:
        image_bytes, mime_type = comfy_image_to_runway_image_bytes(image)
        output_dir = get_comfy_output_dir() / "runway_direct"
        output_path, task_id = generate_image_to_video(
            image_bytes=image_bytes,
            mime_type=mime_type,
            prompt=prompt,
            output_dir=output_dir,
            filename_prefix=filename_prefix,
            model=model,
            ratio=ratio,
            duration=int(duration),
            seed=int(seed) if int(seed) != 0 else None,
            timeout_seconds=int(timeout_seconds),
            poll_interval_seconds=int(poll_interval_seconds),
        )
        return (str(output_path), task_id)


def get_comfy_output_dir() -> Path:
    try:
        import folder_paths

        return Path(folder_paths.get_output_directory())
    except Exception:
        return Path("output")


def comfy_image_to_png_bytes(image) -> bytes:
    pil_image = comfy_image_to_pil_image(image)
    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")
    return buffer.getvalue()


def comfy_image_to_runway_image_bytes(
    image,
    *,
    max_data_uri_bytes: int = MAX_IMAGE_DATA_URI_BYTES,
) -> tuple[bytes, str]:
    pil_image = comfy_image_to_pil_image(image)
    validate_runway_prompt_image_aspect(pil_image)
    image_bytes = encode_jpeg_under_data_uri_limit(
        pil_image,
        max_data_uri_bytes=max_data_uri_bytes,
    )
    return image_bytes, RUNWAY_PROMPT_IMAGE_MIME_TYPE


def comfy_image_to_pil_image(image) -> Image.Image:
    if image is None:
        raise RunwayApiError("Image input is required.")

    if hasattr(image, "detach"):
        frame = image[0] if len(image.shape) == 4 else image
        array = frame.detach().cpu().numpy()
    else:
        array = np.asarray(image)
        if array.ndim == 4:
            array = array[0]

    if array.ndim != 3:
        raise RunwayApiError(f"Expected image with 3 dimensions, got shape {array.shape}.")

    if array.shape[-1] == 1:
        array = np.repeat(array, 3, axis=-1)
    elif array.shape[-1] >= 3:
        array = array[..., :3]
    else:
        raise RunwayApiError(f"Expected image channels in last dimension, got shape {array.shape}.")

    if np.issubdtype(array.dtype, np.floating):
        array = np.clip(array, 0.0, 1.0) * 255.0
    else:
        array = np.clip(array, 0, 255)

    rgb = array.astype(np.uint8)
    return Image.fromarray(rgb).convert("RGB")


def validate_runway_prompt_image_aspect(image: Image.Image) -> None:
    aspect_ratio = image.width / image.height
    if not (MIN_PROMPT_IMAGE_ASPECT_RATIO <= aspect_ratio <= MAX_PROMPT_IMAGE_ASPECT_RATIO):
        raise RunwayApiError(
            "Runway Gen-4.5 prompt image aspect ratio must be between "
            f"{MIN_PROMPT_IMAGE_ASPECT_RATIO:g} and {MAX_PROMPT_IMAGE_ASPECT_RATIO:g}. "
            f"Got {image.width}x{image.height} ({aspect_ratio:.3f})."
        )


def encode_jpeg_under_data_uri_limit(
    image: Image.Image,
    *,
    max_data_uri_bytes: int = MAX_IMAGE_DATA_URI_BYTES,
) -> bytes:
    if max_data_uri_bytes <= len(f"data:{RUNWAY_PROMPT_IMAGE_MIME_TYPE};base64,"):
        raise RunwayApiError("max_data_uri_bytes is too small for an image data URI.")

    current = image.convert("RGB")
    while True:
        for quality in JPEG_QUALITY_STEPS:
            buffer = BytesIO()
            current.save(buffer, format="JPEG", quality=quality, optimize=True)
            image_bytes = buffer.getvalue()
            if data_uri_byte_size(image_bytes, RUNWAY_PROMPT_IMAGE_MIME_TYPE) <= max_data_uri_bytes:
                return image_bytes

        next_width = max(1, int(current.width * IMAGE_DOWNSCALE_FACTOR))
        next_height = max(1, int(current.height * IMAGE_DOWNSCALE_FACTOR))
        if (
            next_width == current.width
            or next_height == current.height
            or next_width < MIN_ENCODED_IMAGE_DIMENSION
            or next_height < MIN_ENCODED_IMAGE_DIMENSION
        ):
            break

        current = current.resize((next_width, next_height), Image.Resampling.LANCZOS)

    raise RunwayApiError(
        "Could not encode the Runway prompt image under the 5 MB data URI limit. "
        "Try a smaller or less noisy image, or use a hosted HTTPS image URL."
    )


def data_uri_byte_size(image_bytes: bytes, mime_type: str) -> int:
    return len(image_bytes_to_data_uri(image_bytes, mime_type=mime_type).encode("utf-8"))


NODE_CLASS_MAPPINGS = {
    "RunwayImageToVideoDirectNode": RunwayImageToVideoDirectNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RunwayImageToVideoDirectNode": "Runway Image To Video (Direct API)",
}
