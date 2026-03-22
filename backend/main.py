import numpy as np
import joblib
import torch
import torch.nn as nn
import parselmouth
from parselmouth.praat import call
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import tempfile, os
import hashlib
import json
from datetime import datetime

from fusion import fuse_scores, ModalityScore
from baseline import save_session, get_baseline_for_fusion, get_history

# ── User auth helpers ─────────────────────────────────────────────────────────
USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Parkinson's Biomarker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── LSTM model definition ─────────────────────────────────────────────────────
class GaitLSTM(nn.Module):
    def __init__(self, input_size=16, hidden_size=64, num_layers=2, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size, hidden_size=hidden_size,
            num_layers=num_layers, batch_first=True, dropout=dropout
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    def forward(self, x):
        _, (h_n, _) = self.lstm(x)
        return self.classifier(h_n[-1])

# ── Load models ───────────────────────────────────────────────────────────────
print("Loading models...")
voice_model    = joblib.load('models/voice_model.pkl')
voice_scaler   = joblib.load('models/voice_scaler.pkl')
voice_features = joblib.load('models/voice_features.pkl')

tremor_model  = joblib.load('models/tremor_model.pkl')
tremor_scaler = joblib.load('models/tremor_scaler.pkl')

gait_scaler = joblib.load('models/gait_scaler.pkl')
gait_model  = GaitLSTM(input_size=16)
gait_model.load_state_dict(torch.load('models/gait_model.pt', map_location='cpu'))
gait_model.eval()
print("All models loaded.")

# ── Pydantic schemas ──────────────────────────────────────────────────────────
class TremorData(BaseModel):
    user_id: str
    samples: List[List[float]]

class GaitData(BaseModel):
    user_id: str
    samples: List[List[float]]

class TappingData(BaseModel):
    user_id: str
    intervals_ms: List[float]

class FusionRequest(BaseModel):
    user_id: str
    voice:   Optional[float] = None
    tremor:  Optional[float] = None
    gait:    Optional[float] = None
    tapping: Optional[float] = None

class RegisterRequest(BaseModel):
    name:     str
    email:    str
    password: str
    age:      int
    gender:   str

class LoginRequest(BaseModel):
    email:    str
    password: str

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "models_loaded": True}

# ── Frontend ──────────────────────────────────────────────────────────────────
@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")

# ── Auth endpoints ────────────────────────────────────────────────────────────
@app.post("/auth/register")
async def register(req: RegisterRequest):
    users = load_users()
    if req.email in users:
        raise HTTPException(400, "Email already registered")
    users[req.email] = {
        "name":     req.name,
        "email":    req.email,
        "password": hash_password(req.password),
        "age":      req.age,
        "gender":   req.gender,
        "joined":   datetime.utcnow().isoformat()[:10],
    }
    save_users(users)
    return {
        "success": True,
        "user_id": req.email,
        "name":    req.name,
        "email":   req.email,
        "age":     req.age,
        "gender":  req.gender,
    }

@app.post("/auth/login")
async def login(req: LoginRequest):
    users = load_users()
    user = users.get(req.email)
    if not user or user['password'] != hash_password(req.password):
        raise HTTPException(401, "Invalid email or password")
    return {
        "success": True,
        "user_id": req.email,
        "name":    user['name'],
        "email":   user['email'],
        "age":     user['age'],
        "gender":  user['gender'],
    }

@app.get("/auth/profile/{user_id}")
async def profile(user_id: str):
    users = load_users()
    user = users.get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return {
        "name":   user['name'],
        "email":  user['email'],
        "age":    user['age'],
        "gender": user['gender'],
        "joined": user['joined'],
    }

# ── Voice endpoint ────────────────────────────────────────────────────────────
@app.post("/predict/voice")
async def predict_voice(user_id: str, file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        sound = parselmouth.Sound(tmp_path)
        harmonicity   = call(sound, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0)
        hnr           = call(harmonicity, "Get mean", 0, 0)
        pitch         = call(sound, "To Pitch", 0.0, 75, 600)
        f0_mean       = call(pitch, "Get mean", 0, 0, "Hertz")
        f0_std        = call(pitch, "Get standard deviation", 0, 0, "Hertz")
        pp            = call(sound, "To PointProcess (periodic, cc)", 75, 600)
        jitter_local  = call(pp, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
        jitter_abs    = call(pp, "Get jitter (local, absolute)", 0, 0, 0.0001, 0.02, 1.3)
        jitter_rap    = call(pp, "Get jitter (rap)", 0, 0, 0.0001, 0.02, 1.3)
        jitter_ppq5   = call(pp, "Get jitter (ppq5)", 0, 0, 0.0001, 0.02, 1.3)
        shimmer_local = call([sound, pp], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
        shimmer_db    = call([sound, pp], "Get shimmer (local, dB)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
        shimmer_apq3  = call([sound, pp], "Get shimmer (apq3)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
        shimmer_apq5  = call([sound, pp], "Get shimmer (apq5)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
        shimmer_apq11 = call([sound, pp], "Get shimmer (apq11)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
        nhr = 1 / hnr if hnr and hnr > 0 else 0

        features = np.array([[
            f0_mean or 0, f0_std or 0, 0, 0,
            jitter_local or 0, jitter_abs or 0, jitter_rap or 0,
            jitter_ppq5 or 0, (jitter_rap or 0) * 3,
            shimmer_local or 0, shimmer_db or 0, shimmer_apq3 or 0,
            shimmer_apq5 or 0, shimmer_apq11 or 0, (shimmer_apq3 or 0) * 3,
            nhr, hnr or 0,
            0, 0, 0, 0, 0
        ]])
        features_scaled = voice_scaler.transform(features)
        prob = float(voice_model.predict_proba(features_scaled)[0][1])
        return {"probability": prob, "modality": "voice"}
    finally:
        os.unlink(tmp_path)

# ── Tremor endpoint ───────────────────────────────────────────────────────────
@app.post("/predict/tremor")
async def predict_tremor(data: TremorData):
    samples = np.array(data.samples)
    if samples.shape[0] < 192:
        raise HTTPException(400, "Need at least 192 samples")
    window = samples[-192:]
    feats = []
    for col in range(window.shape[1]):
        sig = window[:, col]
        feats += [
            np.mean(sig), np.std(sig), np.min(sig), np.max(sig),
            np.max(sig) - np.min(sig),
            np.sqrt(np.mean(sig**2)),
            np.sum(np.abs(np.diff(sig))),
            np.mean(np.abs(sig - np.mean(sig))),
        ]
    X = tremor_scaler.transform(np.array([feats]))
    prob = float(tremor_model.predict_proba(X)[0][1])
    return {"probability": prob, "modality": "tremor"}

# ── Gait endpoint ─────────────────────────────────────────────────────────────
@app.post("/predict/gait")
async def predict_gait(data: GaitData):
    samples = np.array(data.samples, dtype=np.float32)
    if samples.shape[0] < 100:
        raise HTTPException(400, "Need at least 100 samples")
    window = samples[-100:]
    if window.shape[1] < 16:
        pad = np.zeros((window.shape[0], 16 - window.shape[1]), dtype=np.float32)
        window = np.hstack([window, pad])
    flat   = window.reshape(-1, 16)
    flat_s = gait_scaler.transform(flat)
    tensor = torch.FloatTensor(flat_s.reshape(1, 100, 16))
    with torch.no_grad():
        prob = float(gait_model(tensor).squeeze())
    return {"probability": prob, "modality": "gait"}

# ── Tapping endpoint ──────────────────────────────────────────────────────────
@app.post("/predict/tapping")
async def predict_tapping(data: TappingData):
    intervals = np.array(data.intervals_ms)
    if len(intervals) < 10:
        raise HTTPException(400, "Need at least 10 taps")
    mean_iti = np.mean(intervals)
    std_iti  = np.std(intervals)
    cv       = std_iti / mean_iti if mean_iti > 0 else 0
    rhythm   = np.mean(np.abs(np.diff(intervals)))
    score = 0.0
    if mean_iti > 600: score += 0.30
    if mean_iti > 800: score += 0.20
    if cv > 0.20:      score += 0.25
    if cv > 0.35:      score += 0.15
    if rhythm > 50:    score += 0.10
    prob = min(1.0, score)
    return {
        "probability": prob,
        "modality": "tapping",
        "stats": {
            "mean_iti_ms":         round(float(mean_iti), 1),
            "cv":                  round(float(cv), 3),
            "rhythm_irregularity": round(float(rhythm), 1),
        }
    }

# ── Fusion endpoint ───────────────────────────────────────────────────────────
@app.post("/predict/fuse")
async def fuse(req: FusionRequest):
    scores = ModalityScore(
        voice=req.voice, tremor=req.tremor,
        gait=req.gait,   tapping=req.tapping
    )
    baseline = get_baseline_for_fusion(req.user_id)
    result   = fuse_scores(scores, baseline)
    save_session(req.user_id, result.raw_score, result.modality_scores)
    return {
        "risk_score":      result.raw_score,
        "risk_level":      result.risk_level,
        "modality_scores": result.modality_scores,
        "advice":          result.advice,
        "confidence":      result.confidence,
        "baseline_active": baseline is not None,
    }

# ── History endpoint ──────────────────────────────────────────────────────────
@app.get("/history/{user_id}")
async def history(user_id: str):
    return {"history": get_history(user_id)}

# ── Static files (must be last) ───────────────────────────────────────────────
app.mount("/screens", StaticFiles(directory="frontend/screens"), name="screens")
app.mount("/", StaticFiles(directory="frontend"), name="static")