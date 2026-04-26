import hashlib
import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.models import OTPRecord

MAX_ATTEMPTS = 5
OTP_COOLDOWN_SECONDS = 60

def generate_otp() -> str:
    return str(secrets.randbelow(10**6)).zfill(6)

def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()

def save_otp(email: str, otp: str, db: Session):
    # 1. Check cooldown on the MOST RECENT record only
    recent = db.query(OTPRecord).filter(
        OTPRecord.email == email,
    ).order_by(OTPRecord.created_at.desc()).first()

    if recent:
        seconds_passed = (datetime.utcnow() - recent.created_at).total_seconds()
        if seconds_passed < OTP_COOLDOWN_SECONDS:
            remaining = int(OTP_COOLDOWN_SECONDS - seconds_passed)
            raise HTTPException(
                status_code=429,
                detail=f"Please wait {remaining} seconds before requesting another OTP"
            )

    db.query(OTPRecord).filter(OTPRecord.email == email).delete()
    db.flush()  # ensure delete is applied before insert

    # 3. Insert fresh record
    record = OTPRecord(
        email      = email,
        otp_hash   = hash_otp(otp),
        expires_at = datetime.utcnow() + timedelta(minutes=2),
        attempts   = 0,
    )
    db.add(record)
    db.commit()

def verify_otp(email: str, otp: str, db: Session) -> bool:
    record = db.query(OTPRecord).filter(OTPRecord.email == email).first()

    if not record:
        raise HTTPException(status_code=400, detail="No OTP found for this email")

    if datetime.utcnow() > record.expires_at:
        db.delete(record)
        db.commit()
        raise HTTPException(status_code=400, detail="OTP has expired")

    if record.attempts >= MAX_ATTEMPTS:
        db.delete(record)
        db.commit()
        raise HTTPException(status_code=400, detail="Too many attempts. Request a new OTP")

    if record.otp_hash != hash_otp(otp):
        record.attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail=f"Invalid OTP ({MAX_ATTEMPTS - record.attempts} attempts left)")

    # Valid — clean up
    db.delete(record)
    db.commit()
    return True