# 🌤️ Smart Weather System

> **AI-Powered Weather Intelligence Platform with Real-Time Forecasting, NASA Integration & Hardware Support**

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Deploy](https://img.shields.io/badge/Deploy-Railway-purple.svg)](https://railway.app)
[![Status](https://img.shields.io/badge/Status-Production-success.svg)]()

---

## 🎯 Live Demo

**🌐 Deployed Application:** [https://smart-weather-system-production.up.railway.app](https://smart-weather-system-production.up.railway.app)

**🔑 Demo Credentials:**
- **Username:** `admin`
- **Password:** `admin123`

---

## 📸 Screenshots

### 🏠 Dashboard - Real-Time Weather Intelligence
![Dashboard](screenshots/dashboard.png)

*Beautiful gradient theme displaying current weather (21.5°C in London), recent history with timestamps, and customizable alert system. Features clean white cards on purple gradient background with real-time updates.*

### 🔔 Smart Alert Management System
![Alerts Management](screenshots/alerts.png)

*Create custom weather alerts with intuitive form. Set temperature, humidity, wind, or pressure thresholds with above/below conditions. Purple gradient interface makes alert configuration simple and visual.*

### 🛡️ Admin Dashboard - System Overview
![Admin Dashboard](screenshots/admin.png)

*Comprehensive admin panel showing 1 total user, 51 weather records, 0 active alerts, and 100% system health. Includes recent users table with email and location, plus system information displaying version 2.0.0, SQLite database, OpenWeatherMap API, and NASA API connection status.*

---

## ✨ Key Features

### 🧠 AI-Powered Weather Intelligence
- **Machine Learning Predictions** - Advanced forecasting using scikit-learn
- **Real-Time Data Processing** - Live weather updates every 2 seconds
- **Confidence Scoring** - Accuracy tracking for AI predictions
- **Historical Analysis** - Pattern recognition from weather history

### 🔔 Smart Alert System
- **Custom Thresholds** - Set alerts for temperature, humidity, wind, pressure
- **Multi-Parameter Monitoring** - Track multiple weather conditions
- **Instant Notifications** - WebSocket-powered real-time alerts
- **User-Specific Alerts** - Personalized alert management for each user

### 🛰️ Live Satellite Imagery
- **Real-Time Maps** - Current weather visualization with lazy loading
- **Multiple Layers:**
  - ☁️ Precipitation & Cloud Coverage
  - 🌡️ Temperature Distribution Maps
  - 💨 Wind Speed & Direction Patterns
  - 🌀 Atmospheric Pressure Systems
- **OpenWeatherMap API** - High-quality satellite data

### 🚀 NASA Integration
- **Astronomy Picture of the Day (APOD)** - Daily stunning space imagery
- **Earth Satellite Views** - Real-time Earth observation data
- **Mars Weather Data** - Curiosity rover weather reports from Mars
- **Space Weather Insights** - Solar activity and space weather monitoring

### 🔌 Arduino Hardware Support
- **DHT22 Sensor Integration** - Real temperature & humidity monitoring
- **Real-Time Data Streaming** - Live sensor readings via serial port
- **Serial Communication Protocol** - USB connection to Arduino Uno
- **Plug-and-Play Setup** - Easy hardware configuration with COM port detection

### 👥 Multi-User Platform
- **Individual User Accounts** - Secure authentication and personalized tracking
- **Location-Based Weather** - City-specific weather information for each user
- **Customizable Preferences** - User settings, themes, and alert configurations
- **Admin Dashboard** - Complete system management with user analytics

### 🎨 Modern User Experience
- **Beautiful Purple Gradient UI** - Professional design with smooth animations
- **Dark/Light Mode Toggle** - Floating theme switcher button (bottom-right)
- **Fully Responsive Design** - Works perfectly on desktop, tablet, and mobile
- **Intuitive Navigation** - Clean organized interface with icon-based menu
- **Accessibility Focused** - WCAG compliant design principles

---

## 🛠️ Technology Stack

### Backend Technologies
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.13 | Core programming language |
| **Flask** | 3.0.0 | Web application framework |
| **Flask-SocketIO** | 5.3.6 | Real-time WebSocket communication |
| **SQLite** | 3 | Lightweight embedded database |
| **Eventlet** | 0.35.2 | Concurrent networking library |

### Frontend Technologies
| Technology | Purpose |
|------------|---------|
| **HTML5/CSS3** | Modern semantic markup and styling |
| **JavaScript (ES6+)** | Interactive client-side functionality |
| **Socket.IO** | Real-time bidirectional communication |
| **Font Awesome 6.4.0** | Professional icon library |
| **CSS Grid & Flexbox** | Responsive layout system |

### APIs & External Services
| Service | Purpose | Documentation |
|---------|---------|---------------|
| **OpenWeatherMap API** | Current weather data | [docs](https://openweathermap.org/api) |
| **NASA API** | Space imagery and data | [docs](https://api.nasa.gov/) |
| **Railway Platform** | Cloud hosting and deployment | [docs](https://docs.railway.app/) |

### Data Science & Machine Learning
| Library | Version | Purpose |
|---------|---------|---------|
| **scikit-learn** | 1.4.0 | Machine learning models for predictions |
| **pandas** | 2.1.4 | Data manipulation and analysis |
| **numpy** | 1.26.3 | Numerical computing and arrays |

### Hardware Integration
| Component | Purpose | Cost |
|-----------|---------|------|
| **Arduino Uno** | Microcontroller board | ~$25 |
| **DHT22 Sensor** | Temperature/humidity sensor | ~$5 |
| **pyserial** | Serial communication library | Free |
| **Jumper Wires** | Sensor connections | ~$2 |

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11 or higher
- pip package manager
- Git version control
- Arduino IDE (optional, for hardware)

### Local Installation

**1. Clone the Repository**
```bash
git clone https://github.com/Khan-Feroz211/Smart_weather_system.git
cd Smart_weather_system
```

**2. Create Virtual Environment** (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Linux/Mac
source venv/bin/activate
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure Environment Variables**

Create a `.env` file in the root directory:

```env
# ==================== API KEYS ====================
# Get free API keys from the links below
OPENWEATHER_API_KEY=your_openweather_api_key_here
NASA_API_KEY=your_nasa_api_key_here

# ==================== SECURITY ====================
FLASK_SECRET_KEY=your_random_secret_key_here

# ==================== CONFIGURATION ====================
HARDWARE_MODE=False
ARDUINO_PORT=COM3
DEBUG_MODE=True
DATABASE_PATH=database/weather.db
HOST=0.0.0.0
PORT=5000
```

**5. Get Free API Keys**

**OpenWeatherMap API:**
1. Visit [https://openweathermap.org/api](https://openweathermap.org/api)
2. Click "Sign Up" → Create free account
3. Go to "API Keys" section
4. Copy your API key

**NASA API:**
1. Visit [https://api.nasa.gov/](https://api.nasa.gov/)
2. Fill out the form to generate API key
3. Check your email for the key
4. Copy to `.env` file

**6. Run the Application**
```bash
python app.py
```

**7. Open in Browser**
Navigate to: `http://localhost:5000`

**8. Login with Demo Credentials**
- **Username:** `admin`
- **Password:** `admin123`

---

## 🔌 Arduino Hardware Setup (Optional)

### Required Hardware Components

| Item | Quantity | Approx. Cost | Where to Buy |
|------|----------|--------------|--------------|
| Arduino Uno R3 | 1 | $25 | Amazon, Arduino.cc |
| DHT22 Sensor | 1 | $5 | Amazon, Adafruit |
| Jumper Wires (Male-Male) | 3 | $2 | Amazon, local electronics |
| Breadboard (Optional) | 1 | $3 | Amazon, Adafruit |
| **Total** | | **~$35** | |

### Wiring Diagram

```
DHT22 Temperature & Humidity Sensor Pinout:
┌─────────────────────┐
│      DHT22          │
│  (Front View)       │
├─────────────────────┤
│                     │
│  Pin 1: VCC  ───────┼─────► Arduino 5V (Red Wire)
│  Pin 2: DATA ───────┼─────► Arduino Digital Pin 2 (Yellow Wire)
│  Pin 3: NC          │       (Not Connected)
│  Pin 4: GND  ───────┼─────► Arduino GND (Black Wire)
│                     │
└─────────────────────┘

Connection Summary:
DHT22 VCC  → Arduino 5V
DHT22 DATA → Arduino Pin 2
DHT22 GND  → Arduino GND
```

### Step-by-Step Arduino Setup

**Step 1: Install Arduino IDE**

Download and install from: [https://www.arduino.cc/en/software](https://www.arduino.cc/en/software)

**Step 2: Install Required Libraries**

1. Open Arduino IDE
2. Go to: `Sketch → Include Library → Manage Libraries`
3. Search for: **"DHT sensor library"**
4. Select: **"DHT sensor library by Adafruit"**
5. Click **"Install All"** (installs DHT library + dependencies)

**Step 3: Wire the Sensor**

Follow the wiring diagram above to connect:
- Red wire: VCC to 5V
- Yellow wire: DATA to Pin 2
- Black wire: GND to GND

**Step 4: Upload Arduino Sketch**

1. Open file: `hardware/arduino/weather_sensor.ino`
2. Connect Arduino to computer via USB cable
3. Select Board: `Tools → Board → Arduino Uno`
4. Select Port: `Tools → Port → COM3` (Windows) or `/dev/ttyUSB0` (Linux)
5. Click the **Upload** button (→)
6. Wait for "Done uploading" message

**Step 5: Find Your COM Port**

**Windows:**
- Open Device Manager
- Expand "Ports (COM & LPT)"
- Look for "Arduino Uno (COM3)" or similar
- Note the COM number (e.g., COM3, COM4)

**Mac:**
```bash
ls /dev/tty.usb*
# Output example: /dev/tty.usbmodem14201
```

**Linux:**
```bash
ls /dev/ttyUSB*
# Output example: /dev/ttyUSB0
```

**Step 6: Test Arduino Connection**

1. Open Serial Monitor: `Tools → Serial Monitor`
2. Set baud rate: **9600** (bottom-right dropdown)
3. You should see JSON data streaming every 2 seconds:

```json
{"temperature": 22.5, "humidity": 45.0, "pressure": 1013, "source": "arduino"}
{"temperature": 22.6, "humidity": 44.8, "pressure": 1013, "source": "arduino"}
```

**Step 7: Enable Hardware Mode in Flask App**

Update your `.env` file:
```env
HARDWARE_MODE=True
ARDUINO_PORT=COM3
```

**Step 8: Restart Flask Application**
```bash
python app.py
```

Arduino sensor data will now appear in your dashboard alongside API weather data! 🎉

### Troubleshooting Arduino Issues

| Problem | Solution |
|---------|----------|
| **Port not found** | Check Device Manager (Windows) or `ls /dev/tty*` (Mac/Linux). Ensure Arduino is plugged in. |
| **Upload failed** | Install CH340 USB drivers for Arduino clones from: [https://sparks.gogo.co.nz/ch340.html](https://sparks.gogo.co.nz/ch340.html) |
| **No sensor data** | 1. Check wiring connections<br>2. Verify DHT22 sensor orientation<br>3. Test with different USB cable |
| **"Permission denied"** | Close Arduino IDE Serial Monitor before running Flask app. Only one program can access COM port at a time. |
| **Wrong temperature readings** | DHT22 needs 2-second intervals between reads. Sketch already handles this. If still wrong, sensor may be faulty. |

---

## 🚂 Railway Deployment Guide

Deploy your Smart Weather System to the cloud in **5 minutes** with Railway's free tier!

### Prerequisites
- GitHub account
- Railway account (sign up at [railway.app](https://railway.app))
- Your code pushed to GitHub

### Deployment Steps

**Step 1: Access Railway**

Visit: [https://railway.app/new](https://railway.app/new)

**Step 2: Authenticate with GitHub**

1. Click **"Login with GitHub"**
2. Authorize Railway to access your repositories
3. Complete authentication

**Step 3: Deploy from GitHub Repository**

1. Click **"Deploy from GitHub repo"**
2. Select repository: **`Khan-Feroz211/Smart_weather_system`**
3. Click **"Deploy Now"**
4. Railway will automatically detect Flask and start building

**Step 4: Add Environment Variables** (Critical!)

1. Click on your project name in Railway dashboard
2. Navigate to **"Variables"** tab
3. Click **"+ New Variable"** button
4. Add each variable below **one by one**:

```
Variable Name: OPENWEATHER_API_KEY
Value: 7abebf46599844601faf1c220d94e4ed
```

```
Variable Name: NASA_API_KEY
Value: gFRv2vaNMPBmXm8desW71hN1ZJbC12WqpEt99XJf
```

```
Variable Name: FLASK_SECRET_KEY
Value: railway-production-secret-2024-your-random-string
```

```
Variable Name: HARDWARE_MODE
Value: False
```

```
Variable Name: DEBUG_MODE
Value: False
```

```
Variable Name: DATABASE_PATH
Value: /tmp/weather.db
```

```
Variable Name: HOST
Value: 0.0.0.0
```

**Important Notes:**
- Railway automatically sets the `PORT` variable
- Use `/tmp/` for DATABASE_PATH on Railway (ephemeral storage)
- Don't include quotes around values

**Step 5: Generate Public Domain**

1. Click **"Settings"** tab in Railway dashboard
2. Scroll down to **"Networking"** section
3. Click **"Generate Domain"** button
4. Railway will create a public HTTPS URL like:

```
https://smart-weather-system-production.up.railway.app
```

**Step 6: Monitor Deployment**

1. Click **"Deployments"** tab
2. Click on the latest deployment (top of list)
3. Click **"View Logs"** to see build progress
4. Wait for these success messages:

```
✅ Build successful
✅ Starting application...
============================================================
[START] Smart Weather System - Multi-User Edition
============================================================
[INFO] Port: 8000
[WEB] Open browser to: http://localhost:8000
============================================================
```

Deployment typically takes **2-3 minutes**.

**Step 7: Access Your Live Application!**

1. Copy your generated Railway URL
2. Open in browser
3. You should see the login page
4. Login with: `admin` / `admin123`

🎉 **Congratulations! Your app is now live with HTTPS!**

### Railway Deployment Checklist

Before deploying, ensure:

- [x] All code committed and pushed to GitHub
- [x] `requirements.txt` file exists and is up-to-date
- [x] `railway.json` configuration file present
- [x] `Procfile` exists with correct start command
- [x] `.gitignore` excludes `.env` file
- [x] All environment variables added in Railway
- [x] Domain generated in Railway settings

### Post-Deployment Verification

After deployment, test these features:

- [ ] Can access the Railway URL
- [ ] Login page loads with beautiful purple gradient
- [ ] Can login successfully with admin credentials
- [ ] Dashboard displays current weather data
- [ ] Satellite page loads all 4 weather maps
- [ ] Alerts page allows creating new alerts
- [ ] Admin dashboard shows system statistics
- [ ] Settings page allows updating user preferences
- [ ] Theme toggle button works (dark/light mode)

### Continuous Deployment

Railway automatically redeploys when you push to GitHub:

```bash
# Make changes locally
git add .
git commit -m "Updated feature X"
git push origin main

# Railway automatically:
# 1. Detects the push
# 2. Rebuilds the application
# 3. Redeploys with zero downtime
# 4. Updates your live URL
```

No manual intervention needed!

### Railway Dashboard Features

| Feature | Location | Purpose |
|---------|----------|---------|
| **View Logs** | Deployments → Click deployment → View Logs | Debug issues, see print statements |
| **Metrics** | Metrics tab | CPU, memory, bandwidth usage |
| **Custom Domain** | Settings → Networking | Add your own domain name |
| **Environment Vars** | Variables tab | Update API keys, settings |
| **Rollback** | Deployments → ⋯ menu → Redeploy | Return to previous version |
| **Delete Service** | Settings → Danger | Permanently delete project |

### Troubleshooting Railway Deployment

**Issue: "Application Error" / 502 Bad Gateway**

**Solutions:**
1. Check deployment logs for errors:
   - Go to: Deployments → Latest → View Logs
   - Look for Python tracebacks or error messages

2. Verify all environment variables are set:
   - Check Variables tab
   - Ensure no typos in variable names
   - Values should not have quotes

3. Database path issue:
   - Make sure `DATABASE_PATH=/tmp/weather.db`
   - Railway uses ephemeral storage

**Issue: "Build Failed"**

**Solutions:**
1. Check `requirements.txt` syntax:
   - Ensure all dependencies listed
   - No version conflicts
   - Use `==` for exact versions

2. Python version compatibility:
   - Railway uses Python 3.11 by default
   - Ensure your code is compatible

3. Check build logs:
   - Look for specific package installation errors

**Issue: "Can't Access Application"**

**Solutions:**
1. Verify domain is generated:
   - Settings → Networking → Generate Domain

2. Check deployment status:
   - Should show green checkmark ✓
   - If red X, check logs for errors

3. Wait for initial deployment:
   - First deployment takes 3-5 minutes
   - Subsequent deploys are faster (1-2 min)

**Issue: "Port Already in Use"**

**Solution:**
- Don't set PORT in environment variables
- Railway automatically assigns and manages PORT

**Issue: "Database/Data Lost After Redeploy"**

**Explanation:**
- Railway uses ephemeral storage at `/tmp/`
- Database resets on every deployment
- This is normal for free tier

**Solutions for Persistent Data:**
1. Upgrade to Railway Pro and use persistent volumes
2. Use external database (PostgreSQL on Railway)
3. Use cloud database (Supabase, PlanetScale)

### Railway Free Tier Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| **Execution Hours** | 500 hours/month | Plenty for personal projects |
| **Memory** | 512 MB | Sufficient for Flask apps |
| **CPU** | Shared | Fair usage policy |
| **Storage** | Ephemeral | Data resets on redeploy |
| **Bandwidth** | 100 GB/month | Generous for most apps |
| **Build Time** | 5 minutes max | Usually completes in 2-3 min |

---

## 📚 API Documentation

### Weather Data API

#### Get Current Weather for City

**Endpoint:** `/api/weather/<city>`  
**Method:** `GET`  
**Authentication:** None required

**Example Request:**
```bash
curl https://your-app.railway.app/api/weather/London
```

**Example Response:**
```json
{
  "temperature": 21.5,
  "humidity": 49,
  "pressure": 1024,
  "wind_speed": 11.2,
  "conditions": "Cloudy",
  "icon": "04d",
  "city": "London",
  "country": "GB",
  "timestamp": "2026-01-17T22:45:30Z"
}
```

**Response Fields:**
- `temperature` (float): Temperature in Celsius
- `humidity` (int): Relative humidity percentage (0-100)
- `pressure` (int): Atmospheric pressure in hPa
- `wind_speed` (float): Wind speed in km/h
- `conditions` (string): Weather description (e.g., "Cloudy", "Clear sky")
- `icon` (string): Weather icon code for displaying conditions
- `timestamp` (string): ISO 8601 formatted timestamp

### Arduino Hardware API

#### Check Arduino Connection Status

**Endpoint:** `/api/arduino/status`  
**Method:** `GET`  
**Authentication:** Session required (must be logged in)

**Example Request:**
```bash
curl -X GET https://your-app.railway.app/api/arduino/status \
  -H "Cookie: session=your_session_cookie"
```

**Example Response (Connected):**
```json
{
  "connected": true,
  "port": "COM3",
  "sensor": "DHT22",
  "status": "online",
  "last_reading": "2026-01-17T22:45:30Z"
}
```

**Example Response (Disconnected):**
```json
{
  "connected": false,
  "status": "offline",
  "message": "Hardware mode disabled or no Arduino detected"
}
```

#### Get Latest Sensor Data

**Endpoint:** `/api/arduino/data`  
**Method:** `GET`  
**Authentication:** Session required

**Example Response:**
```json
{
  "temperature": 22.5,
  "humidity": 45.0,
  "pressure": 1013,
  "source": "arduino",
  "timestamp": "2026-01-17T22:45:30Z",
  "sensor_type": "DHT22"
}
```

### NASA Space Data API

#### Astronomy Picture of the Day

**Endpoint:** `/api/nasa/apod`  
**Method:** `GET`  
**Authentication:** None required

**Example Response:**
```json
{
  "title": "Nebula in Orion",
  "date": "2026-01-17",
  "explanation": "The Orion Nebula is a diffuse nebula...",
  "url": "https://apod.nasa.gov/apod/image/2601/orion_4k.jpg",
  "hdurl": "https://apod.nasa.gov/apod/image/2601/orion_8k.jpg",
  "media_type": "image",
  "copyright": "NASA/ESA"
}
```

#### Earth Satellite Imagery

**Endpoint:** `/api/nasa/earth`  
**Method:** `GET`  
**Query Parameters:**
- `lat` (required): Latitude (-90 to 90)
- `lon` (required): Longitude (-180 to 180)
- `date` (optional): Date in YYYY-MM-DD format

**Example Request:**
```bash
curl "https://your-app.railway.app/api/nasa/earth?lat=51.5074&lon=-0.1278"
```

**Example Response:**
```json
{
  "date": "2026-01-17",
  "url": "https://api.nasa.gov/planetary/earth/imagery?lon=-0.1278&lat=51.5074",
  "cloud_score": 0.15,
  "location": {
    "latitude": 51.5074,
    "longitude": -0.1278
  }
}
```

### Weather Alerts API

#### Create New Alert

**Endpoint:** `/alerts`  
**Method:** `POST`  
**Authentication:** Session required  
**Content-Type:** `application/x-www-form-urlencoded`

**Request Body:**
```
alert_type=temperature&condition=above&threshold=30
```

**Parameters:**
- `alert_type`: One of `temperature`, `humidity`, `wind_speed`, `pressure`
- `condition`: One of `above`, `below`
- `threshold`: Numeric value for the alert threshold

**Example Response:**
```json
{
  "success": true,
  "message": "Alert created successfully",
  "alert_id": 42
}
```

#### Delete Alert

**Endpoint:** `/alerts`  
**Method:** `POST`  
**Authentication:** Session required  
**Content-Type:** `application/x-www-form-urlencoded`

**Request Body:**
```
delete_id=42
```

**Example Response:**
```json
{
  "success": true,
  "message": "Alert deleted successfully"
}
```

#### List User Alerts

**Endpoint:** `/api/alerts`  
**Method:** `GET`  
**Authentication:** Session required

**Example Response:**
```json
{
  "alerts": [
    {
      "id": 1,
      "alert_type": "temperature",
      "condition": "above",
      "threshold": 30.0,
      "is_active": true,
      "created_at": "2026-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "alert_type": "humidity",
      "condition": "below",
      "threshold": 30.0,
      "is_active": true,
      "created_at": "2026-01-16T14:20:00Z"
    }
  ],
  "total_count": 2
}
```

### WebSocket Events

The application uses Socket.IO for real-time updates.

#### Connect to WebSocket

```javascript
const socket = io('https://your-app.railway.app');

socket.on('connect', () => {
  console.log('Connected to weather system');
});
```

#### Weather Update Event

**Event Name:** `weather_update`

**Payload Example:**
```json
{
  "temperature": 21.5,
  "humidity": 49,
  "timestamp": "2026-01-17T22:45:30Z",
  "city": "London"
}
```

**Client-Side Handler:**
```javascript
socket.on('weather_update', (data) => {
  console.log('New weather data:', data);
  updateWeatherDisplay(data);
});
```

#### Alert Triggered Event

**Event Name:** `alert_triggered`

**Payload Example:**
```json
{
  "alert_id": 1,
  "alert_type": "temperature",
  "threshold": 30.0,
  "current_value": 31.5,
  "message": "Temperature alert: 31.5°C exceeds threshold of 30.0°C"
}
```

---

## 🎨 Features Showcase

### Dashboard Features
✅ **Real-Time Weather Updates** - Live data every 2 seconds via WebSocket  
✅ **Current Weather Display** - Large temperature, weather icon, conditions  
✅ **Weather Statistics** - Humidity, wind speed, pressure indicators  
✅ **AI Predictions** - Machine learning temperature forecasts  
✅ **Recent History** - Last 5 weather readings with timestamps  
✅ **Active Alerts Preview** - Quick view of configured alerts  
✅ **Beautiful Animations** - Smooth card transitions and hover effects  
✅ **Gradient Background** - Purple-to-violet aesthetic  

### Alert Management Features
✅ **Temperature Alerts** - Set thresholds for hot/cold conditions  
✅ **Humidity Alerts** - Monitor moisture levels  
✅ **Wind Speed Alerts** - Track strong wind conditions  
✅ **Pressure Alerts** - Detect pressure changes  
✅ **Custom Thresholds** - Set any numeric value  
✅ **Above/Below Conditions** - Flexible alert logic  
✅ **Visual Status Indicators** - Green (active) / Red (inactive) badges  
✅ **One-Click Delete** - Easy alert management  

### Satellite Imagery Features
✅ **4 Weather Map Types** - Precipitation, temperature, wind, pressure  
✅ **Lazy Loading** - Images load on demand for faster performance  
✅ **Loading Indicators** - Animated spinners while images fetch  
✅ **Error Handling** - Graceful fallbacks if images fail  
✅ **Hover Zoom Effect** - Interactive map exploration  
✅ **Real-Time Data** - Current weather conditions  

### Admin Dashboard Features
✅ **User Statistics** - Total users, weather records, active alerts  
✅ **System Health Monitoring** - 100% uptime indicator  
✅ **Recent Users Table** - Username, email, city, join date  
✅ **System Information** - Version, database, API status  
✅ **Color-Coded Stats Cards** - Blue, green, orange, purple themes  
✅ **Responsive Layout** - Adapts to all screen sizes  

### Settings Features
✅ **Change City** - Update weather location  
✅ **Update Email** - Modify contact information  
✅ **Theme Preferences** - Dark/light/auto mode selection  
✅ **Profile Information** - View account details  
✅ **Join Date Display** - Member since timestamp  
✅ **Danger Zone** - Account deletion option  

### Navigation Features
✅ **Icon-Based Menu** - Clear dashboard, alerts, satellite, admin, settings, logout  
✅ **Responsive Navbar** - Collapses to hamburger menu on mobile  
✅ **Active Page Indicator** - Highlighted current page  
✅ **Floating Theme Toggle** - Dark/light mode switcher (bottom-right)  
✅ **Smooth Transitions** - Animated page navigation  

---

## 🔧 Configuration & Customization

### Environment Variables Reference

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `OPENWEATHER_API_KEY` | String | - | ✅ Yes | API key from OpenWeatherMap |
| `NASA_API_KEY` | String | - | ✅ Yes | API key from NASA |
| `FLASK_SECRET_KEY` | String | - | ✅ Yes | Secret key for Flask sessions |
| `HARDWARE_MODE` | Boolean | False | No | Enable Arduino sensor integration |
| `ARDUINO_PORT` | String | COM3 | No | Serial port for Arduino connection |
| `DEBUG_MODE` | Boolean | False | No | Enable Flask debug mode |
| `DATABASE_PATH` | String | database/weather.db | No | Path to SQLite database file |
| `HOST` | String | 0.0.0.0 | No | Server bind address |
| `PORT` | Integer | 5000 | No | Server port (Railway sets automatically) |

### Database Schema Documentation

**Users Table:**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT,
    city TEXT NOT NULL DEFAULT 'London',
    theme TEXT DEFAULT 'dark',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Weather Data Table:**
```sql
CREATE TABLE weather_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    temperature REAL NOT NULL,
    humidity REAL NOT NULL,
    pressure REAL NOT NULL,
    wind_speed REAL NOT NULL,
    conditions TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

**Alerts Table:**
```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    alert_type TEXT NOT NULL,
    condition TEXT NOT NULL,
    threshold REAL NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Customization Options

#### Change Default City
Edit `.env` file:
```env
DEFAULT_CITY=New York
```

Or modify in `app.py`:
```python
DEFAULT_CITY = os.getenv('DEFAULT_CITY', 'London')
```

#### Adjust Weather Update Interval
In `static/js/main.js`:
```javascript
// Default: 5 minutes (300000 ms)
setInterval(() => {
    location.reload();
}, 300000);

// Change to 2 minutes:
setInterval(() => {
    location.reload();
}, 120000);
```

#### Customize Theme Colors
Edit `templates/base.html` CSS variables:
```css
:root {
    --primary: #667eea;      /* Purple gradient start */
    --secondary: #764ba2;    /* Purple gradient end */
    --success: #10b981;      /* Green for success */
    --danger: #ef4444;       /* Red for errors */
    --warning: #f59e0b;      /* Orange for warnings */
}
```

#### Add New Alert Types
In `app.py`, add to alert types:
```python
ALERT_TYPES = ['temperature', 'humidity', 'wind_speed', 'pressure', 'visibility']
```

Then update the alerts form in `templates/alerts.html`:
```html
<option value="visibility">Visibility (km)</option>
```

---

## 🤝 Contributing

We welcome contributions from the community! Whether it's bug fixes, new features, documentation improvements, or translations, every contribution helps make Smart Weather System better.

### How to Contribute

**1. Fork the Repository**
- Visit [https://github.com/Khan-Feroz211/Smart_weather_system](https://github.com/Khan-Feroz211/Smart_weather_system)
- Click the "Fork" button (top-right)
- Clone your fork locally:
```bash
git clone https://github.com/YOUR_USERNAME/Smart_weather_system.git
cd Smart_weather_system
```

**2. Create a Feature Branch**
```bash
git checkout -b feature/amazing-new-feature
```

Use descriptive branch names:
- `feature/add-7day-forecast`
- `bugfix/fix-alert-notification`
- `docs/update-installation-guide`

**3. Set Up Development Environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install pytest black flake8
```

**4. Make Your Changes**

Follow these guidelines:
- Write clean, readable code
- Follow PEP 8 style guide for Python
- Add comments for complex logic
- Update documentation if needed
- Test your changes thoroughly

**5. Test Your Changes**
```bash
# Run the application
python app.py

# Test in browser
# Open http://localhost:5000
# Verify your changes work as expected
```

**6. Commit Your Changes**
```bash
git add .
git commit -m "Add amazing new feature

- Detailed description of what changed
- Why the change was needed
- Any breaking changes or considerations"
```

**7. Push to Your Fork**
```bash
git push origin feature/amazing-new-feature
```

**8. Create Pull Request**
- Go to your fork on GitHub
- Click "Pull Request" button
- Select base: `main` ← compare: `feature/amazing-new-feature`
- Fill out the PR template:
  - What does this PR do?
  - Why is this change needed?
  - How has it been tested?
  - Screenshots (if UI changes)

### Contribution Guidelines

**Code Style:**
- Follow PEP 8 for Python code
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters
- Use meaningful variable and function names

**Commit Messages:**
- Use present tense: "Add feature" not "Added feature"
- First line: Brief summary (50 chars or less)
- Leave a blank line
- Detailed description if needed
- Reference issues: "Fixes #123"

**Pull Request Checklist:**
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings or errors
- [ ] Tested locally
- [ ] Screenshots included (for UI changes)

### Development Setup

**Running in Debug Mode:**
```bash
# Set debug mode in .env
DEBUG_MODE=True

# Or run with Flask debug:
export FLASK_DEBUG=1  # Linux/Mac
set FLASK_DEBUG=1     # Windows
python app.py
```

**Linting Code:**
```bash
# Check code style with flake8
flake8 app.py

# Auto-format with black
black app.py
```

### Areas for Contribution

We especially welcome contributions in these areas:

**🐛 Bug Fixes:**
- Report or fix any bugs you find
- Improve error handling
- Fix edge cases

**✨ New Features:**
- 7-day weather forecast
- Weather comparison between cities
- Export data as CSV/PDF
- Email/SMS alert notifications
- Mobile app version
- Weather widgets

**📚 Documentation:**
- Improve README
- Add code comments
- Create tutorials
- Translate documentation
- Record video guides

**🎨 UI/UX Improvements:**
- Enhance responsive design
- Add animations
- Improve accessibility
- Create new themes
- Mobile optimization

**🧪 Testing:**
- Write unit tests
- Add integration tests
- Test on different platforms
- Performance testing

### Code Review Process

1. Maintainers will review your PR within 2-3 days
2. They may request changes or ask questions
3. Make requested changes by pushing to your branch
4. Once approved, your PR will be merged
5. You'll be added to contributors list! 🎉

### Getting Help

Need help with your contribution?

- 💬 Open a [Discussion](https://github.com/Khan-Feroz211/Smart_weather_system/discussions)
- 📧 Email: [Your Email]
- 📖 Check existing [Issues](https://github.com/Khan-Feroz211/Smart_weather_system/issues)

---

## 🐛 Bug Reports & Feature Requests

### Reporting Bugs

Found a bug? Help us fix it by providing detailed information:

**🔍 Before Reporting:**
1. Search [existing issues](https://github.com/Khan-Feroz211/Smart_weather_system/issues) to avoid duplicates
2. Update to the latest version
3. Check if it's already fixed in development branch

**📝 Bug Report Template:**

```markdown
**Bug Description:**
A clear description of what the bug is.

**To Reproduce:**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior:**
What you expected to happen.

**Actual Behavior:**
What actually happened.

**Screenshots:**
If applicable, add screenshots.

**Environment:**
- OS: [e.g., Windows 11, macOS, Ubuntu 22.04]
- Python Version: [e.g., 3.13]
- Browser: [e.g., Chrome 120, Firefox 121]
- Deployment: [Local, Railway, Other]

**Additional Context:**
Any other relevant information.

**Error Logs:**
```
Paste any error messages or logs here
```
```

**Submit Issue:** [Create Bug Report](https://github.com/Khan-Feroz211/Smart_weather_system/issues/new?template=bug_report.md)

### Requesting Features

Have an idea for a new feature?

**💡 Feature Request Template:**

```markdown
**Feature Description:**
A clear description of the feature you'd like.

**Problem It Solves:**
What problem does this feature solve?

**Proposed Solution:**
How you envision the feature working.

**Alternative Solutions:**
Any alternative approaches you've considered.

**Use Cases:**
Real-world scenarios where this would be useful.

**Mockups/Examples:**
Screenshots or drawings if applicable.

**Additional Context:**
Any other relevant information.
```

**Submit Feature Request:** [Request Feature](https://github.com/Khan-Feroz211/Smart_weather_system/issues/new?template=feature_request.md)

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for full details.

### MIT License Summary

```
Copyright (c) 2026 Feroz Khan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

### What This Means

✅ **You CAN:**
- Use commercially
- Modify the code
- Distribute copies
- Use privately
- Sublicense

❌ **You CANNOT:**
- Hold the author liable
- Expect warranty
- Use author's name for promotion (without permission)

📋 **You MUST:**
- Include the original license
- Include copyright notice

---

## 👤 Author & Contact

**Feroz Khan**

- 🌐 **GitHub:** [@Khan-Feroz211](https://github.com/Khan-Feroz211)
- 📧 **Email:** [ferozkhan@example.com](mailto:ferozkhan@example.com)
- 💼 **LinkedIn:** [linkedin.com/in/feroz-khan](https://linkedin.com/in/feroz-khan)
- 🌐 **Portfolio:** [ferozkhan.dev](https://ferozkhan.dev)
- 🐦 **Twitter:** [@ferozkhan_dev](https://twitter.com/ferozkhan_dev)

---

## 🙏 Acknowledgments

This project wouldn't be possible without these amazing resources and communities:

### APIs & Services
- **[OpenWeatherMap](https://openweathermap.org/)** - Free weather data API with generous limits
- **[NASA API](https://api.nasa.gov/)** - Open-source space data and imagery
- **[Railway](https://railway.app/)** - Simple, powerful cloud deployment platform

### Libraries & Frameworks
- **[Flask](https://flask.palletsprojects.com/)** - Lightweight Python web framework
- **[Socket.IO](https://socket.io/)** - Real-time bidirectional communication
- **[scikit-learn](https://scikit-learn.org/)** - Machine learning library
- **[Font Awesome](https://fontawesome.com/)** - Beautiful icon library

### Hardware
- **[Arduino](https://www.arduino.cc/)** - Open-source electronics platform
- **[Adafruit](https://www.adafruit.com/)** - DHT sensor libraries and tutorials

### Community
- **Stack Overflow** - Endless help with technical challenges
- **GitHub Community** - Inspiration from open-source projects
- **Flask Discord** - Helpful community for Flask development
- **Python Community** - General Python programming support

### Special Thanks
- All contributors who have submitted pull requests
- Users who reported bugs and suggested features
- Everyone who starred the repository ⭐
- The open-source community for making this possible

---

## 📞 Support & Help

### Getting Support

Need help with Smart Weather System? Here are your options:

**📚 Documentation**
1. Read this README thoroughly
2. Check the [Wiki](https://github.com/Khan-Feroz211/Smart_weather_system/wiki) (coming soon)
3. Browse [closed issues](https://github.com/Khan-Feroz211/Smart_weather_system/issues?q=is%3Aissue+is%3Aclosed) for similar problems

**💬 Community Support**
- **Discussions:** [GitHub Discussions](https://github.com/Khan-Feroz211/Smart_weather_system/discussions)
- **Issues:** [Report Bug or Request Feature](https://github.com/Khan-Feroz211/Smart_weather_system/issues/new/choose)
- **Email:** ferozkhan@example.com (response within 24-48 hours)

**🆘 Emergency Support**
For critical production issues:
- Email: ferozkhan@example.com with subject "URGENT: Smart Weather System"
- Include: error logs, steps to reproduce, deployment environment

### Frequently Asked Questions (FAQ)

**Q: Can I use this project commercially?**  
A: Yes! It's MIT licensed, which means you can use it for commercial purposes. Just include the original license and copyright notice.

**Q: Do I need Arduino hardware to use this?**  
A: No, Arduino integration is completely optional. The app works perfectly using only weather APIs. Hardware adds real sensor data but isn't required.

**Q: Is the NASA API really free?**  
A: Yes! NASA's API is free with a generous rate limit (1000 requests per hour). Perfect for personal and educational projects.

**Q: How much does it cost to deploy on Railway?**  
A: Railway offers a free tier with 500 hours/month of execution time and 100GB bandwidth - plenty for personal projects. Production apps can upgrade as needed.

**Q: Can I change the purple theme to different colors?**  
A: Absolutely! Edit the CSS variables in `templates/base.html`. Look for `:root` section with `--primary` and `--secondary` colors.

**Q: How often does weather data update?**  
A: Weather data updates in real-time every 2 seconds via WebSocket when you're viewing the dashboard. API data refreshes every 5 minutes.

**Q: Can I add more than one city?**  
A: Currently, each user can set one city. Multi-city support is planned for version 2.1. You can track progress in [Issue #XX].

**Q: Why do satellite images take time to load?**  
A: Satellite images are large (800x600+) and fetched from external servers. We've optimized with lazy loading and caching, but initial load depends on internet speed.

**Q: Is my data secure?**  
A: Yes! Passwords are hashed using secure algorithms. For production, use HTTPS (Railway provides this automatically). Never commit API keys to Git.

**Q: Can I use PostgreSQL instead of SQLite?**  
A: Yes! Just update the database connection in `app.py`. SQLite is great for development; PostgreSQL recommended for production.

**Q: Does this work offline?**  
A: No, the app requires internet to fetch weather data from APIs. However, cached data may display briefly offline.

**Q: Can I contribute even if I'm a beginner?**  
A: Absolutely! We welcome contributions of all levels. Check "Good First Issue" label for beginner-friendly tasks.

**Q: How do I update to the latest version?**  
```bash
git pull origin main
pip install -r requirements.txt --upgrade
python app.py
```

**Q: Can I deploy this on Heroku/Vercel/AWS?**  
A: Yes! While we provide Railway instructions, the app can be deployed anywhere that supports Flask. You'll need to adapt the configuration.

**Q: Is there a Docker version?**  
A: Not yet, but Docker support is planned. Track progress in [Issue #XX] or contribute!

---

## 🎯 Roadmap

### Version 2.1 (Coming Q2 2026)
- [ ] **7-Day Weather Forecast** - Extended predictions with charts
- [ ] **Multiple City Comparison** - Compare weather across cities
- [ ] **Weather Data Export** - Download history as CSV/Excel/PDF
- [ ] **Email Notifications** - Alert notifications via email
- [ ] **Weather Widgets** - Embeddable widgets for websites
- [ ] **Dark Mode Improvements** - Enhanced theme customization

### Version 2.5 (Coming Q3 2026)
- [ ] **Mobile App** - React Native iOS/Android apps
- [ ] **Weather Analytics** - Historical data visualization with charts
- [ ] **Social Features** - Share weather status with friends
- [ ] **Custom Dashboards** - Drag-and-drop widget arrangement
- [ ] **Webhook Support** - Integration with Zapier, IFTTT
- [ ] **Air Quality Index** - Pollution and air quality monitoring

### Version 3.0 (Future - 2027)
- [ ] **AI Weather Chatbot** - Natural language weather queries
- [ ] **Voice Assistant** - Alexa/Google Home integration
- [ ] **Weather Predictions** - 14-day advanced forecasting
- [ ] **Crowd-Sourced Data** - Community weather reports
- [ ] **Business API** - Paid API for developers
- [ ] **Weather Events** - Hurricane, tornado, earthquake tracking

### Infrastructure Improvements
- [ ] Docker containerization
- [ ] Kubernetes deployment configs
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Automated testing suite
- [ ] Performance monitoring
- [ ] Database migrations system

Want to help build these features? Check out our [Contributing Guide](#-contributing)!

---

## 📊 Project Statistics

<div align="center">

![Lines of Code](https://img.shields.io/tokei/lines/github/Khan-Feroz211/Smart_weather_system?style=flat-square)
![GitHub code size](https://img.shields.io/github/languages/code-size/Khan-Feroz211/Smart_weather_system?style=flat-square)
![GitHub repo size](https://img.shields.io/github/repo-size/Khan-Feroz211/Smart_weather_system?style=flat-square)

</div>

**Development Statistics:**
- **Lines of Python Code:** ~2,500+
- **Lines of JavaScript:** ~800+
- **Lines of HTML/CSS:** ~1,500+
- **Total Files:** 30+
- **Templates:** 7
- **API Endpoints:** 12+
- **Database Tables:** 3
- **Dependencies:** 12 packages

**Project Metrics:**
- **Development Time:** 40+ hours
- **Contributors:** 1 (and growing!)
- **APIs Integrated:** 2 (OpenWeather, NASA)
- **Deployment Time:** 5 minutes
- **Setup Time:** 10 minutes
- **Test Coverage:** TBD

---

## ⭐ Star History

If you find this project helpful or interesting, please consider giving it a star! ⭐

It helps the project gain visibility and shows appreciation for the work.

[![Star History Chart](https://api.star-history.com/svg?repos=Khan-Feroz211/Smart_weather_system&type=Date)](https://star-history.com/#Khan-Feroz211/Smart_weather_system&Date)

---

## 🌟 Show Your Support

**Give a ⭐️ if this project helped you!**

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/Khan-Feroz211/Smart_weather_system?style=social)](https://github.com/Khan-Feroz211/Smart_weather_system/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Khan-Feroz211/Smart_weather_system?style=social)](https://github.com/Khan-Feroz211/Smart_weather_system/network/members)
[![GitHub watchers](https://img.shields.io/github/watchers/Khan-Feroz211/Smart_weather_system?style=social)](https://github.com/Khan-Feroz211/Smart_weather_system/watchers)

</div>

**Other Ways to Support:**
- ⭐ Star the repository
- 🐛 Report bugs or suggest features
- 🔀 Fork and contribute code
- 📢 Share with friends and colleagues
- 💬 Join discussions
- 📝 Write blog posts or tutorials about it
- 🎥 Create video tutorials
- 🌐 Translate documentation

---

<div align="center">

## 🚀 Ready to Get Started?

[![Deploy to Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/Khan-Feroz211/Smart_weather_system)

**OR**

```bash
git clone https://github.com/Khan-Feroz211/Smart_weather_system.git
cd Smart_weather_system
pip install -r requirements.txt
python app.py
```

---

**Made with ❤️ and lots of ☕ by Feroz Khan**

**© 2026 Smart Weather System. All Rights Reserved.**

---

[⬆ Back to Top](#-smart-weather-system)

</div>
