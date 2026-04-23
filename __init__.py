from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_impl_module():
    package_init = Path(__file__).resolve().parent / "runway_direct_comfy" / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "_runway_direct_comfy_impl",
        package_init,
        submodule_search_locations=[str(package_init.parent)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load Runway node package from {package_init}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_impl = _load_impl_module()

NODE_CLASS_MAPPINGS = _impl.NODE_CLASS_MAPPINGS
NODE_DISPLAY_NAME_MAPPINGS = _impl.NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
