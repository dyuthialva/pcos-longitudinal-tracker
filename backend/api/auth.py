from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["Authentication"])

MOCK_DOCTORS = [
    {
        "id": "doc-mehta",
        "name": "Dr. A. Mehta",
        "email": "dr.mehta@clinic.local",
        "role": "doctor",
        "password": "ClinicianDemo!2026",
    },
    {
        "id": "doc-rao",
        "name": "Dr. S. Rao",
        "email": "dr.rao@clinic.local",
        "role": "doctor",
        "password": "ClinicianDemo!2026",
    },
]

class LoginRequest(BaseModel):
    email: str
    password: str

class DoctorProfile(BaseModel):
    id: str
    name: str
    email: str
    role: str

class AuthSession(BaseModel):
    token: str
    doctor: DoctorProfile

@router.post("/auth/login", response_model=AuthSession)
def login(req: LoginRequest):
    email_clean = req.email.strip().lower()
    doc = next((d for d in MOCK_DOCTORS if d["email"] == email_clean and d["password"] == req.password), None)
    if not doc:
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    token = f"pcos-token-{doc['id']}"
    return AuthSession(
        token=token,
        doctor=DoctorProfile(id=doc["id"], name=doc["name"], email=doc["email"], role=doc["role"])
    )

@router.post("/auth/logout")
def logout():
    return {"message": "Logged out successfully."}

@router.get("/auth/me", response_model=DoctorProfile)
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        # Default to primary clinician for prototype demo if not passed
        doc = MOCK_DOCTORS[0]
        return DoctorProfile(id=doc["id"], name=doc["name"], email=doc["email"], role=doc["role"])
    
    token = authorization.replace("Bearer ", "")
    for doc in MOCK_DOCTORS:
        if doc["id"] in token:
            return DoctorProfile(id=doc["id"], name=doc["name"], email=doc["email"], role=doc["role"])
            
    doc = MOCK_DOCTORS[0]
    return DoctorProfile(id=doc["id"], name=doc["name"], email=doc["email"], role=doc["role"])
