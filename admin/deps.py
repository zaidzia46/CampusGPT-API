from fastapi import Depends, HTTPException, status
from core.security import get_current_user

def get_current_admin(user: dict = Depends(get_current_user)):
    if user['role'] != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Bad Request 401')
    return user