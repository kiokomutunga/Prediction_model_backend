from fastapi import FastAPI, File, UploadFile, HTTPException
from tensorflow.keras.models import load_model
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from tensorflow.keras.preprocessing import image as keras_image
from PIL import Image, UnidentifiedImageError
from datetime import datetime, timezone


import io, os, uuid, logging


from database import get_disease_info, prediction_collection

#logging for better cache
#logs for what is going on the server
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model", "finaltomato_model.keras")
UPLOAD_DIR=os.path.join(BASE_DIR, "uploads", "predictions")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png" "webp"}
IMG_SIZE = (224, 224)
CONFIDENCE_THRESHOLD= 0.70

#class list of all diseases includes in the model
#list are mutable
CLASS_NAMES = [
    "Bacterial_spot", "Early_blight", "Late_blight", "Leaf_Mold",
    "Septoria_leaf_spot", "Spider_mites", "Target_Spot",
    "Tomato_Yellow_Leaf_Curl_Virus", "Tomato_mosaic_virus", "Healthy",
]

#ensures this folder exists and creates it it doesnt
os.makedirs(UPLOAD_DIR, exist_ok=True)

#lifespan load model once the server starts
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = load_model(MODEL_PATH)
    logger.info("model loaded successfully")
    yield
    logger.info("server shutting down")

app = FastAPI(title = "Tomato Disease Detection API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#verify the uploaded image is of the stated formats
def validate_file(filename: str) -> str:
    """reject unsupported images"""
    ext = filename.rsplit(".", 1)[-1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400,detail = f"Unsupported file type '.{ext}'. allowed: {ALLOWED_EXTENSIONS}"
        )
    return ext

#function to save the uploaded image
def save_upload(file_bytes:bytes, ext:str) -> str:
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.{ext}" )
    with open(path, "wb") as f:
        f.write(file_bytes)
    return path

#cpnvert raw images to model tensors

def preprocess(file_bytes: bytes) ->np.ndarray :
    try:
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    except UnidentifiedImageError:

        raise HTTPException(status_code=400, detail= "could not decode image")
    
    img = img.resize(IMG_SIZE)
    arr = keras_image.img_to_array(img) /255.0
    return np.expand_dims(arr, axis=0)

def run_inference(model, img_tensor:np.ndarray) -> tuple[str, float]:
    preds = model.predict(img_tensor)
    confidence = float(np.max(preds))
    cls = CLASS_NAMES[int(np.argmax(preds))]
    return cls, confidence

def log_to_db(predicted_class: str, confidence: float, image_path: str) -> None:
    """Persist a prediction record to MongoDB."""
    prediction_collection.insert_one({
        "prediction" : predicted_class,
        "confidence" : round(confidence * 100, 2),  # stored as percentage
        "image_path" : image_path,
        "timestamp"  : datetime.now(timezone.utc),  # timezone-aware UTC
    })

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    POST a tomato leaf image → get back the predicted disease.

    Returns:
        prediction    – disease name or 'Unknown'
        confidence    – model's certainty (0-1)
        image_path    – where the upload was saved
        disease_info  – treatment / symptoms from DB (None if low confidence)
    """
    # 1. Validate file type before reading anything
    ext = validate_file(file.filename)

    # 2. Read bytes once — reuse for saving AND inference
    contents = await file.read()

    # 3. Save to disk
    image_path = save_upload(contents, ext)

    # 4. Preprocess for the model
    img_tensor = preprocess(contents)

    # 5. Run inference
    predicted_class, confidence = run_inference(app.state.model, img_tensor)
    logger.info(f"Prediction: {predicted_class} ({confidence:.2%})")

    # 6. Low-confidence → return early, nothing saved to DB
    if confidence < CONFIDENCE_THRESHOLD:
        return {
            "prediction"   : "Unknown",
            "confidence"   : round(confidence, 4),
            "image_path"   : image_path,
            "disease_info" : None,
            "message"      : "Confidence too low. Please upload a clearer image of a tomato leaf.",
        }

    # 7. Save confirmed prediction to MongoDB
    log_to_db(predicted_class, confidence, image_path)

    # 8. Fetch disease details from DB  ← was a bug: missing ()
    disease_info = get_disease_info(predicted_class)

    return {
        "prediction"   : predicted_class,
        "confidence"   : round(confidence, 4),
        "image_path"   : image_path,
        "disease_info" : disease_info,
    }

