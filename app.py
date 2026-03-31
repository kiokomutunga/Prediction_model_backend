from fastapi import FastAPI, File, UploadFile, HTTPException
from tensorflow.keras.models import load_model
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from tensorflow.keras.preprocessing import image as keras_image
from PIL import Image, UnidentifiedImageError
from datetime import datetime, timezone
import io, os, uuid, logging
from fastapi.responses import JSONResponse
from bson import ObjectId
from fastapi.staticfiles import StaticFiles

from database import get_disease_info, prediction_collection,get_all_diseases
from routers.stats import router as stats_router    # ← added


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# config
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model", "twolayer.keras")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "predictions")
UPLOADS_ROOT = os.path.join(BASE_DIR, "uploads")

ALLOWED_EXTENSIONS   = {"jpg", "jpeg", "png", "webp"}
IMG_SIZE             = (256, 256)       
CONFIDENCE_THRESHOLD = 0.70            

CRITICAL_DISEASES = {                  
    "Late_blight",
    "Tomato_Yellow_Leaf_Curl_Virus",
}

CLASS_NAMES = [
    "Bacterial_spot", "Early_blight", "Late_blight", "Leaf_Mold",
    "Septoria_leaf_spot", "Spider_mites", "Target_Spot",
    "Tomato_Yellow_Leaf_Curl_Virus", "Tomato_mosaic_virus", "Healthy",
]

os.makedirs(UPLOAD_DIR, exist_ok=True)

#Lifespan load model once at startup 
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = load_model(MODEL_PATH, compile=False)   # ← added compile=False
    logger.info("Model loaded successfully.")
    yield
    logger.info("Server shutting down.")

#App
app = FastAPI(title="Tomato Disease Detection API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=UPLOADS_ROOT), name="uploads")

#Register routers
app.include_router(stats_router)

#Helpers

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
    filename = f"{uuid.uuid4()}.{ext}"
    full_path = os.path.join(UPLOAD_DIR, filename)
    with open(full_path, "wb") as f:
        f.write(file_bytes)
    return f"uploads/predictions/{filename}"


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

#Predict endpoint

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
            "image_path"   : None,
            "disease_info" : None,
            "message"      : "Confidence too low. Please upload a clearer image of a tomato leaf./ confirm whether its a tomato leaf",
        }

    # 7. Save confirmed prediction to MongoDB
    image_path = save_upload(contents, ext)
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

@app.get("/diseases/")
async def fetch_diseases():
        
    try:
        diseases = get_all_diseases()
        return{
            "count": len(diseases),
            "diseases":diseases
            }
    except Exception as e:
        logger.error(f"error fetching diseases {str(e)}")
        raise HTTPException(status_code = 400, detail= "failed to fetch diseases")



@app.get("/history/scans")
async def get_scan_history(limit: int = 50):
    try:
        scans_cursor = prediction_collection.find().sort("timestamp", -1).limit(limit)

        scans = []
        for scan in scans_cursor:
            raw_path = scan["image_path"]
            if os.path.isabs(raw_path) or "\\" in raw_path:
                filename = os.path.basename(raw_path)
                image_path = f"uploads/predictions/{filename}"
            else:
                image_path = raw_path 

            scans.append({
                "_id": str(scan["_id"]),
                "prediction": scan["prediction"],
                "confidence": scan["confidence"],
                "timestamp": scan["timestamp"].isoformat(),
                "image_path": image_path,
                "is_critical": scan.get("is_critical", False),
            })

        total = prediction_collection.count_documents({})
        return JSONResponse({"total": total, "scans": scans})

    except Exception as e:
        logger.error(f"Error fetching scan history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch scan history")