import io
import os
from pathlib import Path
from uuid import uuid4
import base64
import asyncio
import json
import fal_client
import shutil

import numpy as np
from PIL import Image
import torch
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from transformers import AutoModel

from colorizer.inference import main_colorize
from ai_models.vidu_api_model import vidu_generate
from ai_models.wan_api_model import wan_generate
from ai_models.base64_uri import path2base64URI
from manual_creation import Manual
from create_anime import create_anime

from dotenv import load_dotenv
from s3_save_file import load_file_s3
from ai_models.cogvideox_run import cogvideox_generate

load_dotenv()
api_key = os.getenv("FAL_KEY")

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"


app = FastAPI()

if torch.cuda.is_available():
    device = torch.device("cuda")
    print("Using device: CUDA")
else:
    device = torch.device("cpu")
    print("Using device: CPU")
    

model = AutoModel.from_pretrained(
    "ragavsachdeva/magi",
    trust_remote_code=True
)
model = model.to(device)
model.eval()


processor = model.processor


OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def read_imagefile(file_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    return np.array(img)

@app.post("/crop_panels/")
async def crop_panels(file: UploadFile = File(...)):
    contents = await file.read()
    image_np = read_imagefile(contents)

    with torch.no_grad():
        results = model.predict_detections_and_associations([image_np])
    panel_bboxes = results[0]["panels"]  
    crops = processor.crop_image(image_np, panel_bboxes)
    encoded_images = []
    for i, crop_np in enumerate(crops):
        crop_img = Image.fromarray(crop_np)
        
        buf = io.BytesIO()
        crop_img.save(buf, format="PNG")
        base64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        encoded_images.append(base64_str)

    return JSONResponse({"panel_crops": encoded_images})


@app.post("/colorize/")
async def colorize(file: UploadFile = File(...)):
    contents = await file.read()
    input_img = Image.open(io.BytesIO(contents)).convert("RGB")

    uid = str(uuid4())
    input_path = OUTPUT_DIR / f"{uid}.png"
    input_img.save(input_path)

    main_colorize(str(input_path))

    colorized_path = input_path.with_stem(f"{input_path.stem}_colorized")
    if not colorized_path.exists():
        raise HTTPException(status_code=500, detail=str(e))

    with open(colorized_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode("utf-8")

    return JSONResponse({"colorized_image": encoded})


TASKS: dict[str, dict] = {}

async def do_generate(task_id: str, b64_uri: str, prompt: str):
    TASKS[task_id]["status"] = "running"
    handler = await fal_client.submit_async(
        "fal-ai/vidu/q1/image-to-video",
        arguments={"image_url": b64_uri, "prompt": prompt},
    )
    result = await handler.get()
    TASKS[task_id]["status"] = "done"
    TASKS[task_id]["result"] = result

@app.post("/vidu_animate/", status_code=202)
async def enqueue(file: UploadFile = File(...), prompt: str = Form(...), bg: BackgroundTasks = ...):
    contents = await file.read()
    b64 = base64.b64encode(contents).decode()
    uri = f"data:{file.content_type};base64,{b64}"

    task_id = str(uuid4())
    TASKS[task_id] = {"status": "pending", "result": None}
    bg.add_task(do_generate, task_id, uri, prompt)

    return JSONResponse({"task_id": task_id, "status_url": f"/vidu_status/{task_id}"})

@app.get("/vidu_status/{task_id}")
def status(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return {"status": task["status"], **({"result": task["result"]} if task["status"]=="done" else {})}


@app.post("/wan_animate/")
async def wan_animation(file: UploadFile = File(...), prompt: str = Form(...)):
    contents = await file.read()
    base64_file = base64.b64encode(contents).decode("utf-8")
    base64_uri = f"data:{file.content_type};base64,{base64_file}"

    try:
        result = await wan_generate(base64_uri, prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content=result)

@app.post("/cogvideox_animate/")
async def cogvideox_animation(file: UploadFile = File(...), prompt: str = Form(...)):
    tmp_path = f"/tmp/{uuid4()}{os.path.splitext(file.filename)[1] or ".png"}"
    try:
        with open(tmp_path, "wb") as out:
            shutil.copyfileobj(file.file, out)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        result = cogvideox_generate(prompt=prompt, image_or_video_path=tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    return JSONResponse(content=result)


@app.post("/manual_reveal/")
async def manual_reveal(file: UploadFile = File(...)):
    contents = await file.read()
    image_np = read_imagefile(contents)

    try:
        manual = Manual(image_np)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, manual.reveal)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content=result)

@app.post("/manual_zoom/")
async def manual_zoom(file: UploadFile = File(...)):
    contents = await file.read()
    image_np = read_imagefile(contents)

    try:
        manual = Manual(image_np)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, manual.zoom)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content=result)

@app.post("/manual_shake/")
async def manual_shake(file: UploadFile = File(...)):
    contents = await file.read()
    image_np = read_imagefile(contents)

    try:
        manual = Manual(image_np)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, manual.shake)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content=result)


@app.post("/create_anime/")
async def create_anime_from_urls(file: UploadFile = File(...)):
    if file.content_type != "application/json":
        raise HTTPException(status_code=400)
    content = await file.read()
    
    data = json.loads(content)

    videos = data["videos"]
    music = data["music"]
    result = create_anime(videos, music_url=music)
    return JSONResponse(content=result)