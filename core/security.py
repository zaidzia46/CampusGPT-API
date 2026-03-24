from fastapi import Body, Depends, HTTPException, APIRouter, status
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from config import SECRET_KEY, ACCESS_TOKEN_EXPIRY, REFRESH_TOKEN_EXPIRE_DAYS, ALGORITHM

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

#----------------------password hashing and verification-----------------------

def password_hashing(password: str):
    return pwd_context.hash(password)

def verify_password(user_password, hashed_password):
    return pwd_context.verify(user_password, hashed_password)

#-----------------------JWT-access-token creation------------------------

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRY)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

#-----------------------JWT-access-token verification------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload['sub']
        role = payload['role']

        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User don't exist")
        
        return {'user_id': user_id, 'role': role}
    
    except JWTError as e:
        print("JWT DECODE ERROR access >>>", repr(e))
        raise HTTPException(status_code=401, detail=str(e))
    

#-----------------------JWT-refresh-token creation------------------------
def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({'exp': expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return token

router = APIRouter()
@router.post('/refresh')
def refresh_token(refresh_token: str = Body(...)):
    try:
        payload = jwt.decode(token=refresh_token, key=SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload['sub']
        role = payload['role']

        if user_id is None or role is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid Refresh token')
        
        new_access_token = create_access_token({'sub': user_id, 'role': role})
        return {"access_token": new_access_token, "token_type": "bearer"}
    
    except JWTError as e:
        print("JWT DECODE ERROR refresh >>>", repr(e))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))