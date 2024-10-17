import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:root@localhost:5432/app_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = '' 
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = ''
    MAIL_PASSWORD = ''
    MAIL_DEFAULT_SENDER = ''

