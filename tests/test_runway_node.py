import unittest
from io import BytesIO
import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image

from runway_direct_comfy import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from runway_direct_comfy import runway_node
from runway_direct_comfy.runway_api import image_bytes_to_data_uri


class RunwayNodeTests(unittest.TestCase):
    def test_node_registration_exports_display_name(self):
        self.assertIn("RunwayImageToVideoDirectNode", NODE_CLASS_MAPPINGS)
        self.assertEqual(
            NODE_DISPLAY_NAME_MAPPINGS["RunwayImageToVideoDirectNode"],
            "Runway Image To Video (Direct API)",
        )

    def test_runway_node_is_output_node_because_it_saves_video(self):
        node_class = NODE_CLASS_MAPPINGS["RunwayImageToVideoDirectNode"]

        self.assertIs(getattr(node_class, "OUTPUT_NODE", False), True)

    def test_repo_root_entrypoint_exports_comfy_mappings(self):
        root_init = Path(__file__).resolve().parents[1] / "__init__.py"
        spec = importlib.util.spec_from_file_location("runway_comfy_repo_entrypoint", root_init)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        self.assertIn("RunwayImageToVideoDirectNode", module.NODE_CLASS_MAPPINGS)
        self.assertEqual(
            module.NODE_DISPLAY_NAME_MAPPINGS["RunwayImageToVideoDirectNode"],
            "Runway Image To Video (Direct API)",
        )

    def test_comfy_image_to_png_bytes_converts_float_batch_image(self):
        image = np.zeros((1, 2, 3, 3), dtype=np.float32)
        image[0, :, :, 0] = 1.0

        png_bytes = runway_node.comfy_image_to_png_bytes(image)

        self.assertTrue(png_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
        decoded = Image.open(BytesIO(png_bytes))
        self.assertEqual(decoded.size, (3, 2))
        self.assertEqual(decoded.mode, "RGB")

    def test_comfy_image_to_runway_image_bytes_limits_data_uri_size(self):
        rng = np.random.default_rng(123)
        image = rng.random((1, 512, 512, 3), dtype=np.float32)

        image_bytes, mime_type = runway_node.comfy_image_to_runway_image_bytes(
            image,
            max_data_uri_bytes=60_000,
        )
        data_uri = image_bytes_to_data_uri(image_bytes, mime_type=mime_type)

        self.assertEqual(mime_type, "image/jpeg")
        self.assertLessEqual(len(data_uri.encode("utf-8")), 60_000)
        decoded = Image.open(BytesIO(image_bytes))
        self.assertEqual(decoded.mode, "RGB")


if __name__ == "__main__":
    unittest.main()
