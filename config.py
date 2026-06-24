
import os

class Config:
    SECRET_KEY = 'dev-secret-key-change-in-production'
    DATABASE = os.path.join(os.path.dirname(__file__), 'fams.db')
    DEBUG = True