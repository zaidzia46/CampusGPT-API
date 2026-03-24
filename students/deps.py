from fastapi import Depends, HTTPException, status
from core.security import get_current_user

def get_current_student(user: dict = Depends(get_current_user)):
    if user['role'] != 'student':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Bad Request 401')
    return user