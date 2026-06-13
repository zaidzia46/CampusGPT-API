from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from config import SECRET_KEY, ALGORITHM, RESEND_API_KEY
import resend

resend.api_key = RESEND_API_KEY

def create_reset_token(user_id: int):
    payload = {
        'sub': str(user_id),
        'type': 'password_reset'
    }
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    payload.update({'exp': expires_at})

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_reset_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "password_reset":
            raise HTTPException("Invalid token type",status_code=401)

        return int(payload.get("sub"))
    
    except ExpiredSignatureError:
        raise HTTPException(detail='token expired', status_code=401)
    
    except JWTError as e:
        raise HTTPException(detail='invalid token', status_code=401)


def send_email(to_email: str, subject: str, body: str):
    resend.Emails.send({
        "from":    "CampusGPT <onboarding@resend.dev>",
        "to":      to_email,
        "subject": subject,
        "text":    body,
    })