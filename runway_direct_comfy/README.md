# Runway Direct API ComfyUI Node

This ComfyUI custom node uses your own Runway developer API key through the
`RUNWAYML_API_SECRET` environment variable. It does not use Comfy's partner/API
node credit system and does not store the key inside workflow JSON.

## Node

Display name:

```text
Runway Image To Video (Direct API)
```

Category:

```text
Runway/Direct API
```

Inputs:

- `image`: Comfy `IMAGE`
- `prompt`: motion/camera prompt
- `model`: defaults to `gen4.5`
- `ratio`: `1280:720` or `720:1280`
- `duration`: 2 to 10 seconds
- `seed`: `0` omits seed
- `filename_prefix`: prefix for the downloaded `.mp4`
- `timeout_seconds`: polling timeout
- `poll_interval_seconds`: polling interval

Outputs:

- `video_path`: local downloaded `.mp4` path
- `task_id`: Runway task id

## Install

Copy the whole `runway_direct_comfy` folder into:

```text
ComfyUI/custom_nodes/runway_direct_comfy
```

If your Comfy Python environment does not already have dependencies installed,
run from the ComfyUI folder:

```powershell
python -m pip install -r .\custom_nodes\runway_direct_comfy\requirements.txt
```

## Set API Key

Set the Runway key before launching ComfyUI.

For the current PowerShell session:

```powershell
$env:RUNWAYML_API_SECRET="REPLACE_WITH_RUNWAY_API_SECRET"
python .\main.py
```

For persistent Windows user environment:

```powershell
setx RUNWAYML_API_SECRET "REPLACE_WITH_RUNWAY_API_SECRET"
```

After `setx`, open a new terminal before launching ComfyUI.

## Use In Comfy

Build this simple workflow:

```text
Load Image -> Runway Image To Video (Direct API)
```

Recommended first settings:

```text
model: gen4.5
ratio: 1280:720
duration: 5
seed: 0
filename_prefix: runway
timeout_seconds: 900
poll_interval_seconds: 10
```

Generated videos are downloaded under:

```text
ComfyUI/output/runway_direct/
```

The Runway output URL expires, so the node downloads the `.mp4` immediately and
returns the local path.

## Notes

- Do not add the Runway API key as a workflow field.
- Keep the key out of screenshots, logs, commits, and shared workflow JSON.
- This v1 node supports single-image image-to-video only.
