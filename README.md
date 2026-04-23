# Runway Comfy Custom Node

Direct Runway developer API custom node for ComfyUI.

This node uses `RUNWAYML_API_SECRET` from the environment, calls Runway's
`/v1/image_to_video` endpoint, polls the task, downloads the generated `.mp4`,
and returns the local file path plus Runway task id.

The API key is never exposed as a node input, so it is not saved into workflow
JSON.

## Install

Copy the package folder into ComfyUI:

```text
ComfyUI/custom_nodes/runway_direct_comfy
```

If needed, install dependencies in the ComfyUI Python environment:

```powershell
python -m pip install -r .\custom_nodes\runway_direct_comfy\requirements.txt
```

## Configure Key

Set your Runway developer API key before starting ComfyUI:

```powershell
$env:RUNWAYML_API_SECRET="REPLACE_WITH_RUNWAY_API_SECRET"
python .\main.py
```

For persistent Windows configuration:

```powershell
setx RUNWAYML_API_SECRET "REPLACE_WITH_RUNWAY_API_SECRET"
```

Open a new terminal after `setx`.

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
