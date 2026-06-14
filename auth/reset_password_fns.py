from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from config import BREVO_API_KEY, SECRET_KEY, ALGORITHM, RESEND_API_KEY
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

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
    api_key = BREVO_API_KEY
    if not api_key:
        raise ValueError("BREVO_API_KEY is not set in environment variables.")

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        sender={"name": "CampusGPT", "email": "zaidzia46@gmail.com"},
        to=[{"email": to}],
        subject=subject,
        text_content=body,
    )

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print(f"[Brevo] Error sending email: {e}")
        raise