from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from main import closest_color, get_color_name, get_delta_e, do_they_match
from colorthief import ColorThief
from PIL import Image

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze")
async def analyze_outfit(file: UploadFile = File(...)):
    # Save uploaded file temporarily
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Open and process the image
    image = Image.open(temp_path)
    width, height = image.size

    top_half = (0, 0, width, height // 2)
    bottom_half = (0, height // 2, width, height)

    cropped_top = image.crop(top_half)
    cropped_bottom = image.crop(bottom_half)

    cropped_top.save("temp_top.png")
    cropped_bottom.save("temp_bottom.png")

    top_palette = ColorThief("temp_top.png").get_palette(color_count=3, quality=1)
    bottom_palette = ColorThief("temp_bottom.png").get_palette(color_count=3, quality=1)

    top_name = get_color_name(top_palette[0])
    bottom_name = get_color_name(bottom_palette[0])

    result = do_they_match(top_palette, bottom_palette, top_name, bottom_name)

    # Cleanup temp files
    os.remove(temp_path)

    return {
        "top_color": top_name,
        "bottom_color": bottom_name,
        "result": result
    }