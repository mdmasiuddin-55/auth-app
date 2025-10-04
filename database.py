import mysql.connector
from mysql.connector import Error
from config import Config
import os

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
    
    def create_tables(self):
        self.create_users_table()
        self.create_posts_table()
        self.create_likes_table()
        self.create_comments_table()
        self.create_messages_table()
        self.create_chat_sessions_table()
    
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
                    profile_picture VARCHAR(255) DEFAULT NULL,
                    bio TEXT,
                    is_online BOOLEAN DEFAULT FALSE,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                cursor.execute(create_table_query)
                connection.commit()
                print("Users table created successfully")
            except Error as e:
                print(f"Error creating users table: {e}")
            finally:
                cursor.close()
                connection.close()
    
    def create_posts_table(self):
        connection = self.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                create_table_query = """
                CREATE TABLE IF NOT EXISTS posts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    image_url VARCHAR(255) NOT NULL,
                    video_url VARCHAR(255) DEFAULT NULL,
                    caption TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
                cursor.execute(create_table_query)
                connection.commit()
                print("Posts table created successfully")
            except Error as e:
                print(f"Error creating posts table: {e}")
            finally:
                cursor.close()
                connection.close()
    
    def create_likes_table(self):
        connection = self.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                create_table_query = """
                CREATE TABLE IF NOT EXISTS likes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    post_id INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_like (user_id, post_id)
                )
                """
                cursor.execute(create_table_query)
                connection.commit()
                print("Likes table created successfully")
            except Error as e:
                print(f"Error creating likes table: {e}")
            finally:
                cursor.close()
                connection.close()
    
    def create_comments_table(self):
        connection = self.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                create_table_query = """
                CREATE TABLE IF NOT EXISTS comments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    post_id INT NOT NULL,
                    comment_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
                )
                """
                cursor.execute(create_table_query)
                connection.commit()
                print("Comments table created successfully")
            except Error as e:
                print(f"Error creating comments table: {e}")
            finally:
                cursor.close()
                connection.close()
    
    def create_chat_sessions_table(self):
        connection = self.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                create_table_query = """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user1_id INT NOT NULL,
                    user2_id INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_chat_session (user1_id, user2_id)
                )
                """
                cursor.execute(create_table_query)
                connection.commit()
                print("Chat sessions table created successfully")
            except Error as e:
                print(f"Error creating chat sessions table: {e}")
            finally:
                cursor.close()
                connection.close()
    
    def create_messages_table(self):
        connection = self.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                create_table_query = """
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    chat_session_id INT NOT NULL,
                    sender_id INT NOT NULL,
                    message_text TEXT NOT NULL,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
                cursor.execute(create_table_query)
                connection.commit()
                print("Messages table created successfully")
            except Error as e:
                print(f"Error creating messages table: {e}")
            finally:
                cursor.close()
                connection.close()