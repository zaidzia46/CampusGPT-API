from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from config import SECRET_KEY, ALGORITHM, SMTP_EMAIL, SMTP_PASSWORD
from email.message import EmailMessage
from email.utils import formataddr
import smtplib

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
    


def send_email(to: str, subject: str, body: str):
    msg = EmailMessage()
    msg['From'] = formataddr(('CampusGPT', SMTP_EMAIL))
    msg['To'] = to
    msg['Subject'] = subject
    msg.set_content(body)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)