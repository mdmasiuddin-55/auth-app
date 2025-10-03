Vibesphere 🌟

A modern social media platform where users share "vibes" (posts), "boost" (like) content, and engage in "commentary" (comments). Built with Python Flask and AWS RDS.

![Vibesphere](https://img.shields.io/badge/Vibesphere-Social%20Platform-purple)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green)
![AWS RDS](https://img.shields.io/badge/AWS-RDS-orange)

## 🚀 Features

- **Vibes** - Share images and videos with captions
- **Boosts** - Like posts with rocket animations
- **Commentary** - Engage in conversations
- **User Profiles** - Personal profile pages
- **Secure Authentication** - Login/signup with password hashing
- **AWS RDS Integration** - Scalable database storage
- **Responsive Design** - Works on all devices

## 🛠 Tech Stack

- **Backend**: Python, Flask
- **Database**: AWS RDS MySQL
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **File Upload**: Image and video support
- **Security**: Werkzeug password hashing, session management

## 📋 Prerequisites

Before deployment, ensure you have:

- Python 3.8 or higher
- AWS Account with RDS access
- MySQL client (for database management)

## 🚀 Quick Deployment

### 1. Clone the Repository
```bash
git clone https://github.com/mdmasiuddin-55/vibesphere.py.git 
cd vibesphere.py
```

### 2. Set Up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. AWS RDS Setup

#### Create RDS Instance:
1. Go to AWS RDS Console
2. Click "Create database"
3. Choose "MySQL"
4. Select "Free tier" template
5. Configure:
   - DB instance identifier: `vibesphere-db`
   - Master username: `admin` (or your preferred username)
   - Master password: `[strong-password]`
6. Network & Security:
   - Public access: **Yes**
   - VPC security group: Create new or use existing
7. Click "Create database"

#### Configure Security Group:
1. Go to EC2 → Security Groups
2. Find your RDS security group
3. Edit inbound rules:
   - Type: MySQL/Aurora
   - Port: 3306
   - Source: 0.0.0.0/0 (or your IP for security)

### 5. Environment Configuration

Create `.env` file:
```env
# AWS RDS Configuration
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_USER=your-database-username
DB_PASSWORD=your-database-password
DB_NAME=auth_database
DB_PORT=3306

# Flask Configuration
SECRET_KEY=generate-a-secure-random-key
```

Generate secret key:
```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env
```

### 6. Database Initialization

The application automatically creates required tables on first run. Manual setup:

```sql
-- Connect to your RDS instance and run:
CREATE DATABASE IF NOT EXISTS vibesphere_db;
```

### 7. Run the Application

```bash
# Create uploads directory
mkdir -p static/uploads

# Run the application
python app.py
```

The application will be available at `http://localhost:5000`

## 📁 Project Structure

```
vibesphere/
├── app.py                 # Main application file
├── config.py             # Configuration settings
├── database.py           # Database connection and models
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this)
├── static/
│   ├── uploads/          # User uploaded files
│   └── css/              # Custom styles (if any)
└── templates/
    ├── base.html         # Base template
    ├── feed.html         # Main feed page
    ├── create_post.html  # Create vibe page
    ├── profile.html      # User profile
    ├── login.html        # Login page
    └── signup.html       # Registration page
```

## 🔧 Configuration

### Database Tables
The application creates these tables automatically:
- `users` - User accounts and profiles
- `posts` - Vibes (posts with images/videos)
- `likes` - Boosts (likes system)
- `comments` - Commentary (comments on vibes)

### File Uploads
- Supported formats: PNG, JPG, JPEG, GIF, MP4, MOV, AVI
- Max file size: 16MB
- Files stored in `static/uploads/`

## 🚀 Production Deployment

### For AWS EC2 Deployment:

1. **Launch EC2 Instance**
   - Amazon Linux 2 or Ubuntu
   - Configure security groups to allow HTTP/HTTPS

2. **Install Dependencies**
```bash
sudo yum update -y
sudo yum install python3 -y
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Set Up Reverse Proxy (Nginx)**
```bash
sudo yum install nginx -y
sudo systemctl start nginx
```

4. **Configure Nginx**
Create `/etc/nginx/conf.d/vibesphere.conf`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/vibesphere/static;
    }
}
```

5. **Run with Gunicorn**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Environment Variables for Production
```env
# Production .env
DB_HOST=production-rds-endpoint.rds.amazonaws.com
DB_USER=prod_username
DB_PASSWORD=prod_strong_password
DB_NAME=vibesphere_prod
DB_PORT=3306
SECRET_KEY=production-secret-key-here
FLASK_ENV=production
```

## 🔒 Security Considerations

- ✅ Password hashing with Werkzeug
- ✅ SQL injection prevention with parameterized queries
- ✅ File upload validation
- ✅ Session management
- ⚠️ **Important**: Restrict RDS access to specific IPs in production
- ⚠️ **Important**: Use strong secret keys
- ⚠️ **Important**: Regular database backups

## 🐛 Troubleshooting

### Common Issues:

1. **Database Connection Failed**
   - Check RDS endpoint in `.env`
   - Verify security group allows your IP
   - Confirm database is running

2. **File Upload Issues**
   - Check `static/uploads/` directory exists
   - Verify file permissions
   - Check file size limits

3. **Template Errors**
   - Ensure all template files are in `templates/` directory
   - Check for syntax errors in HTML files

### Debug Mode
For development, enable debug mode in `app.py`:
```python
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

## 📈 Monitoring & Maintenance

### Database Backups
```bash
# Export database
mysqldump -h [RDS_ENDPOINT] -u [USERNAME] -p [DATABASE] > backup.sql

# Import database
mysql -h [RDS_ENDPOINT] -u [USERNAME] -p [DATABASE] < backup.sql
```

### Logs
- Application logs: Check terminal/output
- Database logs: AWS RDS console → Logs

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support:
1. Check troubleshooting section above
2. Review AWS RDS documentation
3. Create an issue in the repository

---

**Happy Vibing!** 🚀✨

*Vibesphere - Share Your Vibe with the World*
