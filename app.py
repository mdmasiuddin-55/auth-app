from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from database import Database
from config import Config

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize database
db = Database()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('feed'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('signup.html')
        
        password_hash = generate_password_hash(password)
        
        connection = db.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                insert_query = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
                cursor.execute(insert_query, (username, email, password_hash))
                connection.commit()
                flash('Account created successfully! Please login.', 'success')
                return redirect(url_for('login'))
            except Error as e:
                if 'Duplicate entry' in str(e):
                    flash('Username or email already exists!', 'error')
                else:
                    flash('An error occurred during registration!', 'error')
            finally:
                cursor.close()
                connection.close()
        else:
            flash('Database connection failed!', 'error')
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = db.get_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                select_query = "SELECT * FROM users WHERE username = %s OR email = %s"
                cursor.execute(select_query, (username, username))
                user = cursor.fetchone()
                
                if user and check_password_hash(user['password_hash'], password):
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    flash('Login successful!', 'success')
                    return redirect(url_for('feed'))
                else:
                    flash('Invalid username/email or password!', 'error')
            except Error as e:
                flash('An error occurred during login!', 'error')
            finally:
                cursor.close()
                connection.close()
        else:
            flash('Database connection failed!', 'error')
    
    return render_template('login.html')

@app.route('/feed')
def feed():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = db.get_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            # Get all posts with user information and like/comment counts
            cursor.execute("""
                SELECT p.*, u.username, 
                (SELECT COUNT(*) FROM likes l WHERE l.post_id = p.id) as like_count,
                (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) as comment_count,
                EXISTS(SELECT 1 FROM likes l WHERE l.post_id = p.id AND l.user_id = %s) as user_liked
                FROM posts p
                JOIN users u ON p.user_id = u.id
                ORDER BY p.created_at DESC
            """, (session['user_id'],))
            posts = cursor.fetchall()
            
            # Get comments for each post
            for post in posts:
                cursor.execute("""
                    SELECT c.*, u.username 
                    FROM comments c 
                    JOIN users u ON c.user_id = u.id 
                    WHERE c.post_id = %s 
                    ORDER BY c.created_at ASC
                """, (post['id'],))
                post['comments'] = cursor.fetchall()
                
        except Error as e:
            flash('An error occurred while loading the feed!', 'error')
            posts = []
        finally:
            cursor.close()
            connection.close()
    else:
        posts = []
    
    return render_template('feed.html', posts=posts, username=session['username'])

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        caption = request.form.get('caption', '')
        file = request.files['media']
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Determine if it's an image or video
            file_extension = filename.rsplit('.', 1)[1].lower()
            image_url = f"uploads/{filename}" if file_extension in ['png', 'jpg', 'jpeg', 'gif'] else None
            video_url = f"uploads/{filename}" if file_extension in ['mp4', 'mov', 'avi'] else None
            
            connection = db.get_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    insert_query = "INSERT INTO posts (user_id, image_url, video_url, caption) VALUES (%s, %s, %s, %s)"
                    cursor.execute(insert_query, (session['user_id'], image_url, video_url, caption))
                    connection.commit()
                    flash('Post created successfully!', 'success')
                    return redirect(url_for('feed'))
                except Error as e:
                    flash('An error occurred while creating the post!', 'error')
                finally:
                    cursor.close()
                    connection.close()
        else:
            flash('Please select a valid image or video file!', 'error')
    
    return render_template('create_post.html')

@app.route('/like_post/<int:post_id>', methods=['POST'])
def like_post(post_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    connection = db.get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Check if already liked
            cursor.execute("SELECT id FROM likes WHERE user_id = %s AND post_id = %s", 
                         (session['user_id'], post_id))
            existing_like = cursor.fetchone()
            
            if existing_like:
                # Unlike
                cursor.execute("DELETE FROM likes WHERE user_id = %s AND post_id = %s", 
                             (session['user_id'], post_id))
                action = 'unliked'
            else:
                # Like
                cursor.execute("INSERT INTO likes (user_id, post_id) VALUES (%s, %s)", 
                             (session['user_id'], post_id))
                action = 'liked'
            
            connection.commit()
            
            # Get updated like count
            cursor.execute("SELECT COUNT(*) as like_count FROM likes WHERE post_id = %s", (post_id,))
            like_count = cursor.fetchone()[0]
            
            return jsonify({'action': action, 'like_count': like_count})
            
        except Error as e:
            return jsonify({'error': 'Database error'}), 500
        finally:
            cursor.close()
            connection.close()
    
    return jsonify({'error': 'Database connection failed'}), 500

@app.route('/comment_post/<int:post_id>', methods=['POST'])
def comment_post(post_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    comment_text = request.form.get('comment_text', '').strip()
    if not comment_text:
        return jsonify({'error': 'Comment cannot be empty'}), 400
    
    connection = db.get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            insert_query = "INSERT INTO comments (user_id, post_id, comment_text) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (session['user_id'], post_id, comment_text))
            connection.commit()
            
            # Get the new comment with username
            cursor.execute("""
                SELECT c.*, u.username 
                FROM comments c 
                JOIN users u ON c.user_id = u.id 
                WHERE c.id = LAST_INSERT_ID()
            """)
            new_comment = cursor.fetchone()
            
            return jsonify({
                'success': True,
                'comment': {
                    'username': new_comment['username'],
                    'comment_text': new_comment['comment_text'],
                    'created_at': new_comment['created_at'].strftime('%Y-%m-%d %H:%M')
                }
            })
            
        except Error as e:
            return jsonify({'error': 'Database error'}), 500
        finally:
            cursor.close()
            connection.close()
    
    return jsonify({'error': 'Database connection failed'}), 500

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = db.get_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get user's posts
            cursor.execute("""
                SELECT p.*, 
                (SELECT COUNT(*) FROM likes l WHERE l.post_id = p.id) as like_count,
                (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) as comment_count
                FROM posts p 
                WHERE p.user_id = %s 
                ORDER BY p.created_at DESC
            """, (session['user_id'],))
            user_posts = cursor.fetchall()
            
            # Get user info
            cursor.execute("SELECT username, email, created_at FROM users WHERE id = %s", (session['user_id'],))
            user_info = cursor.fetchone()
            
        except Error as e:
            flash('An error occurred while loading profile!', 'error')
            user_posts = []
            user_info = {}
        finally:
            cursor.close()
            connection.close()
    else:
        user_posts = []
        user_info = {}
    
    return render_template('profile.html', posts=user_posts, user=user_info)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Create all tables and upload folder
    db.create_tables()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)

@app.route('/debug/tables')
def debug_tables():
    connection = db.get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            return f"Tables in database: {tables}"
        except Error as e:
            return f"Error: {e}"
        finally:
            cursor.close()
            connection.close()
    return "No connection"