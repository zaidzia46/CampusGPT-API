from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
SECRET_KEY = os.getenv('SECRET_KEY')
ACCESS_TOKEN_EXPIRY=int(os.getenv('ACCESS_TOKEN_EXPIRY'))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS'))
ALGORITHM=os.getenv('ALGORITHM')
SMTP_EMAIL=os.getenv('SMTP_EMAIL')
SMTP_PASSWORD=os.getenv('SMTP_PASSWORD')