# Crop Advisor - Testing & Troubleshooting Guide

## ✅ How to Test Crop Advisor

### Step 1: Start the Application
```bash
python app.py
```

### Step 2: Login
- Go to: http://localhost:5000
- Login with your account (or admin/admin123)

### Step 3: Navigate to Crop Advisor
- Click on "Crop Advisor" in the menu
- OR visit: http://localhost:5000/crop-recommendations

### Step 4: Fill the Form
1. **Soil Type**: Select any (Loamy, Clay, Sandy, Silt, Peaty, Chalky)
2. **Season**: Select any (Summer, Monsoon, Winter)
3. **Rainfall**: Select any (Low, Medium, High)
4. Click **"Get Recommendations"**

### Step 5: View Results
- Results appear on the right side
- Shows 4-5 recommended crops
- Each with: Suitability level, Expected yield, Growing period

## 🔍 What Should Happen

### Expected Flow:
```
1. User fills form
   ↓
2. Click "Get Recommendations"
   ↓
3. Shows "Analyzing..." spinner
   ↓
4. Fetches data from server
   ↓
5. Displays crop recommendations
   ↓
6. Shows suitability badges
   ↓
7. Shows yield and duration
```

### Example Output:
```
Recommended Crops

┌─────────────────────────────┐
│ Tomato              [High]  │
│ ✓ Expected Yield: 35 tons/ha
│ ⏱ Growing Period: 90 days
└─────────────────────────────┘

┌─────────────────────────────┐
│ Cucumber          [High]    │
│ ✓ Expected Yield: 42 tons/ha
│ ⏱ Growing Period: 75 days
└─────────────────────────────┘
```

## 🐛 Troubleshooting

### Problem 1: Page Not Loading

**Symptoms:**
- Blank page
- 404 error
- "Page not found"

**Solutions:**
1. Check if server is running:
   ```bash
   python app.py
   ```
   Should show: "Running on http://127.0.0.1:5000"

2. Make sure you're logged in:
   - Visit http://localhost:5000/login
   - Login first

3. Check the URL:
   - Correct: http://localhost:5000/crop-recommendations
   - Wrong: http://localhost:5000/crop-advisor

### Problem 2: Form Not Submitting

**Symptoms:**
- Click button, nothing happens
- No loading spinner
- No results

**Solutions:**
1. Open browser console (F12)
2. Check for JavaScript errors
3. Make sure all form fields are filled
4. Try different browser (Chrome, Firefox)

### Problem 3: "Error loading recommendations"

**Symptoms:**
- Red error message
- "Error loading recommendations. Please try again."

**Solutions:**
1. Check server terminal for errors
2. Make sure database exists:
   ```bash
   ls -la aifarm.db
   ```
3. Restart the application:
   ```bash
   python app.py
   ```

### Problem 4: Results Not Showing

**Symptoms:**
- Loading spinner stays forever
- Results section appears but empty

**Solutions:**
1. Check browser console (F12) for errors
2. Verify the route exists:
   ```bash
   grep "get_crop_recommendations" app.py
   ```
3. Test the endpoint directly:
   - Open browser
   - Visit: http://localhost:5000/get-crop-recommendations
   - Should require POST method

### Problem 5: Database Error

**Symptoms:**
- "Database is locked"
- SQL errors in terminal

**Solutions:**
1. Close any database viewers
2. Delete and recreate database:
   ```bash
   rm aifarm.db
   python app.py
   ```
3. Make sure only one instance of app is running

## 🧪 Manual Testing Steps

### Test 1: Loamy Soil + Summer
```
Soil: Loamy
Season: Summer
Rainfall: Medium

Expected: Tomato, Cucumber, Corn, Watermelon
```

### Test 2: Clay Soil + Winter
```
Soil: Clay
Season: Winter
Rainfall: Low

Expected: Wheat, Barley, Mustard, Chickpea
```

### Test 3: Sandy Soil + Monsoon
```
Soil: Sandy
Season: Monsoon
Rainfall: High

Expected: Millets, Pulses, Groundnut
```

### Test 4: All Soil Types
Try each soil type:
- Loamy ✓
- Clay ✓
- Sandy ✓
- Silt ✓
- Peaty ✓
- Chalky ✓

## 📊 Verification Checklist

- [ ] Can access /crop-recommendations page
- [ ] Form displays correctly
- [ ] All dropdowns work
- [ ] Submit button is clickable
- [ ] Loading spinner appears
- [ ] Results display in < 2 seconds
- [ ] Crop names show correctly
- [ ] Suitability badges have colors
- [ ] Yield numbers appear
- [ ] Duration shows in days
- [ ] Can submit multiple times
- [ ] Different selections give different results
- [ ] Info cards display at bottom
- [ ] Page is responsive on mobile

## 🔧 Developer Debugging

### Check Route Registration:
```python
# In app.py
@app.route('/crop-recommendations')
@login_required
def crop_recommendations():
    return render_template('crop_recommendations.html')

@app.route('/get-crop-recommendations', methods=['POST'])
@login_required
def get_crop_recommendations():
    # Process and return recommendations
```

### Check Template Path:
```bash
ls -la templates/crop_recommendations.html
```

### Check Function Exists:
```bash
grep "def simulate_crop_recommendations" app.py
```

### Test Database Connection:
```python
python3
>>> import sqlite3
>>> conn = sqlite3.connect('aifarm.db')
>>> c = conn.cursor()
>>> c.execute("SELECT * FROM crop_recommendations LIMIT 1")
>>> print(c.fetchall())
>>> conn.close()
```

## 📝 Common Issues & Fixes

### Issue: "This page isn't working"
**Fix:** Check login status, restart server

### Issue: Spinner never stops
**Fix:** Check network tab in browser console

### Issue: Wrong recommendations
**Fix:** This is expected - it's simulated AI data

### Issue: CSS not loading
**Fix:** Hard refresh (Ctrl+Shift+R) or clear cache

### Issue: JavaScript errors
**Fix:** Check for missing quotes or brackets in template

## ✨ Features Working Correctly

When everything works, you should see:

✅ **Form Section:**
- Clean input form
- Three dropdowns
- Primary button
- Proper spacing

✅ **Results Section:**
- Animated appearance
- Grid of crop cards
- Color-coded badges
- Icons for yield/duration
- Hover effects

✅ **Info Section:**
- Two info cards
- Tips and how-it-works
- Checkmarks on lists
- Green gradient background

✅ **Responsive:**
- Works on desktop
- Adapts to tablet
- Mobile-friendly
- Sticky form on desktop

## 🎯 Success Indicators

If you see all these, it's working:

1. ✅ Page loads without errors
2. ✅ Form is fillable
3. ✅ Button submits
4. ✅ Spinner shows briefly
5. ✅ Results appear
6. ✅ Crops listed with details
7. ✅ Badges are colored
8. ✅ No console errors
9. ✅ Can submit again
10. ✅ Data saves to database

## 📞 Still Having Issues?

1. **Check browser console** (F12 → Console tab)
2. **Check server terminal** for Python errors
3. **Verify all files exist**:
   - templates/crop_recommendations.html ✓
   - app.py with routes ✓
   - static/css/style.css ✓
4. **Clear browser cache**: Ctrl+Shift+Delete
5. **Try incognito/private mode**
6. **Restart everything**:
   ```bash
   # Stop server (Ctrl+C)
   # Restart
   python app.py
   ```

## 🎉 Working Example

**Input:**
```
Soil Type: Loamy
Season: Summer
Rainfall: Medium
```

**Output:**
```
✅ Recommended Crops

🌱 Tomato                    [High Suitability]
   Expected Yield: 35 tons/hectare
   Growing Period: 90 days

🌱 Cucumber                  [High Suitability]
   Expected Yield: 38 tons/hectare
   Growing Period: 75 days

🌱 Corn                      [Medium Suitability]
   Expected Yield: 42 tons/hectare
   Growing Period: 110 days

🌱 Watermelon                [Medium Suitability]
   Expected Yield: 40 tons/hectare
   Growing Period: 85 days

🌱 Bell Pepper               [Moderate Suitability]
   Expected Yield: 32 tons/hectare
   Growing Period: 95 days
```

---

**If it works:** Great! 🎉 You can now get crop recommendations!

**If it doesn't:** Follow the troubleshooting steps above or check the specific error message.
