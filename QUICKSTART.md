# AI-Farm - Quick Start Guide

## 🚀 Getting Started in 3 Simple Steps

### Step 1: Install Python
Make sure you have Python 3.8 or higher installed on your computer.
- Download from: https://www.python.org/downloads/
- During installation, check "Add Python to PATH"

### Step 2: Run the Application

**On Windows:**
- Double-click `run.bat`

**On Mac/Linux:**
- Open Terminal
- Navigate to the ai-farm-web folder
- Run: `./run.sh`

**Or manually:**
```bash
pip install -r requirements.txt
python app.py
```

### Step 3: Open Your Browser
- Go to: http://localhost:5000
- Register a new account
- Start using AI-Farm!

## 📋 Default Test Credentials (Optional)

You can create any account you want. Sample account:
- Username: farmer1
- Email: farmer@example.com
- Password: password123

## 🎯 Quick Feature Tour

### 1. Disease Detection
- Click "Disease Detection" in menu
- Upload a crop image (any plant image for testing)
- Select crop type
- Get instant AI analysis!

### 2. Weather Forecast
- Click "Weather"
- View current conditions
- Check 5-day forecast
- Get farming advice

### 3. Crop Recommendations
- Click "Crop Advisor"
- Select soil type and season
- Get AI-powered crop suggestions

### 4. Market Prices
- Click "Market Prices"
- View current crop prices
- Search and filter crops
- Get market insights

### 5. Farm Log
- Click "Farm Log"
- Track your daily activities
- View activity timeline
- Filter and search records

## 🔧 Troubleshooting

### Port Already in Use
If you see "Address already in use" error:
1. Close any other applications using port 5000
2. Or edit `app.py` and change the port number in the last line:
   ```python
   app.run(debug=True, host='0.0.0.0', port=5001)  # Change to 5001
   ```

### Module Not Found Error
Run: `pip install -r requirements.txt`

### Database Error
Delete `ai-farm.db` file and restart the application.

## 📱 Features Overview

✅ User Authentication & Profiles
✅ AI Disease Detection with Recommendations
✅ Weather Forecasting
✅ Crop Recommendations
✅ Market Price Tracking
✅ Farm Activity Logging
✅ Interactive Dashboard
✅ Responsive Design

## 🎨 Using the Application

1. **Register/Login** - Create your account first
2. **Complete Profile** - Add farm details (optional)
3. **Upload Crop Images** - Start disease detection
4. **Check Weather** - Plan your farm activities
5. **Get Recommendations** - Find best crops to plant
6. **Track Activities** - Log all farm operations
7. **Monitor Prices** - Stay updated with market rates

## 💡 Tips

- Use clear, well-lit images for disease detection
- Update your farm location for accurate weather data
- Log activities regularly for better farm management
- Check market prices before harvesting
- Follow weather-based farming advice

## 🔐 Security Notes

- Passwords are securely hashed
- Each user has private data
- Uploaded images are stored securely
- Session management prevents unauthorized access

## 📊 Sample Data

The application includes sample market prices to get you started. You can:
- View existing crops and prices
- Add your own activities
- Upload crop images for analysis
- Track your farming operations

## 🎓 Learning Resources

### Understanding the Code
- `app.py` - Main application logic
- `templates/` - All HTML pages
- `static/css/style.css` - Styling
- `static/js/script.js` - Interactive features

### Customization
- Modify colors in `style.css` (look for `:root` variables)
- Add new crops in disease detection dropdown
- Customize market prices in the database
- Add new activity types in farm log

## 🌟 Next Steps

1. **Test All Features** - Explore each section
2. **Upload Real Data** - Add your actual farm information
3. **Track Progress** - Use the dashboard to monitor activities
4. **Customize** - Modify to fit your specific needs
5. **Share Feedback** - Report any issues or suggestions

## 📞 Support

If you encounter issues:
1. Check this guide
2. Review README.md for detailed information
3. Verify Python and dependencies are installed
4. Try restarting the application

---

**Happy Farming! 🌾**

Start making data-driven farming decisions with AI-Farm!
