from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .runway_api import (
    DEFAULT_MODEL,
    VALID_MODELS,
    VALID_RATIOS,
    RunwayApiError,
    generate_image_to_video,
)


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
        image_bytes = comfy_image_to_png_bytes(image)
        output_dir = get_comfy_output_dir() / "runway_direct"
        output_path, task_id = generate_image_to_video(
            image_bytes=image_bytes,
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
    buffer = BytesIO()
    Image.fromarray(rgb, mode="RGB").save(buffer, format="PNG")
    return buffer.getvalue()


NODE_CLASS_MAPPINGS = {
    "RunwayImageToVideoDirectNode": RunwayImageToVideoDirectNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RunwayImageToVideoDirectNode": "Runway Image To Video (Direct API)",
}
