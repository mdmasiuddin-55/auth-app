from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from database import Database
from config import Config
from flask_socketio import SocketIO, emit, join_room, leave_room
import eventlet
eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['PROFILE_PICTURE_FOLDER'] = 'static/uploads/profile_pictures'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize database
db = Database()

# Store online users (in production, use Redis)
online_users = {}

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
        bio = request.form.get('bio', '')
        
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
                insert_query = "INSERT INTO users (username, email, password_hash, bio) VALUES (%s, %s, %s, %s)"
                cursor.execute(insert_query, (username, email, password_hash, bio))
                connection.commit()
                user_id = cursor.lastrowid
                
                session['user_id'] = user_id
                session['username'] = username
                session['profile_picture'] = None
                flash('Account created successfully!', 'success')
                return redirect(url_for('feed'))
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
                    session['profile_picture'] = user['profile_picture']
                    
                    # Update user online status
                    cursor.execute("UPDATE users SET is_online = TRUE WHERE id = %s", (user['id'],))
                    connection.commit()
                    
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
                SELECT p.*, u.username, u.profile_picture,
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
                    SELECT c.*, u.username, u.profile_picture
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
                    flash('Vibe created successfully!', 'success')
                    return redirect(url_for('feed'))
                except Error as e:
                    flash('An error occurred while creating the vibe!', 'error')
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
                SELECT c.*, u.username, u.profile_picture
                FROM comments c 
                JOIN users u ON c.user_id = u.id 
                WHERE c.id = LAST_INSERT_ID()
            """)
            new_comment = cursor.fetchone()
            
            return jsonify({
                'success': True,
                'comment': {
                    'username': new_comment['username'],
                    'profile_picture': new_comment['profile_picture'],
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
            cursor.execute("SELECT username, email, profile_picture, bio, created_at FROM users WHERE id = %s", (session['user_id'],))
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

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = db.get_connection()
    if connection:
        try:
            if request.method == 'POST':
                username = request.form.get('username')
                bio = request.form.get('bio', '')
                file = request.files.get('profile_picture')
                
                # Check if username is taken by another user
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT id FROM users WHERE username = %s AND id != %s", (username, session['user_id']))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    flash('Username already taken!', 'error')
                    return redirect(url_for('edit_profile'))
                
                profile_picture_path = session.get('profile_picture')
                
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Add user id to filename to make it unique
                    name, ext = os.path.splitext(filename)
                    filename = f"user_{session['user_id']}_{int(datetime.now().timestamp())}{ext}"
                    file_path = os.path.join(app.config['PROFILE_PICTURE_FOLDER'], filename)
                    file.save(file_path)
                    profile_picture_path = f"uploads/profile_pictures/{filename}"
                
                # Update user in database
                update_query = "UPDATE users SET username = %s, bio = %s"
                params = [username, bio]
                
                if profile_picture_path:
                    update_query += ", profile_picture = %s"
                    params.append(profile_picture_path)
                
                update_query += " WHERE id = %s"
                params.append(session['user_id'])
                
                cursor.execute(update_query, tuple(params))
                connection.commit()
                
                # Update session
                session['username'] = username
                if profile_picture_path:
                    session['profile_picture'] = profile_picture_path
                
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('profile'))
            
            # GET request - load current user data
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT username, email, profile_picture, bio FROM users WHERE id = %s", (session['user_id'],))
            user_info = cursor.fetchone()
            
        except Error as e:
            flash('An error occurred while updating profile!', 'error')
            return redirect(url_for('profile'))
        finally:
            cursor.close()
            connection.close()
    else:
        flash('Database connection failed!', 'error')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html', user=user_info)

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = db.get_connection()
    users = []
    chat_sessions = []
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get all users except current user
            cursor.execute("""
                SELECT id, username, profile_picture, is_online, last_seen 
                FROM users 
                WHERE id != %s 
                ORDER BY username
            """, (session['user_id'],))
            users = cursor.fetchall()
            
            # Get chat sessions for current user
            cursor.execute("""
                SELECT cs.*, 
                CASE 
                    WHEN cs.user1_id = %s THEN u2.username
                    ELSE u1.username
                END as other_username,
                CASE 
                    WHEN cs.user1_id = %s THEN u2.profile_picture
                    ELSE u1.profile_picture
                END as other_profile_picture,
                CASE 
                    WHEN cs.user1_id = %s THEN u2.is_online
                    ELSE u1.is_online
                END as other_online,
                (SELECT message_text FROM messages WHERE chat_session_id = cs.id ORDER BY created_at DESC LIMIT 1) as last_message,
                (SELECT created_at FROM messages WHERE chat_session_id = cs.id ORDER BY created_at DESC LIMIT 1) as last_message_time
                FROM chat_sessions cs
                JOIN users u1 ON cs.user1_id = u1.id
                JOIN users u2 ON cs.user2_id = u2.id
                WHERE cs.user1_id = %s OR cs.user2_id = %s
                ORDER BY cs.updated_at DESC
            """, (session['user_id'], session['user_id'], session['user_id'], session['user_id'], session['user_id']))
            chat_sessions = cursor.fetchall()
            
        except Error as e:
            flash('An error occurred while loading chat!', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('chat.html', users=users, chat_sessions=chat_sessions)

@app.route('/get_messages/<int:chat_session_id>')
def get_messages(chat_session_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    connection = db.get_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Verify user has access to this chat session
            cursor.execute("""
                SELECT id FROM chat_sessions 
                WHERE id = %s AND (user1_id = %s OR user2_id = %s)
            """, (chat_session_id, session['user_id'], session['user_id']))
            chat_session = cursor.fetchone()
            
            if not chat_session:
                return jsonify({'error': 'Chat session not found'}), 404
            
            # Get messages
            cursor.execute("""
                SELECT m.*, u.username, u.profile_picture
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE m.chat_session_id = %s
                ORDER BY m.created_at ASC
            """, (chat_session_id,))
            messages = cursor.fetchall()
            
            # Mark messages as read
            cursor.execute("""
                UPDATE messages 
                SET is_read = TRUE 
                WHERE chat_session_id = %s AND sender_id != %s AND is_read = FALSE
            """, (chat_session_id, session['user_id']))
            connection.commit()
            
            # Convert datetime objects to strings
            for message in messages:
                message['created_at'] = message['created_at'].strftime('%Y-%m-%d %H:%M')
            
            return jsonify({'messages': messages})
            
        except Error as e:
            return jsonify({'error': 'Database error'}), 500
        finally:
            cursor.close()
            connection.close()
    
    return jsonify({'error': 'Database connection failed'}), 500

@app.route('/start_chat/<int:user_id>')
def start_chat(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    connection = db.get_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Check if chat session already exists
            cursor.execute("""
                SELECT id FROM chat_sessions 
                WHERE (user1_id = %s AND user2_id = %s) OR (user1_id = %s AND user2_id = %s)
            """, (session['user_id'], user_id, user_id, session['user_id']))
            existing_chat = cursor.fetchone()
            
            if existing_chat:
                return jsonify({'chat_session_id': existing_chat['id']})
            
            # Create new chat session
            cursor.execute("""
                INSERT INTO chat_sessions (user1_id, user2_id) 
                VALUES (%s, %s)
            """, (session['user_id'], user_id))
            connection.commit()
            chat_session_id = cursor.lastrowid
            
            return jsonify({'chat_session_id': chat_session_id})
            
        except Error as e:
            return jsonify({'error': 'Database error'}), 500
        finally:
            cursor.close()
            connection.close()
    
    return jsonify({'error': 'Database connection failed'}), 500

@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        user_id = session['user_id']
        online_users[user_id] = request.sid
        
        # Update user online status in database
        connection = db.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("UPDATE users SET is_online = TRUE WHERE id = %s", (user_id,))
                connection.commit()
            except Error as e:
                print(f"Error updating online status: {e}")
            finally:
                cursor.close()
                connection.close()
        
        emit('user_online', {'user_id': user_id}, broadcast=True)
        print(f"User {user_id} connected")

@socketio.on('disconnect')
def handle_disconnect():
    if 'user_id' in session:
        user_id = session['user_id']
        online_users.pop(user_id, None)
        
        # Update user offline status in database
        connection = db.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("UPDATE users SET is_online = FALSE, last_seen = NOW() WHERE id = %s", (user_id,))
                connection.commit()
            except Error as e:
                print(f"Error updating offline status: {e}")
            finally:
                cursor.close()
                connection.close()
        
        emit('user_offline', {'user_id': user_id}, broadcast=True)
        print(f"User {user_id} disconnected")

@socketio.on('send_message')
def handle_send_message(data):
    if 'user_id' not in session:
        return
    
    chat_session_id = data['chat_session_id']
    message_text = data['message_text']
    
    connection = db.get_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Save message to database
            cursor.execute("""
                INSERT INTO messages (chat_session_id, sender_id, message_text) 
                VALUES (%s, %s, %s)
            """, (chat_session_id, session['user_id'], message_text))
            connection.commit()
            
            # Get the saved message with user info
            cursor.execute("""
                SELECT m.*, u.username, u.profile_picture
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE m.id = LAST_INSERT_ID()
            """)
            message = cursor.fetchone()
            
            # Get the other user in the chat session
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN user1_id = %s THEN user2_id
                        ELSE user1_id
                    END as other_user_id
                FROM chat_sessions 
                WHERE id = %s
            """, (session['user_id'], chat_session_id))
            other_user = cursor.fetchone()
            
            # Update chat session timestamp
            cursor.execute("UPDATE chat_sessions SET updated_at = NOW() WHERE id = %s", (chat_session_id,))
            connection.commit()
            
            # Prepare message data for emitting
            message_data = {
                'id': message['id'],
                'chat_session_id': message['chat_session_id'],
                'sender_id': message['sender_id'],
                'username': message['username'],
                'profile_picture': message['profile_picture'],
                'message_text': message['message_text'],
                'created_at': message['created_at'].strftime('%Y-%m-%d %H:%M')
            }
            
            # Send to sender
            emit('new_message', message_data, room=request.sid)
            
            # Send to receiver if online
            if other_user['other_user_id'] in online_users:
                emit('new_message', message_data, room=online_users[other_user['other_user_id']])
            
        except Error as e:
            print(f"Error sending message: {e}")
        finally:
            cursor.close()
            connection.close()

@app.route('/logout')
def logout():
    if 'user_id' in session:
        user_id = session['user_id']
        
        # Update user offline status
        connection = db.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("UPDATE users SET is_online = FALSE, last_seen = NOW() WHERE id = %s", (user_id,))
                connection.commit()
            except Error as e:
                print(f"Error updating logout status: {e}")
            finally:
                cursor.close()
                connection.close()
    
    session.clear()
    flash('You have been logged out!', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Create all tables and upload folders
    db.create_tables()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROFILE_PICTURE_FOLDER'], exist_ok=True)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)