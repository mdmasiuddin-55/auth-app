import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # AWS RDS MySQL Configuration
    DB_HOST = os.getenv('DB_HOST', 'your-rds-endpoint.rds.amazonaws.com')
    DB_USER = os.getenv('DB_USER', 'your-username')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'your-password')
    DB_NAME = os.getenv('DB_NAME', 'auth_database')
    DB_PORT = os.getenv('DB_PORT', '3306')
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')