import unittest

import numpy as np
from PIL import Image

from runway_direct_comfy import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from runway_direct_comfy.runway_node import comfy_image_to_png_bytes


class RunwayNodeTests(unittest.TestCase):
    def test_node_registration_exports_display_name(self):
        self.assertIn("RunwayImageToVideoDirectNode", NODE_CLASS_MAPPINGS)
        self.assertEqual(
            NODE_DISPLAY_NAME_MAPPINGS["RunwayImageToVideoDirectNode"],
            "Runway Image To Video (Direct API)",
        )

    def test_comfy_image_to_png_bytes_converts_float_batch_image(self):
        image = np.zeros((1, 2, 3, 3), dtype=np.float32)
        image[0, :, :, 0] = 1.0

        png_bytes = comfy_image_to_png_bytes(image)

        self.assertTrue(png_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
        decoded = Image.open(__import__("io").BytesIO(png_bytes))
        self.assertEqual(decoded.size, (3, 2))
        self.assertEqual(decoded.mode, "RGB")


if __name__ == "__main__":
    unittest.main()
