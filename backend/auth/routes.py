from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from supabase import Client
from dependencies import get_supabase
from auth.dependencies import get_current_user

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
def register(user: UserRegister, supabase: Client = Depends(get_supabase)):
    try:
        result = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {"data": {"username": user.username}}  # goes into raw_user_meta_data
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result.user:
        raise HTTPException(status_code=400, detail="Registration failed")

    return {"user_uuid": result.user.id, "username": user.username, "email": user.email}


@router.post("/login")
def login(user: UserLogin, supabase: Client = Depends(get_supabase)):
    try:
        result = supabase.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })
    except Exception as e:
        print(f"Login failed for {user.email}: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session = result.session
    profile = supabase.table("profiles").select("*").eq("id", result.user.id).maybe_single().execute()
    profile_data = profile.data or {} if profile else {}

    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "token_type": "bearer",
        "user": {
            "user_uuid": result.user.id,
            "username": profile_data.get("username"),
            "email": result.user.email
        }
    }

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user