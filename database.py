import mysql.connector
from mysql.connector import Error
from config import Config

class Database:
    def __init__(self):
        self.config = {
            'host': Config.DB_HOST,
            'database': Config.DB_NAME,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'port': Config.DB_PORT
        }
    
    def get_connection(self):
        try:
            connection = mysql.connector.connect(**self.config)
            return connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None
    
    def create_users_table(self):
        connection = self.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                create_table_query = """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                cursor.execute(create_table_query)
                connection.commit()
                print("Users table created successfully")
            except Error as e:
                print(f"Error creating table: {e}")
            finally:
                cursor.close()
                connection.close()