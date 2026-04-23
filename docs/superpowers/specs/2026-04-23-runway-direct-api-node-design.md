# Runway Direct API Node Design

**Goal**

Build a standalone ComfyUI custom-node package that uses a Runway developer API key from the `RUNWAYML_API_SECRET` environment variable to generate a video from a single input image with the latest Runway model, then download the generated `.mp4` to local disk and return a simple local file path.

**Scope**

This design covers only v1:

- single-image to video
- direct Runway API auth
- latest Runway model (`gen4.5`)
- local file save and simple path output
- step-by-step Comfy installation and usage guidance after implementation

This design explicitly excludes:

- first/last-frame generation
- native Comfy `VIDEO` object output
- workflow-embedded API keys
- advanced upload/file-hosting flows
- multiple-model orchestration

## Current Context

The current workspace contains direct API smoke tests for Vertex/Veo in Python and Node, but no Comfy custom-node package. There is no git repository initialized in this folder today, so spec and plan files can be written locally, but git commit steps cannot be completed unless the workspace is later placed inside a repository.

## Requirements

### Functional

1. Provide a Comfy custom node that accepts a single `IMAGE` input and a prompt.
2. Use the Runway developer API directly, not Comfy partner-node auth.
3. Read the API key from `RUNWAYML_API_SECRET`.
4. Default to Runway’s latest image-to-video model `gen4.5`.
5. Convert the Comfy image to a PNG data URI and send it in `promptImage`.
6. Start the task with `POST /v1/image_to_video`.
7. Poll `GET /v1/tasks/{id}` until the task succeeds, fails, or times out.
8. Download the first output video URL immediately to a local `.mp4`.
9. Return a simple local file path and task id for easy inspection in Comfy.
10. Include clear user-facing error messages for missing keys, API failures, moderation failures, and timeouts.

### Non-Functional

1. Do not store the Runway API key in node inputs or workflow JSON.
2. Keep dependencies minimal and explicit.
3. Keep the first implementation easy to debug.
4. Keep node/package structure small and self-contained.
5. Make local output paths deterministic and easy to find.

## External Constraints

Based on current Runway documentation:

- Authentication uses `Authorization: Bearer <key>`.
- Requests must include `X-Runway-Version: 2024-11-06`.
- `RUNWAYML_API_SECRET` is the standard environment variable for SDK and API usage.
- `promptImage` can be supplied as a base64 data URI for local files.
- Current latest model in the getting-started docs is `gen4.5`.
- Output URLs are ephemeral and should be downloaded immediately.

## Recommended Approach

Build a small custom-node package in this workspace with:

1. a direct Runway image-to-video node
2. a lightweight helper node for preview/save-oriented metadata passthrough if needed
3. a shared API/helper module for auth, request building, polling, and file download
4. tests for the non-network helper logic

This approach is preferred over forking an existing third-party node because it avoids weak image preprocessing, avoids saving keys into workflow JSON, and aligns tightly with the current Runway API.

## Alternatives Considered

### A. Use Comfy’s built-in Runway partner nodes

Pros:

- already integrated in Comfy
- lowest setup if Comfy-managed auth is acceptable

Cons:

- uses Comfy’s API-node/partner access model
- does not satisfy the requirement to use the team’s own Runway developer API key

Decision: rejected.

### B. Fork an existing third-party Runway custom node

Pros:

- faster initial prototype
- proves direct Runway key flow is possible

Cons:

- currently available example code is older and prototype-like
- exposes the API key as a node input
- weak return/output design for Comfy

Decision: use only as reference if needed, not as the final implementation basis.

### C. Build a small direct node from scratch

Pros:

- correct auth model
- simplest security story
- easiest to maintain
- fully tailored to current Runway docs and desired UX

Cons:

- modest implementation effort

Decision: selected.

## Architecture

### Package Layout

Planned package structure:

```text
runway_direct_comfy/
  __init__.py
  runway_node.py
  runway_api.py
  README.md
tests/
  test_runway_api.py
```

### Module Responsibilities

#### `runway_direct_comfy/runway_api.py`

Shared helper module responsible for:

- reading `RUNWAYML_API_SECRET`
- converting PIL image bytes to a data URI
- building request headers
- building the Runway request payload
- starting image-to-video tasks
- polling task state
- validating task outcomes
- downloading the resulting `.mp4`

This module should remain Comfy-agnostic where possible.

#### `runway_direct_comfy/runway_node.py`

Comfy-facing node definitions responsible for:

- declaring node inputs/outputs
- converting Comfy `IMAGE` tensors to PNG bytes
- calling helper functions in `runway_api.py`
- choosing output filenames/locations
- returning simple path-oriented results to Comfy

#### `runway_direct_comfy/__init__.py`

Registers node classes with ComfyUI through `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS`.

#### `tests/test_runway_api.py`

Local tests for deterministic, non-network logic:

- header building
- payload building
- ratio validation
- duration validation
- data URI creation
- output URL extraction
- output file naming

## Node Interface

### Main Node

Proposed display name:

`Runway Image To Video (Direct API)`

Proposed inputs:

- `image` (`IMAGE`, required)
- `prompt` (`STRING`, required)
- `duration` (`INT`, required, v1 default `5`)
- `ratio` (`COMBO`, required, defaults to `1280:720`)
- `seed` (`INT`, optional, `0` means omit)
- `model` (`COMBO`, required, default `gen4.5`)
- `filename_prefix` (`STRING`, optional, default `runway`)
- `timeout_seconds` (`INT`, optional)
- `poll_interval_seconds` (`INT`, optional)

Proposed outputs:

- `video_path` (`STRING`)
- `task_id` (`STRING`)

The node returns strings in v1 because that is the lowest-risk way to get a usable Comfy integration without reverse-engineering native `VIDEO` object expectations.

## Data Flow

1. User loads an image in Comfy.
2. The node receives Comfy `IMAGE` tensor input.
3. The node converts that tensor to PNG bytes.
4. The helper module base64-encodes the PNG and wraps it as:

```text
data:image/png;base64,...
```

5. The helper module sends:

```http
POST https://api.dev.runwayml.com/v1/image_to_video
Authorization: Bearer <RUNWAYML_API_SECRET>
X-Runway-Version: 2024-11-06
Content-Type: application/json
```

6. The request body includes:

- `model`
- `promptText`
- `promptImage`
- `ratio`
- `duration`
- optional `seed`

7. The helper polls `GET /v1/tasks/{id}`.
8. When the task succeeds, the helper reads `output[0]`.
9. The helper downloads the `.mp4` into a local output directory.
10. The node returns the local file path and task id.

## Output Location

For v1, save downloaded videos into a package-local output directory under the working Comfy instance, with names based on:

- filename prefix
- timestamp
- short task id suffix

Example:

```text
output/runway_direct/runway_2026-04-23T12-34-56_abcd1234.mp4
```

This keeps results easy to locate and avoids dependence on ephemeral Runway asset URLs.

## Error Handling

The node should surface these errors clearly:

1. `RUNWAYML_API_SECRET` missing
2. prompt empty
3. unsupported ratio
4. unsupported duration for the selected v1 model surface
5. Runway HTTP errors
6. Runway task `FAILED`
7. Runway moderation failures
8. polling timeout
9. output missing after success
10. download failure for returned output URL

Errors should be raised with plain, direct messages suitable for display in Comfy logs.

## Security

1. The API key must only come from `RUNWAYML_API_SECRET`.
2. The node must not expose an `api_key` input.
3. The node must not write the raw key to logs, workflow files, or output metadata.
4. Logged request summaries should avoid sensitive headers.

## Testing Strategy

### Automated Local Tests

Add tests for deterministic helper logic only:

- payload generation for required fields
- omission of seed when zero/empty
- data URI prefix for PNG
- task success output extraction
- handling of missing output
- filename construction
- environment-key validation behavior

### Manual Integration Test

After implementation:

1. set `RUNWAYML_API_SECRET`
2. copy the package into `ComfyUI/custom_nodes`
3. restart ComfyUI
4. run:

```text
LoadImage → Runway Image To Video (Direct API)
```

5. confirm the `.mp4` is downloaded locally
6. confirm the returned `video_path` points to an existing file

## User Workflow After Build

Expected user steps:

1. Open a terminal.
2. Set `RUNWAYML_API_SECRET`.
3. Start ComfyUI from that terminal.
4. Copy the package folder into `ComfyUI/custom_nodes/`.
5. Restart ComfyUI.
6. Add the new node to the graph.
7. Connect a `Load Image` node.
8. Enter prompt and settings.
9. Run the workflow.
10. Open the returned local file path or inspect the saved `.mp4`.

## Out-of-Scope Follow-Ups

After v1 works, likely follow-up tasks are:

- native Comfy `VIDEO` output support
- first/last-frame Runway mode
- optional text-to-video mode
- richer preview/save helper node
- retry logic for transient Runway failures
- optional support for additional latest Runway video models beyond `gen4.5`

## Self-Review

Checked for:

- placeholders: none left
- contradictory auth models: none
- hidden scope growth: constrained to single-image path-output v1
- mismatch with approved direction: none found

## Status

Spec written locally. Git commit not completed because this workspace is not currently a git repository.
