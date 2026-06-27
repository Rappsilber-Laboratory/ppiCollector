from app.supabase_client import supabase
from fastapi import Header,HTTPException

def get_optional_user(authorization:str=Header(None)):
    if(not authorization):
        return None
    try:
        token=authorization.split(" ")
        user=supabase.auth.get_user(token[1])
        return user.user
    except:
        return None

    