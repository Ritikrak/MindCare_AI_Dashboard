from functools import lru_cache
from pathlib import Path
from typing import Literal

import joblib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "Mental_Health_Model.pkl"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class StudentData(BaseModel):
    age: int = Field(..., ge=10, le=100)
    gender: Literal["Male", "Female"]
    country: str
    academic_level: Literal["Undergraduate", "Graduate", "High School"]
    most_used_platform: Literal[
        "Facebook",
        "LinkedIn",
        "Instagram",
        "Snapchat",
        "Twitter",
        "YouTube",
        "TikTok",
        "LINE",
        "KakaoTalk",
        "VKontakte",
        "WhatsApp",
        "WeChat",
    ]
    purpose_of_use: Literal["Networking", "Education", "Entertainment", "News"]
    avg_daily_usage_hours: float = Field(..., ge=0, le=24)
    daily_unlocks: int = Field(..., ge=0)
    study_hours: float = Field(..., ge=0, le=24)
    physical_activity_hours: float = Field(..., ge=0, le=24)
    sleep_hours_per_night: float = Field(..., ge=0, le=24)
    stress_level: Literal["Medium", "Low", "Very High", "High"]


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)


@app.get("/")
def serve_ui():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
def serve_favicon():
    return FileResponse(BASE_DIR / "static" / "favicon.svg", media_type="image/svg+xml")


@app.post("/predict")
def predict(data: StudentData):
    model = load_model()
    payload = {
        "age": data.age,
        "gender": data.gender,
        "country": data.country,
        "academic_level": data.academic_level,
        "most_used_platform": data.most_used_platform,
        "purpose_of_use": data.purpose_of_use,
        "avg_daily_usage_hours": data.avg_daily_usage_hours,
        "daily_unlocks": data.daily_unlocks,
        "study_hours": data.study_hours,
        "physical_activity_hours": data.physical_activity_hours,
        "sleep_hours_per_night": data.sleep_hours_per_night,
        "stress_level": data.stress_level,
    }
    prediction = model.predict(payload)
    return {"mental_health_score": float(prediction)}
