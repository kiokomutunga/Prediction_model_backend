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
from groq import Groq
from dotenv import load_dotenv
from ollama import chat as ollama_chat

from database import get_disease_info, prediction_collection, get_all_diseases,  get_disease_for_scan,    get_chat_by_scan, chat_collection
from routers.stats import router as stats_router
load_dotenv()
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
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
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
        _id          MongoDB document ID for feedback linking
        prediction   disease name or 'Unknown'
        confidence   model certainty (0-1)
        image_path   where the upload was saved
        disease_info treatment/symptoms from DB
        is_critical  true if disease needs urgent attention
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
@app.get("/diseases/{key}")
async def fetch_disease_by_key(key: str):
    """Fetch a single disease by its key e.g. Early_blight, Healthy"""
    try:
        disease = get_disease_info(key)
        if not disease:
            raise HTTPException(status_code=404, detail=f"Disease '{key}' not found in database.")
        return disease
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching disease {key}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch disease")
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

            chat_exists = prediction_collection.database["chat_sessions"].count_documents({
            "scan_id": str(scan["_id"])
        }) > 0

            scans.append({
                "_id": str(scan["_id"]),
                "prediction": scan["prediction"],
                "confidence": scan["confidence"],
                "timestamp": scan["timestamp"].isoformat(),
                "image_path": image_path,
                "is_critical": scan.get("is_critical", False),
                "has_chat": chat_exists ,
            })

        total = prediction_collection.count_documents({})
        return JSONResponse({"total": total, "scans": scans})

    except Exception as e:
        logger.error(f"Error fetching scan history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch scan history")
@app.post("/chat")
async def chat_endpoint(req: dict):
    messages    = req.get("messages", [])
    disease_ctx = req.get("diseaseContext")
    session_id  = req.get("sessionId")
    scan_id     = req.get("scanId")

    # Fetch disease context from DB if not provided
    if not disease_ctx and scan_id:
        try:
            scan = prediction_collection.find_one({"_id": ObjectId(scan_id)})
            if scan:
                disease_info = get_disease_for_scan(scan["prediction"])
                disease_ctx  = {
                    "prediction"  : scan["prediction"],
                    "confidence"  : scan["confidence"] / 100,
                    "disease_info": disease_info,
                }
        except Exception:
            pass

    # Build system prompt
    if disease_ctx:
        system = f"""You are an expert tomato disease assistant helping farmers and agronomists.
The AI model detected:
- Disease: {disease_ctx.get('prediction', 'N/A')}
- Confidence: {disease_ctx.get('confidence', 0) * 100:.1f}%
- Description: {(disease_ctx.get('disease_info') or {}).get('description', 'N/A')}
- Symptoms: {(disease_ctx.get('disease_info') or {}).get('symptoms', 'N/A')}
- Treatment: {(disease_ctx.get('disease_info') or {}).get('treatment', 'N/A')}
- Prevention: {(disease_ctx.get('disease_info') or {}).get('prevention', 'N/A')}

Rules:
- Give practical, actionable farming advice
- Keep responses under 150 words
- Use simple language a farmer understands
- If asked something unrelated to tomatoes, politely redirect"""
    else:
        system = """You are a helpful tomato disease expert assistant.
No image has been analysed yet. You can answer general tomato disease questions.
Encourage the user to upload a tomato leaf image for a specific diagnosis.
Keep responses under 150 words."""

    # Build messages for Groq — filter out system role from history
    groq_messages = []
    for m in messages:
        if m.get("role") in ("user", "assistant") and m.get("content", "").strip():
            groq_messages.append({
                "role"   : m["role"],
                "content": m["content"],
            })

    try:
        response = groq_client.chat.completions.create(
            model      = "llama-3.3-70b-versatile",   # fast, free, good quality
            messages   = [{"role": "system", "content": system}] + groq_messages,
            max_tokens = 512,
            temperature= 0.7,
        )
        reply = response.choices[0].message.content

    except Exception as e:
        logger.error(f"Groq error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat model error: {str(e)}")

    # Save to MongoDB
    try:
        chat_collection.update_one(
            {"session_id": session_id},
            {
                "$set"        : {
                    "updated_at"      : datetime.now(timezone.utc),
                    "disease_context" : disease_ctx,
                    "scan_id"         : scan_id,
                },
                "$push"       : {
                    "messages": {
                        "$each": [
                            messages[-1],
                            {"role": "assistant", "content": reply},
                        ]
                    }
                },
                "$setOnInsert": {
                    "session_id": session_id,
                    "created_at": datetime.now(timezone.utc),
                },
            },
            upsert=True,
        )
    except Exception as e:
        logger.warning(f"Chat save warning: {e}")

    return {"reply": reply}
@app.get("/chat/by-scan/{scan_id}")
async def get_chat_by_scan_endpoint(scan_id: str):
    """Return existing chat messages for a scan."""
    session = get_chat_by_scan(scan_id)
    if not session:
        return {"messages": [], "has_chat": False}
    return {"messages": session.get("messages", []), "has_chat": True}

@app.get("/chat/history")
async def chat_history(sessionId: str = None):
    db = chat_collection.database

    if sessionId:
        session = chat_collection.find_one({"session_id": sessionId})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session["_id"] = str(session["_id"])
        # normalize dates
        if "created_at" in session:
            session["created_at"] = session["created_at"].isoformat()
        if "updated_at" in session:
            session["updated_at"] = session["updated_at"].isoformat()
        return session
    sessions = list(chat_collection.find().sort("updated_at", -1).limit(20))
    result = []
    for s in sessions:
        s["_id"] = str(s["_id"])
        # normalize for frontend
        s["sessionId"]  = s.get("session_id", "")
        s["createdAt"]  = s["created_at"].isoformat()  if s.get("created_at")  else None
        s["updatedAt"]  = s["updated_at"].isoformat()  if s.get("updated_at")  else None
        result.append(s)
    return result
@app.delete("/history/scans/{scan_id}")
async def delete_scan(scan_id: str):
    try:
        obj_id = ObjectId(scan_id)

        scan = prediction_collection.find_one({"_id": obj_id})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")

        # delete image
        image_path = scan.get("image_path")
        if image_path:
            full_path = os.path.join(BASE_DIR, image_path)
            if os.path.exists(full_path):
                os.remove(full_path)

        # delete scan
        prediction_collection.delete_one({"_id": obj_id})

        # delete chats linked to scan
        prediction_collection.database["chat_sessions"].delete_many({
            "scan_id": scan_id
        })

        return {"message": "Scan and related chat deleted successfully"}

    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete scan")