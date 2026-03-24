from pydantic import BaseModel, Field, field_validator
import re
from fastapi import HTTPException,status

UNIVERSITY_EMAIL_REGEX = re.compile(
    r"^("
    r"(fa|sp)\d{2}-[a-z]+-\d{3}@students\.cuisahiwal\.edu\.pk"
    r"|"
    r"[a-z]+\d*@(cuisahiwal|ciitsahiwal)\.edu\.pk"
    r")$",
    re.IGNORECASE,
)

class Register(BaseModel):
    username: str
    email: str
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_and_validate_email(cls, v: str) -> str:
        email = v.strip().lower()

        if not UNIVERSITY_EMAIL_REGEX.match(email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid university email")

        return email
    


class ResetPwd(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class SendOTP(BaseModel):
    email: str

class VerifyOTP(BaseModel):
    email: str
    otp: str