import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', "dev")
    CARTOLA_API_URL = os.getenv("CARTOLA_API_URL")