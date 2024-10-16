import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:root@localhost:5432/app_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'a7f8e9c2c89d4d5f9b3c13b5e1c44bfb' 
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'a6974kumari@gmail.com'
    MAIL_PASSWORD = 'uagwhwggqfowical'
    MAIL_DEFAULT_SENDER = 'a6974kumari@gmail.com'

