from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from database import Database
from config import Config

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Initialize database
db = Database()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Basic validation
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('signup.html')
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Save to database
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
                    return redirect(url_for('dashboard'))
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

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Create users table if it doesn't exist
    db.create_users_table()
    app.run(debug=True, host='0.0.0.0', port=5000)