# Runway Direct API Node Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a ComfyUI custom-node package that uses `RUNWAYML_API_SECRET` to generate a video from one input image with Runway `gen4.5`, download the result, and return the saved file path.

**Architecture:** Keep Runway API logic in a Comfy-agnostic helper module, keep tensor/image conversion and node registration in a small Comfy-facing module, and test the deterministic helper behavior without network calls. The v1 node returns strings (`video_path`, `task_id`) rather than a native Comfy `VIDEO` object.

**Tech Stack:** Python 3, ComfyUI custom-node API, Pillow, NumPy, `requests`, Runway REST API `2024-11-06`.

---

## Files

- Create: `runway_direct_comfy/__init__.py`
- Create: `runway_direct_comfy/runway_api.py`
- Create: `runway_direct_comfy/runway_node.py`
- Create: `runway_direct_comfy/README.md`
- Create: `tests/test_runway_api.py`
- Modify: `.gitignore`

## Tasks

### Task 1: Add Runway API Helper Tests

**Files:**
- Create: `tests/test_runway_api.py`

- [x] **Step 1: Write failing tests**

Create tests for headers, payload construction, prompt image data URI handling, task output extraction, output filename creation, and missing API key behavior.

- [x] **Step 2: Run tests to verify failure**

Run: `python -m unittest tests.test_runway_api`

Expected: import failure because `runway_direct_comfy.runway_api` does not exist.

### Task 2: Implement Runway API Helper Module

**Files:**
- Create: `runway_direct_comfy/runway_api.py`

- [x] **Step 1: Add helper implementation**

Implement:

- `RunwayApiError`
- `RunwayTaskFailed`
- `RunwayTaskTimeout`
- `RunwayConfig`
- `get_api_key`
- `build_headers`
- `image_bytes_to_data_uri`
- `build_image_to_video_payload`
- `extract_task_output_url`
- `make_output_path`
- `start_image_to_video`
- `get_task`
- `wait_for_task`
- `download_file`
- `generate_image_to_video`

- [x] **Step 2: Run tests**

Run: `python -m unittest tests.test_runway_api`

Expected: all helper tests pass.

### Task 3: Add Comfy Node Wrapper

**Files:**
- Create: `runway_direct_comfy/runway_node.py`
- Create: `runway_direct_comfy/__init__.py`

- [x] **Step 1: Add node class**

Implement `RunwayImageToVideoDirectNode` with:

- required `image`, `prompt`, `model`, `ratio`, `duration`, `filename_prefix`
- optional `seed`, `timeout_seconds`, `poll_interval_seconds`
- outputs `video_path`, `task_id`

- [x] **Step 2: Add Comfy registration**

Expose `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS`.

### Task 4: Add User Documentation

**Files:**
- Create: `runway_direct_comfy/README.md`
- Modify: root `README.md`

- [x] **Step 1: Add install/use instructions**

Document:

- setting `RUNWAYML_API_SECRET`
- copying `runway_direct_comfy` into `ComfyUI/custom_nodes`
- installing dependencies if needed
- restarting ComfyUI
- building a simple `Load Image -> Runway Image To Video (Direct API)` workflow

### Task 5: Validate, Stage Safely, Commit, Push

**Files:**
- Modify: `.gitignore`

- [x] **Step 1: Run tests and compile checks**

Run:

```powershell
python -m unittest tests.test_runway_api
python -m py_compile runway_direct_comfy\runway_api.py runway_direct_comfy\runway_node.py tests\test_runway_api.py
```

- [x] **Step 2: Check ignored sensitive files**

Run:

```powershell
git check-ignore -v local_workflow.json local_service_account.json outputs
```

- [x] **Step 3: Stage only safe files**

Stage code, docs, tests, and ignore rules only. Do not stage credential JSON, API workflow JSON, outputs, or environment files.

- [x] **Step 4: Commit and push**

Commit with `feat: add Runway direct API Comfy node` and push to `origin main`.

## Self-Review

- Spec coverage: all v1 requirements are mapped to tasks.
- Placeholder scan: no placeholders left.
- Type consistency: helper and node names are consistent across tasks.
