from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.utils.auth import create_access_token, verify_password, get_password_hash

router = APIRouter()

# Mock database
users_db = {
    "admin": get_password_hash("password123")
}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_hash = users_db.get(form_data.username)
    if not user_hash or not verify_password(form_data.password, user_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}
