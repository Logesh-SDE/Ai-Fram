from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import sqlite3
import os
import requests
from datetime import datetime, timedelta
import json
import base64
from io import BytesIO
from PIL import Image
import secrets

# OpenWeatherMap API Configuration
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', '2cf9e83a42b43c65fa1da60e0177c9d6')
OPENWEATHER_BASE_URL = 'https://api.openweathermap.org/data/2.5'

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('templates', exist_ok=True)


# Database initialization
def init_db():
    conn = sqlite3.connect('aifarm.db')
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  full_name TEXT,
                  farm_location TEXT,
                  farm_size REAL,
                  is_admin INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Crop scans table
    c.execute('''CREATE TABLE IF NOT EXISTS crop_scans
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  image_path TEXT,
                  crop_type TEXT,
                  disease_detected TEXT,
                  confidence REAL,
                  recommendations TEXT,
                  scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')

    # Weather data table
    c.execute('''CREATE TABLE IF NOT EXISTS weather_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  location TEXT,
                  temperature REAL,
                  humidity REAL,
                  rainfall REAL,
                  weather_condition TEXT,
                  fetch_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')

    # Crop recommendations table
    c.execute('''CREATE TABLE IF NOT EXISTS crop_recommendations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  soil_type TEXT,
                  season TEXT,
                  recommended_crops TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')

    # Market prices table
    c.execute('''CREATE TABLE IF NOT EXISTS market_prices
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  crop_name TEXT,
                  price_per_kg REAL,
                  market_location TEXT,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Farm activities log
    c.execute('''CREATE TABLE IF NOT EXISTS farm_activities
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  activity_type TEXT,
                  crop_type TEXT,
                  description TEXT,
                  activity_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')

    # Government schemes table
    c.execute('''CREATE TABLE IF NOT EXISTS govt_schemes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  scheme_name TEXT NOT NULL,
                  description TEXT,
                  eligibility TEXT,
                  benefits TEXT,
                  how_to_apply TEXT,
                  ministry TEXT,
                  website_link TEXT,
                  category TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Admin logs table
    c.execute('''CREATE TABLE IF NOT EXISTS admin_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  admin_id INTEGER,
                  action TEXT,
                  details TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (admin_id) REFERENCES users (id))''')

    # Chat history table
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  message TEXT,
                  response TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')

    conn.commit()
    conn.close()

    # Add default admin user and schemes
    add_default_admin()
    add_government_schemes()


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))

        conn = sqlite3.connect('aifarm.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
        user = c.fetchone()
        conn.close()

        if not user or not user['is_admin']:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)

    return decorated_function


# Add default admin user
def add_default_admin():
    try:
        conn = sqlite3.connect('aifarm.db')
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE username = ?', ('admin',))
        if not c.fetchone():
            hashed_password = generate_password_hash('admin123')
            c.execute('''INSERT INTO users (username, email, password, full_name, is_admin)
                         VALUES (?, ?, ?, ?, ?)''',
                      ('admin', 'admin@aifarm.com', hashed_password, 'System Administrator', 1))
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error creating admin: {e}")


# Add government schemes
def add_government_schemes():
    schemes = [
        {
            'scheme_name': 'PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)',
            'description': 'Direct income support to all farmer families with cultivable land, providing ₹6000 per year in three equal installments.',
            'eligibility': 'All landholding farmer families. Institutional landholders, farmer families with income tax paying members are excluded.',
            'benefits': '₹6000 per year in three installments of ₹2000 each directly to bank accounts',
            'how_to_apply': 'Visit PM-KISAN portal, register with Aadhaar number, land details, and bank account. Can also register through CSC or local agriculture office.',
            'ministry': 'Ministry of Agriculture & Farmers Welfare',
            'website_link': 'https://pmkisan.gov.in',
            'category': 'Financial Assistance'
        },
        {
            'scheme_name': 'Pradhan Mantri Fasal Bima Yojana (PMFBY)',
            'description': 'Crop insurance scheme providing financial support to farmers in case of crop failure due to natural calamities, pests, and diseases.',
            'eligibility': 'All farmers including sharecroppers and tenant farmers. Loanee farmers are enrolled compulsorily.',
            'benefits': 'Comprehensive risk cover for crops from sowing to post-harvest. Premium subsidy provided by government.',
            'how_to_apply': 'Apply through banks, CSC centers, agriculture department offices, or online portal within cut-off dates.',
            'ministry': 'Ministry of Agriculture & Farmers Welfare',
            'website_link': 'https://pmfby.gov.in',
            'category': 'Insurance'
        },
        {
            'scheme_name': 'Kisan Credit Card (KCC)',
            'description': 'Credit facility for farmers to meet their agriculture and allied activities requirements at concessional interest rates.',
            'eligibility': 'All farmers including tenant farmers, oral lessees, and sharecroppers who are engaged in agriculture and allied activities.',
            'benefits': 'Collateral-free loans up to ₹1.60 lakh. Interest subvention of 2%. Prompt repayment incentive of 3%.',
            'how_to_apply': 'Apply at any commercial bank, RRB, or cooperative bank with land documents, Aadhaar, and KYC documents.',
            'ministry': 'Ministry of Agriculture & Farmers Welfare',
            'website_link': 'https://kcc.gov.in',
            'category': 'Credit'
        },
        {
            'scheme_name': 'Soil Health Card Scheme',
            'description': 'Provides soil health cards to farmers with information on nutrient status and recommendations on appropriate dosage of nutrients.',
            'eligibility': 'All farmers across the country',
            'benefits': 'Free soil testing, customized fertilizer recommendations, improved soil health, and increased crop productivity.',
            'how_to_apply': 'Contact local agriculture department, soil testing labs, or Krishi Vigyan Kendras for soil sample collection.',
            'ministry': 'Ministry of Agriculture & Farmers Welfare',
            'website_link': 'https://soilhealth.dac.gov.in',
            'category': 'Soil Management'
        },
        {
            'scheme_name': 'Pradhan Mantri Krishi Sinchai Yojana (PMKSY)',
            'description': 'Aims to expand cultivable area under irrigation, improve water use efficiency, and adopt precision-irrigation.',
            'eligibility': 'Individual farmers, self-help groups, cooperatives, FPOs, and other eligible institutions.',
            'benefits': 'Financial assistance for drip/sprinkler irrigation, farm ponds, and other water conservation measures.',
            'how_to_apply': 'Apply through state agriculture/horticulture departments or designated nodal agencies.',
            'ministry': 'Ministry of Jal Shakti',
            'website_link': 'https://pmksy.gov.in',
            'category': 'Irrigation'
        },
        {
            'scheme_name': 'National Agriculture Market (e-NAM)',
            'description': 'Electronic trading platform connecting APMCs across the country for transparent price discovery and better market access.',
            'eligibility': 'All farmers and traders can register and trade',
            'benefits': 'Online trading, better price realization, reduced transaction costs, and transparent auction process.',
            'how_to_apply': 'Register on e-NAM portal with mobile number, Aadhaar, and bank account details.',
            'ministry': 'Ministry of Agriculture & Farmers Welfare',
            'website_link': 'https://enam.gov.in',
            'category': 'Marketing'
        },
        {
            'scheme_name': 'Paramparagat Krishi Vikas Yojana (PKVY)',
            'description': 'Promotes organic farming through cluster approach and assists farmers in certification process.',
            'eligibility': 'Farmers willing to adopt organic farming practices. Groups of 50 farmers form clusters.',
            'benefits': '₹50,000 per hectare over 3 years including organic inputs, certification, and marketing support.',
            'how_to_apply': 'Form farmer groups, apply through state agriculture department or district agriculture office.',
            'ministry': 'Ministry of Agriculture & Farmers Welfare',
            'website_link': 'https://pgsindia-ncof.gov.in',
            'category': 'Organic Farming'
        },
        {
            'scheme_name': 'Modified Interest Subvention Scheme (MISS)',
            'description': 'Provides short-term crop loans up to ₹3 lakh at subsidized interest rates.',
            'eligibility': 'Farmers availing crop loans from banks',
            'benefits': '2% interest subvention + 3% prompt repayment incentive. Effective interest rate can be as low as 4%.',
            'how_to_apply': 'Avail crop loan from any scheduled commercial bank, benefit is automatically provided.',
            'ministry': 'Ministry of Agriculture & Farmers Welfare',
            'website_link': 'https://agricoop.nic.in',
            'category': 'Credit'
        },
        {
            'scheme_name': 'Rashtriya Krishi Vikas Yojana (RKVY)',
            'description': 'State Plan Scheme providing additional central assistance to states for agriculture and allied sector development.',
            'eligibility': 'State governments and their implementing agencies',
            'benefits': 'Funding for agriculture infrastructure, mechanization, seed production, and extension services.',
            'how_to_apply': 'State governments prepare and submit District Agriculture Plans (DAP) to central government.',
            'ministry': 'Ministry of Agriculture & Farmers Welfare',
            'website_link': 'https://rkvy.nic.in',
            'category': 'Development'
        },
        {
            'scheme_name': 'Sub-Mission on Agricultural Mechanization (SMAM)',
            'description': 'Promotes agricultural mechanization to increase efficiency and reduce drudgery in farm operations.',
            'eligibility': 'Individual farmers, women farmers, SC/ST farmers, and farmer groups',
            'benefits': '40-50% subsidy on farm equipment purchase. Up to 80% for SC/ST/women farmers in some cases.',
            'how_to_apply': 'Apply through state agriculture department, submit application with required documents and quotations.',
            'ministry': 'Ministry of Agriculture & Farmers Welfare',
            'website_link': 'https://agrimachinery.nic.in',
            'category': 'Mechanization'
        },
        {
            'scheme_name': 'National Mission for Sustainable Agriculture (NMSA)',
            'description': 'Promotes sustainable agriculture practices through soil health management, water conservation, and resource optimization.',
            'eligibility': 'Farmers, farmer groups, and implementing agencies',
            'benefits': 'Technical and financial support for sustainable farming, climate-resilient practices, and natural resource management.',
            'how_to_apply': 'Contact state agriculture department or district agriculture office for specific programs.',
            'ministry': 'Ministry of Agriculture & Farmers Welfare',
            'website_link': 'https://nmsa.dac.gov.in',
            'category': 'Sustainability'
        },
        {
            'scheme_name': 'National Horticulture Mission (NHM)',
            'description': 'Promotes holistic growth of horticulture sector covering fruits, vegetables, flowers, spices, and plantation crops.',
            'eligibility': 'Individual farmers, groups, and cooperative societies',
            'benefits': 'Financial assistance for area expansion, protected cultivation, tissue culture, and post-harvest management.',
            'how_to_apply': 'Apply through state horticulture department with project proposal and land details.',
            'ministry': 'Ministry of Agriculture & Farmers Welfare',
            'website_link': 'https://midh.gov.in',
            'category': 'Horticulture'
        }
    ]

    try:
        conn = sqlite3.connect('aifarm.db')
        c = conn.cursor()
        # Always wipe and reinsert so DB stays in sync with code (removes deleted schemes)
        c.execute('DELETE FROM govt_schemes')
        for scheme in schemes:
            c.execute('''INSERT INTO govt_schemes 
                         (scheme_name, description, eligibility, benefits, how_to_apply, ministry, website_link, category)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (scheme['scheme_name'], scheme['description'], scheme['eligibility'],
                       scheme['benefits'], scheme['how_to_apply'], scheme['ministry'],
                       scheme['website_link'], scheme['category']))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error adding schemes: {e}")


# Helper function to check allowed file
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        farm_location = request.form.get('farm_location')
        farm_size = request.form.get('farm_size')

        if not all([username, email, password]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect('aifarm.db')
            c = conn.cursor()
            c.execute('''INSERT INTO users (username, email, password, full_name, farm_location, farm_size)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (username, email, hashed_password, full_name, farm_location, farm_size))
            conn.commit()
            conn.close()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect('aifarm.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            flash(f'Welcome back, {user["username"]}!', 'success')

            if user['is_admin']:
                return redirect(url_for('admin_panel'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect('aifarm.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get recent scans
    c.execute('''SELECT * FROM crop_scans WHERE user_id = ? 
                 ORDER BY scan_date DESC LIMIT 5''', (session['user_id'],))
    recent_scans = c.fetchall()

    # Get total scans count
    c.execute('SELECT COUNT(*) as count FROM crop_scans WHERE user_id = ?', (session['user_id'],))
    total_scans = c.fetchone()['count']

    # Get recent activities
    c.execute('''SELECT * FROM farm_activities WHERE user_id = ? 
                 ORDER BY activity_date DESC LIMIT 5''', (session['user_id'],))
    recent_activities = c.fetchall()

    conn.close()

    return render_template('dashboard.html',
                           recent_scans=recent_scans,
                           total_scans=total_scans,
                           recent_activities=recent_activities)


@app.route('/disease-detection', methods=['GET', 'POST'])
@login_required
def disease_detection():
    if request.method == 'POST':
        if 'crop_image' not in request.files:
            flash('No file uploaded.', 'error')
            return redirect(request.url)

        file = request.files['crop_image']
        crop_type = request.form.get('crop_type', 'Unknown')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{session['user_id']}_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Simulate AI disease detection (replace with actual AI model)
            disease_result = simulate_disease_detection(filepath, crop_type)

            # Save to database
            conn = sqlite3.connect('aifarm.db')
            c = conn.cursor()
            c.execute('''INSERT INTO crop_scans 
                         (user_id, image_path, crop_type, disease_detected, confidence, recommendations)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (session['user_id'], filepath, crop_type,
                       disease_result['disease'], disease_result['confidence'],
                       json.dumps(disease_result['recommendations'])))
            scan_id = c.lastrowid
            conn.commit()
            conn.close()

            flash('Crop scan completed successfully!', 'success')
            return redirect(url_for('scan_result', scan_id=scan_id))

    return render_template('disease_detection.html')


@app.route('/scan-result/<int:scan_id>')
@login_required
def scan_result(scan_id):
    conn = sqlite3.connect('aifarm.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM crop_scans WHERE id = ? AND user_id = ?',
              (scan_id, session['user_id']))
    scan = c.fetchone()
    conn.close()

    if not scan:
        flash('Scan not found.', 'error')
        return redirect(url_for('disease_detection'))

    recommendations = json.loads(scan['recommendations']) if scan['recommendations'] else []

    return render_template('scan_result.html', scan=scan, recommendations=recommendations)


@app.route('/weather')
@login_required
def weather():
    # Check if we have coordinates in session from GPS
    location = session.get('user_location')
    show_prompt = True

    if not location:
        # Try user's profile location
        conn = sqlite3.connect('aifarm.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT farm_location FROM users WHERE id = ?', (session['user_id'],))
        user = c.fetchone()
        conn.close()

        if user and user['farm_location']:
            location = user['farm_location']
            show_prompt = False
    else:
        show_prompt = False

    # Get weather data if we have a location
    weather_data = None
    if location:
        weather_data = get_real_weather_data(location)

    return render_template('weather.html', weather=weather_data, location=location, show_location_prompt=show_prompt)


@app.route('/weather/by-coordinates', methods=['POST'])
@login_required
def weather_by_coordinates():
    """Get weather by GPS coordinates from browser"""
    try:
        data = request.get_json()
        lat = data.get('lat')
        lon = data.get('lon')

        if not lat or not lon:
            return jsonify({'error': 'Coordinates required'}), 400

        # Get weather by coordinates
        weather_data = get_weather_by_coordinates(lat, lon)

        # Store location in session
        if weather_data and 'location' in weather_data:
            session['user_location'] = weather_data['location']
            session.modified = True

        return jsonify({'success': True, 'location': weather_data.get('location')})

    except Exception as e:
        print(f"Error in weather_by_coordinates: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/weather/update-location', methods=['POST'])
@login_required
def update_weather_location():
    location = request.form.get('location')
    if location:
        weather_data = get_real_weather_data(location)
        return jsonify(weather_data)
    return jsonify({'error': 'Location required'}), 400


@app.route('/crop-recommendations')
@login_required
def crop_recommendations():
    return render_template('crop_recommendations.html')


@app.route('/get-crop-recommendations', methods=['POST'])
@login_required
def get_crop_recommendations():
    soil_type = request.form.get('soil_type')
    season = request.form.get('season')
    rainfall = request.form.get('rainfall')

    # Simulate AI crop recommendations
    recommendations = simulate_crop_recommendations(soil_type, season, rainfall)

    # Save to database
    conn = sqlite3.connect('aifarm.db')
    c = conn.cursor()
    c.execute('''INSERT INTO crop_recommendations (user_id, soil_type, season, recommended_crops)
                 VALUES (?, ?, ?, ?)''',
              (session['user_id'], soil_type, season, json.dumps(recommendations)))
    conn.commit()
    conn.close()

    return jsonify(recommendations)


@app.route('/market-prices')
@login_required
def market_prices():
    conn = sqlite3.connect('aifarm.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Check if prices need updating (update if older than 1 day or no prices)
    c.execute('SELECT COUNT(*) as count FROM market_prices')
    count = c.fetchone()['count']

    needs_update = False
    if count == 0:
        needs_update = True
    else:
        c.execute('SELECT updated_at FROM market_prices ORDER BY updated_at DESC LIMIT 1')
        last_update = c.fetchone()
        if last_update:
            from datetime import datetime, timedelta
            last_update_time = datetime.strptime(last_update['updated_at'], '%Y-%m-%d %H:%M:%S')
            if datetime.now() - last_update_time > timedelta(hours=24):
                needs_update = True

    if needs_update:
        conn.close()
        add_sample_market_prices()
        conn = sqlite3.connect('aifarm.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

    c.execute('SELECT * FROM market_prices ORDER BY crop_name')
    prices = c.fetchall()

    # Get today's date for display
    from datetime import datetime
    today_date = datetime.now().strftime('%B %d, %Y')

    conn.close()

    return render_template('market_prices.html', prices=prices, today_date=today_date)


@app.route('/market-prices/refresh', methods=['POST'])
@login_required
def refresh_market_prices():
    """Manually refresh market prices"""
    add_sample_market_prices()
    flash('Market prices updated successfully!', 'success')
    return redirect(url_for('market_prices'))


@app.route('/farm-log', methods=['GET', 'POST'])
@login_required
def farm_log():
    if request.method == 'POST':
        activity_type = request.form.get('activity_type')
        crop_type = request.form.get('crop_type')
        description = request.form.get('description')

        conn = sqlite3.connect('aifarm.db')
        c = conn.cursor()
        c.execute('''INSERT INTO farm_activities (user_id, activity_type, crop_type, description)
                     VALUES (?, ?, ?, ?)''',
                  (session['user_id'], activity_type, crop_type, description))
        conn.commit()
        conn.close()

        flash('Activity logged successfully!', 'success')
        return redirect(url_for('farm_log'))

    conn = sqlite3.connect('aifarm.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''SELECT * FROM farm_activities WHERE user_id = ? 
                 ORDER BY activity_date DESC''', (session['user_id'],))
    activities = c.fetchall()
    conn.close()

    return render_template('farm_log.html', activities=activities)


@app.route('/govt-schemes')
@login_required
def govt_schemes():
    conn = sqlite3.connect('aifarm.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    category = request.args.get('category', 'all')

    if category == 'all':
        c.execute('SELECT * FROM govt_schemes ORDER BY scheme_name')
    else:
        c.execute('SELECT * FROM govt_schemes WHERE category = ? ORDER BY scheme_name', (category,))

    schemes = c.fetchall()

    # Get unique categories
    c.execute('SELECT DISTINCT category FROM govt_schemes ORDER BY category')
    categories = [row['category'] for row in c.fetchall()]

    conn.close()

    return render_template('govt_schemes.html', schemes=schemes, categories=categories, selected_category=category)


@app.route('/scheme/<int:scheme_id>')
@login_required
def scheme_detail(scheme_id):
    conn = sqlite3.connect('aifarm.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM govt_schemes WHERE id = ?', (scheme_id,))
    scheme = c.fetchone()
    conn.close()

    if not scheme:
        flash('Scheme not found.', 'error')
        return redirect(url_for('govt_schemes'))

    return render_template('scheme_detail.html', scheme=scheme)


@app.route('/admin')
@admin_required
def admin_panel():
    conn = sqlite3.connect('aifarm.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get statistics
    c.execute('SELECT COUNT(*) as count FROM users WHERE is_admin = 0')
    total_users = c.fetchone()['count']

    c.execute('SELECT COUNT(*) as count FROM crop_scans')
    total_scans = c.fetchone()['count']

    c.execute('SELECT COUNT(*) as count FROM farm_activities')
    total_activities = c.fetchone()['count']

    c.execute('SELECT COUNT(*) as count FROM govt_schemes')
    total_schemes = c.fetchone()['count']

    # Get recent users
    c.execute('SELECT * FROM users WHERE is_admin = 0 ORDER BY created_at DESC LIMIT 10')
    recent_users = c.fetchall()

    # Get recent logs
    c.execute('''SELECT al.*, u.username FROM admin_logs al 
                 LEFT JOIN users u ON al.admin_id = u.id 
                 ORDER BY al.timestamp DESC LIMIT 10''')
    recent_logs = c.fetchall()

    conn.close()

    return render_template('admin_panel.html',
                           total_users=total_users,
                           total_scans=total_scans,
                           total_activities=total_activities,
                           total_schemes=total_schemes,
                           recent_users=recent_users,
                           recent_logs=recent_logs)


@app.route('/admin/users')
@admin_required
def admin_users():
    conn = sqlite3.connect('aifarm.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE is_admin = 0 ORDER BY created_at DESC')
    users = c.fetchall()
    conn.close()

    return render_template('admin_users.html', users=users)


@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    conn = sqlite3.connect('aifarm.db')
    c = conn.cursor()

    # Get user info before deletion
    c.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()

    if not user:
        flash('User not found.', 'error')
        conn.close()
        return redirect(url_for('admin_users'))

    username = user[0]

    # Delete user and related data
    c.execute('DELETE FROM crop_scans WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM farm_activities WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM crop_recommendations WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM weather_data WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))

    # Log admin action
    c.execute('''INSERT INTO admin_logs (admin_id, action, details)
                 VALUES (?, ?, ?)''',
              (session['user_id'], 'DELETE_USER', f'Deleted user: {username} (ID: {user_id})'))

    conn.commit()
    conn.close()

    flash(f'User {username} has been deleted successfully.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/schemes')
@admin_required
def admin_schemes():
    conn = sqlite3.connect('aifarm.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM govt_schemes ORDER BY scheme_name')
    schemes = c.fetchall()
    conn.close()

    return render_template('admin_schemes.html', schemes=schemes)


@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    conn = sqlite3.connect('aifarm.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # User growth
    c.execute('''SELECT DATE(created_at) as date, COUNT(*) as count 
                 FROM users WHERE is_admin = 0 
                 GROUP BY DATE(created_at) 
                 ORDER BY date DESC LIMIT 30''')
    user_growth = c.fetchall()

    # Scan statistics
    c.execute('''SELECT crop_type, COUNT(*) as count 
                 FROM crop_scans 
                 GROUP BY crop_type 
                 ORDER BY count DESC''')
    scan_stats = c.fetchall()

    # Activity statistics
    c.execute('''SELECT activity_type, COUNT(*) as count 
                 FROM farm_activities 
                 GROUP BY activity_type 
                 ORDER BY count DESC''')
    activity_stats = c.fetchall()

    conn.close()

    return render_template('admin_analytics.html',
                           user_growth=user_growth,
                           scan_stats=scan_stats,
                           activity_stats=activity_stats)


@app.route('/profile/delete-account', methods=['POST'])
@login_required
def delete_account():
    user_id = session['user_id']

    conn = sqlite3.connect('aifarm.db')
    c = conn.cursor()

    # Delete user data
    c.execute('DELETE FROM crop_scans WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM farm_activities WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM crop_recommendations WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM weather_data WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))

    conn.commit()
    conn.close()

    session.clear()
    flash('Your account has been deleted successfully.', 'success')
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    conn = sqlite3.connect('aifarm.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = c.fetchone()
    conn.close()

    return render_template('profile.html', user=user)


# ============================================
# FERTILIZER CALCULATOR
# ============================================

FERTILIZER_DATA = {
    'rice': {'N': 120, 'P': 60, 'K': 40, 'cost': 25},
    'wheat': {'N': 100, 'P': 50, 'K': 40, 'cost': 22},
    'corn': {'N': 140, 'P': 70, 'K': 60, 'cost': 28},
    'tomato': {'N': 150, 'P': 80, 'K': 100, 'cost': 30},
    'potato': {'N': 120, 'P': 60, 'K': 80, 'cost': 26},
    'cotton': {'N': 120, 'P': 60, 'K': 60, 'cost': 27},
    'sugarcane': {'N': 200, 'P': 100, 'K': 80, 'cost': 35},
    'onion': {'N': 100, 'P': 50, 'K': 50, 'cost': 24},
    'soybean': {'N': 30, 'P': 60, 'K': 40, 'cost': 20},
    'chickpea': {'N': 25, 'P': 50, 'K': 30, 'cost': 18}
}

SOIL_FACTORS = {
    'loamy': 1.0,
    'clay': 1.2,
    'sandy': 0.8,
    'silt': 1.1,
    'peaty': 0.9,
    'chalky': 1.1
}


@app.route('/fertilizer-calculator')
@login_required
def fertilizer_calculator():
    return render_template('fertilizer_calculator.html')


@app.route('/api/fertilizer/calculate', methods=['POST'])
@login_required
def calculate_fertilizer():
    try:
        data = request.get_json()
        crop_type = data.get('cropType', '').lower()
        soil_type = data.get('soilType', '').lower()
        area = float(data.get('area', 0))

        if crop_type not in FERTILIZER_DATA or area <= 0:
            return jsonify({'error': 'Invalid input'}), 400

        base = FERTILIZER_DATA[crop_type]
        factor = SOIL_FACTORS.get(soil_type, 1.0)

        nitrogen = round(base['N'] * factor * area, 2)
        phosphorus = round(base['P'] * factor * area, 2)
        potassium = round(base['K'] * factor * area, 2)
        total_cost = round((nitrogen + phosphorus + potassium) * base['cost'], 2)

        result = {
            'nitrogen': nitrogen,
            'phosphorus': phosphorus,
            'potassium': potassium,
            'totalFertilizer': nitrogen + phosphorus + potassium,
            'estimatedCost': total_cost,
            'applicationSchedule': [
                {'stage': 'Base dose', 'percentage': 50, 'timing': 'At planting'},
                {'stage': 'First top dress', 'percentage': 25, 'timing': '30 days after planting'},
                {'stage': 'Second top dress', 'percentage': 25, 'timing': '60 days after planting'}
            ]
        }

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# AI CHATBOT - IMPROVED WITH FALLBACK
# ============================================

@app.route('/chatbot')
@login_required
def chatbot():
    return render_template('chatbot.html')


@app.route('/api/chatbot/message', methods=['POST'])
@login_required
def chatbot_message():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        print(f"Received message: {user_message}")  # Debug log

        if not user_message:
            return jsonify({'error': 'Message required'}), 400

        # Use environment variable for API key (more secure)
        api_key = os.environ.get('OPENROUTER_API_KEY',
                                 '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')

        print("Calling OpenRouter API...")  # Debug log

        # Call OpenRouter API with better error handling
        try:
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'http://localhost:5000',  # Required by OpenRouter
                    'X-Title': 'AI-Farm Assistant'  # Optional but recommended
                },
                json={
                    'model': 'meta-llama/llama-3.2-3b-instruct:free',
                    'messages': [
                        {
                            'role': 'system',
                            'content': '''You are an AI farming assistant for Indian farmers. Provide practical advice about:
                            - Crop cultivation and management
                            - Pest and disease control  
                            - Fertilizer recommendations
                            - Weather-based decisions
                            - Government schemes (PM-KISAN, PMFBY, etc.)
                            - Market prices
                            Be concise, friendly, and use simple language. Keep responses under 200 words.'''
                        },
                        {'role': 'user', 'content': user_message}
                    ]
                },
                timeout=30
            )

            print(f"API Response Status: {response.status_code}")  # Debug log

            if response.status_code != 200:
                error_msg = response.text
                print(f"API Error: {error_msg}")

                # Fallback to rule-based responses
                ai_response = generate_fallback_response(user_message)
            else:
                response_data = response.json()
                ai_response = response_data['choices'][0]['message']['content']

        except requests.exceptions.Timeout:
            print("API Timeout!")
            ai_response = generate_fallback_response(user_message)

        except requests.exceptions.RequestException as e:
            print(f"Request Error: {str(e)}")
            ai_response = generate_fallback_response(user_message)

        print(f"AI Response: {ai_response[:100]}...")  # Debug log (truncated)

        # Save to database
        conn = sqlite3.connect('aifarm.db')
        c = conn.cursor()
        c.execute('INSERT INTO chat_history (user_id, message, response) VALUES (?, ?, ?)',
                  (session['user_id'], user_message, ai_response))
        conn.commit()
        conn.close()

        return jsonify({'response': ai_response}), 200

    except Exception as e:
        print(f"General Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'An error occurred. Please try again.'}), 500


def generate_fallback_response(message):
    """Generate rule-based responses when API fails"""
    message_lower = message.lower()

    # Weather queries
    if any(word in message_lower for word in ['weather', 'rain', 'temperature', 'climate']):
        return """I recommend checking the Weather section in the app for real-time weather data. 

Based on weather conditions:
- If rain is expected: Delay pesticide application and check drainage
- If hot weather: Increase irrigation and apply mulch
- Monitor weather daily for best farming decisions"""

    # Price queries
    elif any(word in message_lower for word in ['price', 'market', 'sell', 'cost']):
        return """Check the Market Prices section for current crop rates.

Tips for better prices:
- Sell during peak demand seasons
- Store crops properly to reduce spoilage
- Consider joining farmer cooperatives
- Use e-NAM platform for better price discovery"""

    # PM-KISAN queries
    elif 'pm-kisan' in message_lower or 'pmkisan' in message_lower or 'pm kisan' in message_lower:
        return """PM-KISAN provides ₹6000/year to farmers in 3 installments.

Eligibility: All landholding farmers
Benefits: ₹2000 per installment (3 times/year)
How to apply: Visit pmkisan.gov.in with Aadhaar and land records

Check the Government Schemes section for more details!"""

    # PMFBY queries
    elif 'pmfby' in message_lower or 'fasal bima' in message_lower or 'crop insurance' in message_lower:
        return """Pradhan Mantri Fasal Bima Yojana (PMFBY) provides crop insurance.

Benefits: Financial support for crop failure due to natural calamities, pests, diseases
Premium: Subsidized by government
Apply: Through banks, CSC centers, or online at pmfby.gov.in

Check Government Schemes section for full details!"""

    # Fertilizer queries
    elif any(word in message_lower for word in ['fertilizer', 'fertiliser', 'npk', 'urea', 'manure']):
        return """Use the Fertilizer Calculator in the app for crop-specific recommendations.

General tips:
- Test soil before applying fertilizers
- Use balanced NPK ratios
- Apply in split doses (base, top-dress)
- Follow recommended dosages to avoid over-fertilization
- Consider organic alternatives like compost"""

    # Disease/pest queries
    elif any(word in message_lower for word in ['disease', 'pest', 'insect', 'fungus', 'leaf', 'spot', 'blight']):
        return """Use the Disease Detection feature to scan your crops!

General advice:
- Remove affected plant parts immediately
- Improve air circulation around plants
- Use appropriate pesticides/fungicides
- Practice crop rotation annually
- Monitor crops regularly for early detection"""

    # Crop recommendations
    elif any(word in message_lower for word in ['crop', 'plant', 'grow', 'cultivate', 'sow', 'which crop']):
        return """Visit the Crop Advisor section for personalized recommendations based on:
- Your soil type
- Current season
- Rainfall patterns

Popular crops by season:
- Summer: Tomato, Corn, Cucumber, Watermelon
- Winter: Wheat, Peas, Cabbage, Cauliflower
- Monsoon: Rice, Cotton, Sugarcane, Soybean"""

    # Irrigation queries
    elif any(word in message_lower for word in ['water', 'irrigation', 'drip', 'sprinkler']):
        return """Irrigation tips for better water management:

- Use drip irrigation for water efficiency
- Water early morning or evening
- Mulch to retain soil moisture
- Check soil moisture before irrigating
- Install rain sensors for automated systems

Check PM-KISAN Sinchai Yojana for subsidy on irrigation equipment!"""

    # Greeting
    elif any(word in message_lower for word in ['hello', 'hi', 'hey', 'namaste']):
        return """Hello! I'm your AI farming assistant. I can help you with:

🌱 Crop cultivation advice
🌤️ Weather information
💰 Market prices
🐛 Pest & disease control
🧪 Fertilizer recommendations
📜 Government schemes

What would you like to know about?"""

    # Default response
    else:
        return """I'm here to help with:

🌱 Crop cultivation advice
🌤️ Weather-based farming tips
💰 Market prices and selling strategies
🐛 Pest and disease control
🧪 Fertilizer recommendations
📜 Government schemes (PM-KISAN, PMFBY, KCC, etc.)

Please ask me a specific question or use the quick question buttons below!"""


@app.route('/api/chatbot/history', methods=['GET'])
@login_required
def chat_history():
    try:
        conn = sqlite3.connect('aifarm.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''SELECT message, response, timestamp FROM chat_history 
                     WHERE user_id = ? ORDER BY timestamp ASC LIMIT 50''',
                  (session['user_id'],))
        history = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify({'history': history}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Real Weather API Integration
def get_real_weather_data(location):
    """
    Fetch real weather data from OpenWeatherMap API
    Falls back to simulation if API key not configured or request fails
    """
    try:
        # Check if API key is configured
        if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == 'your_api_key_here':
            print("OpenWeatherMap API key not configured. Using simulated data.")
            return simulate_weather_data()

        # Get current weather
        current_url = f"{OPENWEATHER_BASE_URL}/weather"
        current_params = {
            'q': location,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric'
        }

        current_response = requests.get(current_url, params=current_params, timeout=5)

        if current_response.status_code != 200:
            print(f"Weather API error: {current_response.status_code}")
            return simulate_weather_data()

        current_data = current_response.json()

        # Get 5-day forecast
        forecast_url = f"{OPENWEATHER_BASE_URL}/forecast"
        forecast_params = {
            'q': location,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric',
            'cnt': 40  # 5 days * 8 (3-hour intervals)
        }

        forecast_response = requests.get(forecast_url, params=forecast_params, timeout=5)

        if forecast_response.status_code != 200:
            # Use current data with simulated forecast
            return format_weather_data(current_data, None)

        forecast_data = forecast_response.json()

        return format_weather_data(current_data, forecast_data)

    except requests.exceptions.RequestException as e:
        print(f"Weather API request failed: {e}")
        return simulate_weather_data()
    except Exception as e:
        print(f"Weather data processing error: {e}")
        return simulate_weather_data()


def format_weather_data(current_data, forecast_data):
    """Format OpenWeatherMap data into our application format"""
    try:
        # Extract current weather
        weather_info = {
            'temperature': round(current_data['main']['temp'], 1),
            'humidity': round(current_data['main']['humidity'], 1),
            'rainfall': 0,  # Default, updated if raining
            'condition': current_data['weather'][0]['main'],
            'description': current_data['weather'][0]['description'],
            'wind_speed': round(current_data['wind']['speed'] * 3.6, 1),  # Convert m/s to km/h
            'pressure': current_data['main']['pressure'],
            'feels_like': round(current_data['main']['feels_like'], 1),
            'visibility': current_data.get('visibility', 10000) / 1000,  # Convert to km
            'sunrise': datetime.fromtimestamp(current_data['sys']['sunrise']).strftime('%H:%M'),
            'sunset': datetime.fromtimestamp(current_data['sys']['sunset']).strftime('%H:%M'),
            'location': current_data['name'],
            'country': current_data['sys']['country'],
            'forecast': []
        }

        # Check for rain data
        if 'rain' in current_data:
            weather_info['rainfall'] = round(current_data['rain'].get('1h', 0), 1)

        # Process forecast data
        if forecast_data and 'list' in forecast_data:
            # Group forecast by day and get midday forecast for each day
            daily_forecasts = {}

            for item in forecast_data['list']:
                date = datetime.fromtimestamp(item['dt']).date()
                hour = datetime.fromtimestamp(item['dt']).hour

                # Get midday forecast (around 12:00-15:00) for each day
                if date not in daily_forecasts and 11 <= hour <= 15:
                    daily_forecasts[date] = {
                        'day': date.strftime('%A') if len(daily_forecasts) == 0 else
                        'Tomorrow' if len(daily_forecasts) == 1 else
                        date.strftime('%a'),
                        'temp': round(item['main']['temp'], 1),
                        'condition': item['weather'][0]['main'],
                        'description': item['weather'][0]['description'],
                        'humidity': item['main']['humidity'],
                        'wind_speed': round(item['wind']['speed'] * 3.6, 1)
                    }

                # Limit to 5 days
                if len(daily_forecasts) >= 5:
                    break

            weather_info['forecast'] = list(daily_forecasts.values())

        # If no forecast data, create simulated forecast based on current
        if not weather_info['forecast']:
            weather_info['forecast'] = generate_forecast_from_current(weather_info)

        return weather_info

    except Exception as e:
        print(f"Error formatting weather data: {e}")
        return simulate_weather_data()


def generate_forecast_from_current(current_weather):
    """Generate approximate 5-day forecast based on current conditions"""
    import random

    forecast = []
    base_temp = current_weather['temperature']

    days = ['Today', 'Tomorrow', 'Day 3', 'Day 4', 'Day 5']

    for i, day in enumerate(days):
        # Add some variation
        temp_variation = random.uniform(-3, 3)
        forecast.append({
            'day': day,
            'temp': round(base_temp + temp_variation, 1),
            'condition': current_weather['condition'],
            'description': current_weather.get('description', current_weather['condition']),
            'humidity': current_weather['humidity'] + random.randint(-10, 10)
        })

    return forecast


def detect_location_from_ip():
    """Detect user's location from IP address using ipapi.co"""
    try:
        response = requests.get('https://ipapi.co/json/', timeout=3)
        if response.status_code == 200:
            data = response.json()
            city = data.get('city', '')
            country = data.get('country_code', '')
            if city:
                return f"{city}, {country}"
        return None
    except:
        return None


def get_weather_by_coordinates(lat, lon):
    """Get weather data using GPS coordinates"""
    try:
        if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == 'your_api_key_here':
            return simulate_weather_data()

        # Get current weather by coordinates
        current_url = f"{OPENWEATHER_BASE_URL}/weather"
        current_params = {
            'lat': lat,
            'lon': lon,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric'
        }

        current_response = requests.get(current_url, params=current_params, timeout=5)

        if current_response.status_code != 200:
            return simulate_weather_data()

        current_data = current_response.json()

        # Get 5-day forecast
        forecast_url = f"{OPENWEATHER_BASE_URL}/forecast"
        forecast_params = {
            'lat': lat,
            'lon': lon,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric',
            'cnt': 40
        }

        forecast_response = requests.get(forecast_url, params=forecast_params, timeout=5)
        forecast_data = forecast_response.json() if forecast_response.status_code == 200 else None

        return format_weather_data(current_data, forecast_data)

    except Exception as e:
        print(f"Error getting weather by coordinates: {e}")
        return simulate_weather_data()


# Simulation functions (fallback when API is not available)
def simulate_disease_detection(image_path, crop_type):
    diseases = {
        'tomato': ['Early Blight', 'Late Blight', 'Leaf Mold', 'Healthy'],
        'potato': ['Late Blight', 'Early Blight', 'Healthy'],
        'wheat': ['Rust', 'Smut', 'Healthy'],
        'rice': ['Blast', 'Brown Spot', 'Healthy'],
        'corn': ['Common Rust', 'Gray Leaf Spot', 'Healthy']
    }

    import random
    crop_diseases = diseases.get(crop_type.lower(), ['Unknown Disease', 'Healthy'])
    detected_disease = random.choice(crop_diseases)
    confidence = round(random.uniform(0.75, 0.98), 2)

    recommendations = []
    if detected_disease == 'Healthy':
        recommendations = [
            'Continue regular monitoring',
            'Maintain proper irrigation',
            'Apply balanced fertilizers'
        ]
    else:
        recommendations = [
            f'Apply fungicide treatment for {detected_disease}',
            'Remove affected leaves immediately',
            'Improve air circulation around plants',
            'Avoid overhead irrigation',
            'Consider crop rotation next season'
        ]

    return {
        'disease': detected_disease,
        'confidence': confidence,
        'recommendations': recommendations
    }


def simulate_weather_data():
    import random
    return {
        'temperature': round(random.uniform(20, 35), 1),
        'humidity': round(random.uniform(40, 80), 1),
        'rainfall': round(random.uniform(0, 50), 1),
        'condition': random.choice(['Sunny', 'Partly Cloudy', 'Cloudy', 'Rainy']),
        'wind_speed': round(random.uniform(5, 25), 1),
        'forecast': [
            {'day': 'Today', 'temp': 28, 'condition': 'Sunny'},
            {'day': 'Tomorrow', 'temp': 26, 'condition': 'Cloudy'},
            {'day': 'Day 3', 'temp': 27, 'condition': 'Partly Cloudy'},
            {'day': 'Day 4', 'temp': 25, 'condition': 'Rainy'},
            {'day': 'Day 5', 'temp': 29, 'condition': 'Sunny'}
        ]
    }


def simulate_crop_recommendations(soil_type, season, rainfall):
    """Generate crop recommendations based on soil, season, and rainfall"""
    import random

    crop_db = {
        'loamy': {
            'summer': ['Tomato', 'Cucumber', 'Corn', 'Watermelon', 'Bell Pepper'],
            'winter': ['Wheat', 'Peas', 'Cabbage', 'Spinach', 'Cauliflower'],
            'monsoon': ['Rice', 'Sugarcane', 'Cotton', 'Soybean']
        },
        'clay': {
            'summer': ['Cotton', 'Sunflower', 'Sorghum', 'Okra'],
            'winter': ['Wheat', 'Barley', 'Mustard', 'Chickpea'],
            'monsoon': ['Rice', 'Jute', 'Pulses', 'Cotton']
        },
        'sandy': {
            'summer': ['Watermelon', 'Peanuts', 'Carrots', 'Millet'],
            'winter': ['Potatoes', 'Onions', 'Garlic', 'Radish'],
            'monsoon': ['Millets', 'Pulses', 'Groundnut']
        },
        'silt': {
            'summer': ['Tomato', 'Cucumber', 'Squash', 'Beans'],
            'winter': ['Lettuce', 'Broccoli', 'Peas', 'Cabbage'],
            'monsoon': ['Rice', 'Vegetables', 'Pulses']
        },
        'peaty': {
            'summer': ['Vegetables', 'Berries', 'Herbs'],
            'winter': ['Root Vegetables', 'Brassicas'],
            'monsoon': ['Rice', 'Vegetables']
        },
        'chalky': {
            'summer': ['Beans', 'Brassicas', 'Spinach'],
            'winter': ['Cabbage', 'Beetroot', 'Onions'],
            'monsoon': ['Legumes', 'Vegetables']
        }
    }

    # Get crops for soil and season
    soil_data = crop_db.get(soil_type.lower(), {
        'summer': ['Consult Agricultural Expert'],
        'winter': ['Consult Agricultural Expert'],
        'monsoon': ['Consult Agricultural Expert']
    })

    crops = soil_data.get(season.lower(), ['Consult Agricultural Expert'])

    # Generate recommendations with varied data
    recommendations = []
    for i, crop in enumerate(crops[:5]):  # Limit to 5 crops
        suitability = 'High' if i < 2 else 'Medium' if i < 4 else 'Moderate'

        # Adjust yield based on rainfall
        base_yield = random.randint(25, 45)
        if rainfall == 'high':
            yield_multiplier = 1.2
        elif rainfall == 'medium':
            yield_multiplier = 1.0
        else:
            yield_multiplier = 0.8

        expected_yield = int(base_yield * yield_multiplier)

        recommendations.append({
            'crop': crop,
            'suitability': suitability,
            'expected_yield': f'{expected_yield} tons/hectare',
            'duration': f'{random.randint(60, 120)} days'
        })

    return recommendations


def add_sample_market_prices():
    """Add or update market prices with today's date and realistic variations"""
    from datetime import datetime
    import random

    # Base prices for Indian crops (in ₹ per kg)
    base_prices = {
        'Wheat': 25.50,
        'Rice': 32.00,
        'Tomato': 18.00,
        'Potato': 22.00,
        'Onion': 28.00,
        'Corn': 20.00,
        'Cotton': 55.00,
        'Sugarcane': 30.00,
        'Soybean': 45.00,
        'Groundnut': 50.00,
        'Chickpea': 60.00,
        'Mustard': 52.00,
        'Cauliflower': 25.00,
        'Cabbage': 15.00,
        'Carrot': 30.00,
        'Cucumber': 20.00
    }

    # Market locations in India
    markets = ['Chennai Market', 'Delhi Mandi', 'Mumbai APMC', 'Bangalore Market', 'Kolkata Market']

    conn = sqlite3.connect('aifarm.db')
    c = conn.cursor()

    # Clear old prices
    c.execute('DELETE FROM market_prices')

    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Add updated prices with variations
    for crop, base_price in base_prices.items():
        # Add price variation (±15%)
        variation = random.uniform(-0.15, 0.15)
        current_price = round(base_price * (1 + variation), 2)

        # Select random market
        market = random.choice(markets)

        c.execute('''INSERT INTO market_prices (crop_name, price_per_kg, market_location, updated_at)
                     VALUES (?, ?, ?, ?)''', (crop, current_price, market, today))

    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)