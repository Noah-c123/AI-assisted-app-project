from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
from main import closest_color, get_color_name, get_delta_e, do_they_match
from colorthief import ColorThief
from PIL import Image
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2
from dotenv import load_dotenv

load_dotenv()
#
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PAT = os.getenv("CLARIFAI_PAT")
USER_ID = "clarifai"
APP_ID = "main"
MODEL_ID = "apparel-detection"
MODEL_VERSION_ID = "1ed35c3d176f45d69d2aa7971e6ab9fe"

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"]


def get_clothing_regions(image_path):
    channel = ClarifaiChannel.get_grpc_channel()
    stub = service_pb2_grpc.V2Stub(channel)

    metadata = (("authorization", f"Key {PAT}"),)

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    response = stub.PostModelOutputs(
        service_pb2.PostModelOutputsRequest(
            user_app_id=resources_pb2.UserAppIDSet(
                user_id=USER_ID,
                app_id=APP_ID
            ),
            model_id=MODEL_ID,
            version_id=MODEL_VERSION_ID,
            inputs=[
                resources_pb2.Input(
                    data=resources_pb2.Data(
                        image=resources_pb2.Image(base64=image_bytes)
                    )
                )
            ]
        ),
        metadata=metadata
    )

    if response.status.code != status_code_pb2.SUCCESS:
        print(f"Clarifai error: {response.status.description}")
        return None, None

    image = Image.open(image_path)
    width, height = image.size

    top_region = None
    bottom_region = None
    top_score = 0
    bottom_score = 0

    top_labels = ["shirt", "top", "jacket", "sweater", "hoodie", "blouse", "coat", "tshirt", "t-shirt"]
    bottom_labels = ["pants", "jeans", "shorts", "skirt", "trousers", "leggings"]

    for region in response.outputs[0].data.regions:
        name = region.data.concepts[0].name.lower()
        score = region.data.concepts[0].value
        box = region.region_info.bounding_box

        left = int(box.left_col * width)
        top = int(box.top_row * height)
        right = int(box.right_col * width)
        bottom = int(box.bottom_row * height)

        if any(label in name for label in top_labels) and score > top_score:
            top_region = (left, top, right, bottom)
            top_score = score

        if any(label in name for label in bottom_labels) and score > bottom_score:
            bottom_region = (left, top, right, bottom)
            bottom_score = score

    return top_region, bottom_region


@app.post("/analyze")
async def analyze_outfit(file: UploadFile = File(...)):
    # File type validation
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP images are allowed")

    # File size validation
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")

    # Use random filename to avoid conflicts
    temp_path = f"temp_{uuid.uuid4().hex}.png"
    top_path = f"temp_top_{uuid.uuid4().hex}.png"
    bottom_path = f"temp_bottom_{uuid.uuid4().hex}.png"

    try:
        with open(temp_path, "wb") as f:
            f.write(contents)

        # Validate it's actually an image
        try:
            image = Image.open(temp_path)
            image.verify()
            image = Image.open(temp_path)  # reopen after verify
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid or corrupted image file")

        width, height = image.size

        top_region, bottom_region = get_clothing_regions(temp_path)

        if top_region and bottom_region:
            cropped_top = image.crop(top_region)
            cropped_bottom = image.crop(bottom_region)
            detection_method = "clarifai"
        else:
            cropped_top = image.crop((0, 0, width, height // 2))
            cropped_bottom = image.crop((0, height // 2, width, height))
            detection_method = "fallback"

        cropped_top.save(top_path)
        cropped_bottom.save(bottom_path)

        top_palette = ColorThief(top_path).get_palette(color_count=3, quality=1)
        bottom_palette = ColorThief(bottom_path).get_palette(color_count=3, quality=1)

        top_name = get_color_name(top_palette[0])
        bottom_name = get_color_name(bottom_palette[0])

        result = do_they_match(top_palette, bottom_palette, top_name, bottom_name)

        return {
            "top_color": top_name,
            "bottom_color": bottom_name,
            "result": result,
            "detection_method": detection_method
        }

    finally:
        # Always clean up temp files even if something crashes
        for path in [temp_path, top_path, bottom_path]:
            if os.path.exists(path):
                os.remove(path)