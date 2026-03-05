from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from app.database import SessionLocal
from app.models.user_models import User
from app.core.security import hash_password, verify_password, create_token, decode_token

router = APIRouter()

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = "Admin"
    role: str = "operator"

class LoginRequest(BaseModel):
    email: str
    password: str

def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

@router.post("/register")
def register(req: RegisterRequest):
    db = SessionLocal()
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=req.email, hashed_password=hash_password(req.password), name=req.name, role=req.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    token = create_token({"user_id": user.id, "email": user.email, "role": user.role, "name": user.name})
    return {"token": token, "user": {"id": user.id, "email": user.email, "name": user.name, "role": user.role}}

@router.post("/login")
def login(req: LoginRequest):
    db = SessionLocal()
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        db.close()
        raise HTTPException(status_code=401, detail="Invalid email or password")
    db.close()
    token = create_token({"user_id": user.id, "email": user.email, "role": user.role, "name": user.name})
    return {"token": token, "user": {"id": user.id, "email": user.email, "name": user.name, "role": user.role}}

@router.get("/me")
def get_me(user=Depends(get_current_user)):
    return user
