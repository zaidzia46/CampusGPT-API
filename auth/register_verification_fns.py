import random
from datetime import datetime, timedelta

def generate_otp(length=6):
    digits = "0123456789"
    otp = "".join(random.choice(digits) for _ in range(length))
    return otp

otp_store = {}
def save_otp(email, otp):
    expiry_time = datetime.now() + timedelta(minutes=2)
    otp_store[email] = (otp, expiry_time)

def verify_otp(email, otp):
    if email not in otp_store:
        return False

    stored_otp, expiry_time = otp_store[email]

    if datetime.now() > expiry_time:
        del otp_store[email]
        return False

    if stored_otp == otp:
        del otp_store[email]
        return True

    return False