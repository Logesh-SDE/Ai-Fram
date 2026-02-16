@echo off
echo ==========================================
echo   AI-Farm - Smart Farming Assistant
echo ==========================================
echo.

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting AI-Farm application...
echo.
echo Access the application at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python app.py
pause
