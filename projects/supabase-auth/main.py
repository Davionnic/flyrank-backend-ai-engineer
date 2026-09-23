import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI(
    title="FlyRank BE-03 Auth API",
    description="Authentication system using FastAPI and Supabase with Bearer token authentication",
    version="1.0.0"
)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

supabase: Client = create_client(supabase_url, supabase_key)

# Security
security = HTTPBearer()

# Pydantic models
class UserSignup(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Auth middleware dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Reusable FastAPI dependency for authentication.
    Validates Bearer token and returns the current user.
    """
    try:
        if not credentials or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token required"
            )
        
        # Verify token with Supabase
        response = supabase.auth.get_user(credentials.credentials)
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        return response.user
    except Exception as e:
        error_message = str(e).lower()
        if "invalid" in error_message or "expired" in error_message or "unauthorized" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token required"
        )

@app.get("/")
async def root():
    return {"message": "FlyRank BE-03 Auth API is running"}

# Auth routes
@app.post("/auth/signup", 
         status_code=status.HTTP_201_CREATED,
         summary="User Registration",
         description="Create a new user account with email and password")
async def signup(user_data: UserSignup):
    try:
        # Check if email and password are provided
        if not user_data.email or not user_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        
        # Sign up user with Supabase
        response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        
        if response.user:
            return {
                "message": "User created successfully",
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "created_at": response.user.created_at
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
    except Exception as e:
        # Handle Supabase errors
        error_message = str(e)
        if "already registered" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

@app.post("/auth/login", 
         status_code=status.HTTP_200_OK,
         summary="User Login",
         description="Authenticate user and receive access tokens")
async def login(user_data: UserLogin):
    try:
        # Check if email and password are provided
        if not user_data.email or not user_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        
        # Sign in user with Supabase
        response = supabase.auth.sign_in_with_password({
            "email": user_data.email,
            "password": user_data.password
        })
        
        if response.user and response.session:
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": {
                    "id": response.user.id,
                    "email": response.user.email
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid login credentials"
            )
    except Exception as e:
        # Handle Supabase auth errors
        error_message = str(e)
        if "invalid" in error_message.lower() or "credentials" in error_message.lower():
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Invalid login credentials"}
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

@app.post("/auth/logout", 
         status_code=status.HTTP_204_NO_CONTENT,
         summary="User Logout",
         description="Sign out the current user (requires Bearer token)")
async def logout(current_user=Depends(get_current_user)):
    try:
        # Sign out user from Supabase
        supabase.auth.sign_out()
        return None  # 204 No Content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout"
        )

# Public routes
@app.get("/public/info",
         summary="Public Information",
         description="Get public information - no authentication required")
async def public_info():
    return {"message": "Welcome stranger! This info is public."}

# Protected routes with proper token verification
@app.get("/protected/profile",
         summary="User Profile",
         description="Get current user profile information (requires Bearer token)")
async def get_profile(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at
    }

@app.get("/protected/dashboard",
         summary="User Dashboard", 
         description="Access user dashboard (requires Bearer token)")
async def get_dashboard(current_user=Depends(get_current_user)):
    return {
        "message": "Welcome to your dashboard!",
        "user_id": current_user.id,
        "email": current_user.email
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)