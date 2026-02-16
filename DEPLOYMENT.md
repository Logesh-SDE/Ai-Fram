# AI-Farm Deployment Guide

## Local Development Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser

### Installation Steps

1. **Navigate to project directory**
   ```bash
   cd ai-farm-web
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the app**
   - Open browser to: http://localhost:5000

## Production Deployment Options

### Option 1: Deploy on Heroku

1. **Install Heroku CLI**
   ```bash
   # Mac
   brew tap heroku/brew && brew install heroku
   
   # Windows - Download from heroku.com
   ```

2. **Create Procfile**
   ```
   web: gunicorn app:app
   ```

3. **Add gunicorn to requirements.txt**
   ```
   gunicorn==21.2.0
   ```

4. **Deploy**
   ```bash
   heroku login
   heroku create ai-farm-app
   git init
   git add .
   git commit -m "Initial commit"
   git push heroku main
   ```

### Option 2: Deploy on PythonAnywhere

1. **Sign up at pythonanywhere.com**

2. **Upload files**
   - Use "Files" tab to upload project

3. **Create virtual environment**
   ```bash
   mkvirtualenv --python=/usr/bin/python3.8 ai-farm
   pip install -r requirements.txt
   ```

4. **Configure WSGI**
   - Edit WSGI configuration file
   - Point to app.py

5. **Reload web app**

### Option 3: Deploy on AWS EC2

1. **Launch EC2 instance**
   - Ubuntu 20.04 LTS
   - t2.micro (free tier)

2. **SSH into instance**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

3. **Install dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx
   ```

4. **Setup application**
   ```bash
   git clone your-repo
   cd ai-farm-web
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn
   ```

5. **Configure Nginx**
   Create `/etc/nginx/sites-available/ai-farm`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

6. **Enable site**
   ```bash
   sudo ln -s /etc/nginx/sites-available/ai-farm /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

7. **Run with gunicorn**
   ```bash
   gunicorn -w 4 -b 127.0.0.1:5000 app:app
   ```

8. **Setup systemd service** (optional for auto-start)
   Create `/etc/systemd/system/ai-farm.service`:
   ```ini
   [Unit]
   Description=AI-Farm Flask App
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/ai-farm-web
   Environment="PATH=/home/ubuntu/ai-farm-web/venv/bin"
   ExecStart=/home/ubuntu/ai-farm-web/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app

   [Install]
   WantedBy=multi-user.target
   ```

   Enable service:
   ```bash
   sudo systemctl enable ai-farm
   sudo systemctl start ai-farm
   ```

### Option 4: Docker Deployment

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.9-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install -r requirements.txt

   COPY . .

   EXPOSE 5000

   CMD ["python", "app.py"]
   ```

2. **Create docker-compose.yml**
   ```yaml
   version: '3.8'
   services:
     web:
       build: .
       ports:
         - "5000:5000"
       volumes:
         - ./:/app
       environment:
         - FLASK_ENV=production
   ```

3. **Build and run**
   ```bash
   docker-compose up -d
   ```

## Environment Configuration

### Production Settings

Edit `app.py` for production:

```python
import os

# Use environment variables
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key')

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///ai-farm.db')

# Disable debug mode
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
```

### Environment Variables

Create `.env` file:
```
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/ai-farm
FLASK_ENV=production
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216
```

## Database Migration (PostgreSQL)

For production, switch to PostgreSQL:

1. **Install psycopg2**
   ```bash
   pip install psycopg2-binary
   ```

2. **Update database connection**
   ```python
   import psycopg2
   from urllib.parse import urlparse
   
   url = urlparse(os.environ['DATABASE_URL'])
   conn = psycopg2.connect(
       database=url.path[1:],
       user=url.username,
       password=url.password,
       host=url.hostname,
       port=url.port
   )
   ```

## Security Enhancements

### 1. HTTPS Setup (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 2. Security Headers

Add to app.py:
```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

### 3. Rate Limiting

```bash
pip install Flask-Limiter
```

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # login logic
```

## Performance Optimization

### 1. Enable Caching

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/market-prices')
@cache.cached(timeout=300)
def market_prices():
    # ...
```

### 2. Compress Responses

```bash
pip install flask-compress
```

```python
from flask_compress import Compress
Compress(app)
```

### 3. Static File Serving

Use CDN or configure nginx to serve static files:
```nginx
location /static {
    alias /path/to/ai-farm-web/static;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

## Monitoring & Logging

### 1. Application Logging

Add to app.py:
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    handler = RotatingFileHandler('ai-farm.log', maxBytes=10000, backupCount=3)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
```

### 2. Error Tracking (Sentry)

```bash
pip install sentry-sdk[flask]
```

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()]
)
```

## Backup Strategy

### 1. Database Backup

```bash
# SQLite
sqlite3 ai-farm.db .dump > backup.sql

# PostgreSQL
pg_dump ai-farm > backup.sql
```

### 2. Automated Backups (cron)

```bash
# Add to crontab
0 2 * * * /path/to/backup-script.sh
```

Create backup script:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
sqlite3 /path/to/ai-farm.db .dump > /backups/ai-farm_$DATE.sql
find /backups -name "ai-farm_*.sql" -mtime +7 -delete
```

## Scaling Considerations

### Horizontal Scaling
- Use load balancer (AWS ELB, nginx)
- Session storage (Redis)
- Centralized file storage (S3)

### Vertical Scaling
- Increase server resources
- Optimize database queries
- Add database indexes

## Maintenance Checklist

- [ ] Regular security updates
- [ ] Database backups
- [ ] Monitor disk space
- [ ] Check application logs
- [ ] Update dependencies
- [ ] SSL certificate renewal
- [ ] Performance monitoring
- [ ] User feedback review

## Troubleshooting

### Application won't start
- Check Python version
- Verify all dependencies installed
- Check port availability
- Review error logs

### Database errors
- Verify database file permissions
- Check database schema
- Review migration logs

### Performance issues
- Enable caching
- Optimize database queries
- Check server resources
- Review application logs

## Support & Updates

For updates and support:
- Check GitHub repository
- Review documentation
- Submit issues
- Join community forums

---

**Remember**: Always test in staging before deploying to production!
