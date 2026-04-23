import os
import tempfile
import unittest
from pathlib import Path

from runway_direct_comfy.runway_api import (
    DEFAULT_MODEL,
    RUNWAY_API_VERSION,
    RunwayApiError,
    build_headers,
    build_image_to_video_payload,
    extract_task_output_url,
    get_api_key,
    image_bytes_to_data_uri,
    make_output_path,
)


class RunwayApiHelperTests(unittest.TestCase):
    def test_get_api_key_reads_env_and_rejects_missing_values(self):
        env = {"RUNWAYML_API_SECRET": "  example-token  "}

        self.assertEqual(get_api_key(env), "example-token")

        with self.assertRaisesRegex(RunwayApiError, "RUNWAYML_API_SECRET"):
            get_api_key({})

        with self.assertRaisesRegex(RunwayApiError, "RUNWAYML_API_SECRET"):
            get_api_key({"RUNWAYML_API_SECRET": "   "})

    def test_build_headers_uses_bearer_key_and_version(self):
        headers = build_headers("example-token")

        self.assertEqual(headers["Authorization"], "Bearer example-token")
        self.assertEqual(headers["X-Runway-Version"], RUNWAY_API_VERSION)
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_image_bytes_to_data_uri_uses_png_prefix(self):
        uri = image_bytes_to_data_uri(b"abc", mime_type="image/png")

        self.assertEqual(uri, "data:image/png;base64,YWJj")

    def test_build_payload_defaults_to_latest_model_and_omits_zero_seed(self):
        payload = build_image_to_video_payload(
            prompt="A slow dolly push with soft atmospheric movement.",
            prompt_image_uri="data:image/png;base64,YWJj",
            ratio="1280:720",
            duration=5,
            seed=0,
        )

        self.assertEqual(payload["model"], DEFAULT_MODEL)
        self.assertEqual(payload["promptText"], "A slow dolly push with soft atmospheric movement.")
        self.assertEqual(payload["promptImage"], "data:image/png;base64,YWJj")
        self.assertEqual(payload["ratio"], "1280:720")
        self.assertEqual(payload["duration"], 5)
        self.assertNotIn("seed", payload)

    def test_build_payload_includes_nonzero_seed(self):
        payload = build_image_to_video_payload(
            prompt="Clouds move quickly across the sky.",
            prompt_image_uri="data:image/png;base64,YWJj",
            ratio="720:1280",
            duration=10,
            seed=42,
        )

        self.assertEqual(payload["seed"], 42)

    def test_build_payload_validates_prompt_ratio_and_duration(self):
        kwargs = {
            "prompt_image_uri": "data:image/png;base64,YWJj",
            "ratio": "1280:720",
            "duration": 5,
        }

        with self.assertRaisesRegex(RunwayApiError, "prompt"):
            build_image_to_video_payload(prompt="", **kwargs)

        with self.assertRaisesRegex(RunwayApiError, "ratio"):
            build_image_to_video_payload(
                prompt="Valid motion prompt.",
                prompt_image_uri="data:image/png;base64,YWJj",
                ratio="1:1",
                duration=5,
            )

        with self.assertRaisesRegex(RunwayApiError, "duration"):
            build_image_to_video_payload(
                prompt="Valid motion prompt.",
                prompt_image_uri="data:image/png;base64,YWJj",
                ratio="1280:720",
                duration=11,
            )

    def test_extract_task_output_url_handles_success_and_errors(self):
        self.assertEqual(
            extract_task_output_url({"status": "SUCCEEDED", "output": ["https://example.com/out.mp4"]}),
            "https://example.com/out.mp4",
        )

        with self.assertRaisesRegex(RunwayApiError, "output"):
            extract_task_output_url({"status": "SUCCEEDED", "output": []})

        with self.assertRaisesRegex(RunwayApiError, "not succeeded"):
            extract_task_output_url({"status": "RUNNING", "output": ["https://example.com/out.mp4"]})

    def test_make_output_path_sanitizes_prefix_and_uses_task_suffix(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_path = make_output_path(
                output_dir=tmp,
                filename_prefix="runway demo!/../bad",
                task_id="12345678-abcd-4000-9000-abcdef123456",
                extension=".mp4",
                now="2026-04-23T12-30-00Z",
            )

            self.assertEqual(Path(output_path).parent, Path(tmp))
            self.assertEqual(
                Path(output_path).name,
                "runway_demo_bad_2026-04-23T12-30-00Z_12345678.mp4",
            )


if __name__ == "__main__":
    unittest.main()
