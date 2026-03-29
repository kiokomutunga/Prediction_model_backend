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
from routers.stats import router as stats_router    # ← added


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model", "twolayer.keras")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "predictions")

ALLOWED_EXTENSIONS   = {"jpg", "jpeg", "png", "webp"}
IMG_SIZE             = (256, 256)        # ← fixed from 224 to match your model
CONFIDENCE_THRESHOLD = 0.70             # ← fixed from 0.905 — too strict

CRITICAL_DISEASES = {                   # ← added for stats tracking
    "Late_blight",
    "Tomato_Yellow_Leaf_Curl_Virus",
}

CLASS_NAMES = [
    "Bacterial_spot", "Early_blight", "Late_blight", "Leaf_Mold",
    "Septoria_leaf_spot", "Spider_mites", "Target_Spot",
    "Tomato_Yellow_Leaf_Curl_Virus", "Tomato_mosaic_virus", "Healthy",
]

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── Lifespan — load model once at startup ────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = load_model(MODEL_PATH, compile=False)   # ← added compile=False
    logger.info("Model loaded successfully.")
    yield
    logger.info("Server shutting down.")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Tomato Disease Detection API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ──────────────────────────────────────────────────────────
app.include_router(stats_router)        # ← added — mounts all /stats/* routes

# ── Helpers ───────────────────────────────────────────────────────────────────

def validate_file(filename: str) -> str:
    """Reject unsupported file types."""
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Allowed: {ALLOWED_EXTENSIONS}",
        )
    return ext


def save_upload(file_bytes: bytes, ext: str) -> str:
    """Save raw bytes to disk and return the saved path."""
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.{ext}")
    with open(path, "wb") as f:
        f.write(file_bytes)
    return path


def preprocess(file_bytes: bytes) -> np.ndarray:
    """Convert raw image bytes into model-ready tensor."""
    try:
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Could not decode image.")

    img = img.resize(IMG_SIZE)
    arr = keras_image.img_to_array(img) / 255.0
    return np.expand_dims(arr, axis=0)


def run_inference(model, img_tensor: np.ndarray) -> tuple[str, float]:
    """Run model and return (class_name, confidence)."""
    preds      = model.predict(img_tensor)
    confidence = float(np.max(preds))
    cls        = CLASS_NAMES[int(np.argmax(preds))]
    return cls, confidence


def log_to_db(predicted_class: str, confidence: float, image_path: str) -> str:
    """Persist prediction to MongoDB and return the inserted ID."""
    result = prediction_collection.insert_one({
        "prediction"  : predicted_class,
        "confidence"  : round(confidence * 100, 2),
        "image_path"  : image_path,
        "timestamp"   : datetime.now(timezone.utc),
        "is_critical" : predicted_class in CRITICAL_DISEASES,  # ← added
    })
    return str(result.inserted_id)

# ── Predict endpoint ──────────────────────────────────────────────────────────

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    POST a tomato leaf image → get back the predicted disease.

    Returns:
        _id          – MongoDB document ID for feedback linking
        prediction   – disease name or 'Unknown'
        confidence   – model certainty (0-1)
        image_path   – where the upload was saved
        disease_info – treatment/symptoms from DB
        is_critical  – true if disease needs urgent attention
    """
    # 1. Validate file type before reading anything
    ext = validate_file(file.filename)

    # 2. Read bytes once — reused for saving AND inference
    contents = await file.read()

    # 3. Save to disk
    image_path = save_upload(contents, ext)

    # 4. Preprocess for the model
    img_tensor = preprocess(contents)

    # 5. Run inference
    predicted_class, confidence = run_inference(app.state.model, img_tensor)
    logger.info(f"Prediction: {predicted_class} ({confidence:.2%})")

    # 6. Low confidence — return early, nothing saved to DB
    if confidence < CONFIDENCE_THRESHOLD:
        return {
            "prediction"   : "Unknown",
            "confidence"   : round(confidence, 4),
            "image_path"   : image_path,
            "disease_info" : None,
            "message"      : "Confidence too low. Please upload a clearer image of a tomato leaf.",
        }

    # 7. Save confirmed prediction to MongoDB
    prediction_id = log_to_db(predicted_class, confidence, image_path)

    # 8. Fetch disease details from DB
    disease_info = get_disease_info(predicted_class)

    return {
        "_id"          : prediction_id,
        "prediction"   : predicted_class,
        "confidence"   : round(confidence, 4),
        "image_path"   : image_path,
        "disease_info" : disease_info,
        "is_critical"  : predicted_class in CRITICAL_DISEASES,
    }


