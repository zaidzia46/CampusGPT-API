from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from auth.register_verification_fns import save_otp, verify_otp, generate_otp
from config import FRONTEND_APP_URL
from core.security import password_hashing, verify_password, create_access_token, create_refresh_token
from db.session import get_db
from sqlalchemy.orm import Session
from schemas.auth import Register, ResetPasswordRequest, ResetPwd, SendOTP, VerifyOTP
from models.models import EmailVerification, UserAuth
from fastapi.security import OAuth2PasswordRequestForm
from auth.reset_password_fns import create_reset_token, send_email, verify_reset_token
from datetime import datetime, timedelta
import re

UNIVERSITY_EMAIL_REGEX = re.compile(
    r"^("
    r"(fa|sp)\d{2}-[a-z]+-\d{3}@students\.cuisahiwal\.edu\.pk"
    r"|"
    r"[a-z]+\d*@(cuisahiwal|ciitsahiwal)\.edu\.pk"
    r")$",
    re.IGNORECASE,
)

def validate_university_email(email: str) -> str:
    email = email.strip().lower()

    if not UNIVERSITY_EMAIL_REGEX.match(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid university email"
        )

    return email

def get_role_from_email(email: str) -> str:
    return "student" if "student" in email.lower() else "faculty"

router = APIRouter(
    prefix='/auth',
    tags=['Auth'],
    dependencies=[Depends(get_db)]
)

@router.post('/register')
def Register(register: Register, db = Depends(get_db)):
    email = validate_university_email(register.email)

    existing_user = db.query(UserAuth).filter(UserAuth.email == email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='User already existed')

    verification = db.query(EmailVerification).filter(
        EmailVerification.email == email,
        EmailVerification.expires_at > datetime.utcnow()
    ).first()

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Please verify your email before registering'
        )
    
    hashed_password = password_hashing(register.password)
    role = get_role_from_email(email)
    new_user = UserAuth(username=register.username, email = email, password=hashed_password, role=role)

    db.add(new_user)
    db.delete(verification)
    db.commit()
    db.refresh(new_user)

    return JSONResponse(status_code=status.HTTP_201_CREATED, content={'message': 'Account created successfully'})

@router.post('/login')
def Login(form_data: OAuth2PasswordRequestForm = Depends(), db = Depends(get_db)):
    email = validate_university_email(form_data.username)
    existing_user = db.query(UserAuth).filter(UserAuth.email == email).first()
    if existing_user is None or not verify_password(form_data.password, existing_user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Wrong email or password')

    role = existing_user.role
    if role != "admin":
        role = get_role_from_email(email)
        if existing_user.role != role:
            existing_user.role = role
            db.commit()
            db.refresh(existing_user)
    
    access_token = create_access_token({'sub': str(existing_user.id), 'role': role})
    refresh_token = create_refresh_token({'sub': str(existing_user.id), 'role': role})

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer'
    }

@router.post('/forgot-password')
def ForgotPassword(data: ResetPwd, db: Session = Depends(get_db)):
    email = validate_university_email(data.email)
    user = db.query(UserAuth).filter(UserAuth.email == email).first()

    if user:
        token = create_reset_token(user.id)
        reset_link = f"{FRONTEND_APP_URL}static-pwd-reset/forgot-password.html?token={token}"

        send_email(
            subject='Reset Password',
            body=f"Click this link to reset your password:\n{reset_link}"
        )

    return {"message": "A reset link has been sent"}

@router.post('/reset-password')
def ResetPWD(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        user_id = verify_reset_token(data.token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    user = db.query(UserAuth).filter(UserAuth.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password = password_hashing(data.new_password)
    db.commit()
    db.refresh(user) 
    return {"message": "Password reset successful"}

@router.post('/send-otp')
def SendOTP(payload: SendOTP, db: Session = Depends(get_db)):
    email = validate_university_email(payload.email)

    if db.query(UserAuth).filter(UserAuth.email == email).first():
        raise HTTPException(status_code=400, detail="User already exists with this email")

    otp = generate_otp()
    save_otp(email, otp, db)          # handles cooldown + storage
    send_email(
            subject='Your CampusGPT Verification Code',
            body=f"Your OTP is: {otp}\n\nIt expires in 60 seconds. Do not share it with anyone."
        )
    return {"message": "OTP sent to your email"}


@router.post('/verify-otp')
def VerifyOTP(payload: VerifyOTP, db: Session = Depends(get_db)):
    email = validate_university_email(payload.email)
    verify_otp(email, payload.otp, db)   # raises HTTPException on failure

    db.query(EmailVerification).filter(
        EmailVerification.email == email
    ).delete()

    verification = EmailVerification(
        email=email,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(verification)
    db.commit()

    return {"message": "OTP verified successfully"}
