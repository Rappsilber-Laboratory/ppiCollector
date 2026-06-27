from fastapi import FastAPI,APIRouter,HTTPException
from pydantic import BaseModel,EmailStr
from app.supabase_client import supabase

class AuthCredentials(BaseModel):
    email:EmailStr
    password:str

app=FastAPI()

@app.post("/signup")
def sign_up(credentials:AuthCredentials):
    response=supabase.auth.sign_up({'email':credentials.email,'password':credentials.password})
    if(response.user==None):
        raise HTTPException(status_code=400,detail="signup failed")
    return {"message":"SignUp successful, please verify your email"}

@app.post("/login")
def login(credentials:AuthCredentials):
    response=supabase.auth.sign_in_with_password({'email':credentials.email,'password':credentials.password})

    if(response.user==None):
        raise HTTPException(status_code=401,detail="Invalid Credentials")
    return{
        "access_token":response.session.access_token,
        "token_type":"bearer",
    }

@app.post('/logout')
def logout(token:str):
    supabase.auth.sign_out(token)
    return {"message":"SignedOut successfully"}
    

