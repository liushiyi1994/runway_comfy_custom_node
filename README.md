# Runway Comfy Custom Node

Direct Runway developer API custom node for ComfyUI.

This node uses `RUNWAYML_API_SECRET` from the environment, calls Runway's
`/v1/image_to_video` endpoint, polls the task, downloads the generated `.mp4`,
and returns the local file path plus Runway task id.

The API key is never exposed as a node input, so it is not saved into workflow
JSON.

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

If you are installing by copying files instead, copy the package folder to:

```text
ComfyUI/custom_nodes/runway_direct_comfy
```

Then install dependencies in the same Python environment that runs ComfyUI.
For the current ComfyUI Desktop app, open the built-in terminal from the Desktop
bottom panel, then run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\custom_nodes\runway_direct_comfy\requirements.txt
```

For ComfyUI Windows Portable, run from the portable root folder:

```powershell
.\python_embeded\python.exe -m pip install -r .\ComfyUI\custom_nodes\runway_direct_comfy\requirements.txt
```

## Configure Key

If you start ComfyUI by clicking the Desktop icon, set the key as a persistent
Windows user environment variable first:

```powershell
setx RUNWAYML_API_SECRET "REPLACE_WITH_RUNWAY_API_SECRET"
```

Close ComfyUI completely and reopen it from the icon. New apps inherit the
updated environment variable; already-running apps do not.

If you launch ComfyUI manually from a terminal, you can set it only for that
session:

```powershell
$env:RUNWAYML_API_SECRET="REPLACE_WITH_RUNWAY_API_SECRET"
python .\main.py
```

## Use

In ComfyUI, create:

```text
Load Image -> Runway Image To Video (Direct API)
```

Initial settings:

```text
model: gen4.5
ratio: 1280:720
duration: 5
seed: 0
filename_prefix: runway
timeout_seconds: 900
poll_interval_seconds: 10
```

The downloaded video is saved under:

```text
ComfyUI/output/runway_direct/
```

See [runway_direct_comfy/README.md](runway_direct_comfy/README.md) for node
details.
