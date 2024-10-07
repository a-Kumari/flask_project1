import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:root@localhost:5432/flask_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    SECRET_KEY = 'a7f8e9c2c89d4d5f9b3c13b5e1c44bfb' 
