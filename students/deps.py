from fastapi import Depends, HTTPException, status
from core.security import get_current_user

def get_current_student(user: dict = Depends(get_current_user)):
    if user['role'] != 'student' and user['role'] != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized')
    return user