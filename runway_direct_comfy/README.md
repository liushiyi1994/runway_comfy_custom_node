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
- `ratio`: `1280:720`, `720:1280`, `1104:832`, `960:960`, `832:1104`, or `1584:672`
- `duration`: 2 to 10 seconds
- `seed`: `0` omits seed
- `filename_prefix`: prefix for the downloaded `.mp4`
- `timeout_seconds`: polling timeout
- `poll_interval_seconds`: polling interval

Outputs:

- `video_path`: local downloaded `.mp4` path
- `task_id`: Runway task id

## Install

For ComfyUI Desktop on Windows:

```powershell
cd C:\Users\<you>\Documents\ComfyUI\custom_nodes
git clone https://github.com/liushiyi1994/runway_comfy_custom_node.git runway_direct_comfy
cd C:\Users\<you>\Documents\ComfyUI
.\.venv\Scripts\python.exe -m pip install -r .\custom_nodes\runway_direct_comfy\requirements.txt
```

If you already cloned the repo, update it with:

```powershell
cd C:\Users\<you>\Documents\ComfyUI\custom_nodes\runway_direct_comfy
git pull
```

If you are installing by copying files instead, copy the whole
`runway_direct_comfy` folder into:

```text
ComfyUI/custom_nodes/runway_direct_comfy
```

Install dependencies in the same Python environment that runs ComfyUI.

For the current ComfyUI Desktop app, open the built-in terminal from the Desktop
bottom panel, then run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\custom_nodes\runway_direct_comfy\requirements.txt
```

For ComfyUI Windows Portable, run from the portable root folder:

```powershell
.\python_embeded\python.exe -m pip install -r .\ComfyUI\custom_nodes\runway_direct_comfy\requirements.txt
```

## Set API Key

If you start ComfyUI by clicking the Desktop icon, set the Runway key as a
persistent Windows user environment variable first:

```powershell
setx RUNWAYML_API_SECRET "REPLACE_WITH_RUNWAY_API_SECRET"
```

Close ComfyUI completely and reopen it from the icon. New apps inherit the
updated environment variable; already-running apps do not.

If you launch ComfyUI manually from PowerShell, you can set it only for that
session:

```powershell
$env:RUNWAYML_API_SECRET="REPLACE_WITH_RUNWAY_API_SECRET"
python .\main.py
```

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
