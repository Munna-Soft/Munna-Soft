import os
import requests
import re
from datetime import datetime
import pytz

# Config
API_KEY = os.getenv("WEATHER_API_KEY")  # GitHub secret name: WEATHER_API_KEY
CITY = "Dhaka"
TIMEZONE = "Asia/Dhaka"  # To show local times

if not API_KEY:
    raise ValueError("No API key found in environment variable WEATHER_API_KEY")

# API call
url = f"https://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={CITY}&days=1&aqi=yes&alerts=no"
resp = requests.get(url, timeout=15)
resp.raise_for_status()
data = resp.json()

# Current
current = data.get("current", {})
forecast_day = data.get("forecast", {}).get("forecastday", [{}])[0]

condition = current.get("condition", {}).get("text", "N/A")
icon = current.get("condition", {}).get("icon", "")
temp = current.get("temp_c", "N/A")
feels = current.get("feelslike_c", "N/A")
humidity = current.get("humidity", "N/A")
wind = current.get("wind_kph", "N/A")

# Astro
astro = forecast_day.get("astro", {})
sunrise = astro.get("sunrise", "N/A")
sunset = astro.get("sunset", "N/A")
moon_phase = astro.get("moon_phase", "N/A")

# Hourly — Next 6 hours from current local time
hours = forecast_day.get("hour", [])  # list of 24 hour dicts
# Determine current local hour index from API times (they are in local time already)
# We'll pick next 6 time slots starting from the first hour >= now
tz = pytz.timezone(TIMEZONE)
now_local = datetime.now(tz)
now_str = now_local.strftime("%Y-%m-%d %H:%M")

# Find start index
start_idx = 0
for i, h in enumerate(hours):
    # hour time string like "2025-11-28 09:00"
    t = h.get("time")
    if not t:
        continue
    try:
        dt = datetime.strptime(t, "%Y-%m-%d %H:%M")
    except Exception:
        continue
    # assume API times are local to requested location; compare by hour
    if dt.hour >= now_local.hour:
        start_idx = i
        break

next_hours = hours[start_idx:start_idx+6] if hours else []

# small helper to pick emoji based on condition text
def cond_emoji(txt):
    txt = (txt or "").lower()
    if "sun" in txt or "clear" in txt:
        return "☀️"
    if "cloud" in txt or "overcast" in txt:
        return "⛅"
    if "rain" in txt or "drizzle" in txt or "shower" in txt:
        return "🌧️"
    if "storm" in txt or "thunder" in txt:
        return "⛈️"
    if "snow" in txt or "sleet" in txt:
        return "❄️"
    if "fog" in txt or "mist" in txt or "haze" in txt:
        return "🌫️"
    return "🌤️"

# Build hourly lines
hourly_lines = []
for h in next_hours:
    t = h.get("time", "")
    # extract HH:MM
    hh = t.split()[-1] if t else ""
    temp_h = h.get("temp_c", "N/A")
    cond_h = h.get("condition", {}).get("text", "")
    emoji = cond_emoji(cond_h)
    hourly_lines.append(f"{hh} → {temp_h}°C {emoji}  {cond_h}")

hourly_block_md = "<br>".join(hourly_lines) if hourly_lines else "No hourly data available."

# Compose compact emoji-rich card (Markdown-friendly)
weather_block = f"""
<img src="{icon}" width="60"><br>
**🌤️ {CITY} Weather Update**  — _{now_str}_  

**🌡️ Temp:** {temp}°C  |  **🤗 Feels:** {feels}°C  
**💧 Humidity:** {humidity}%  |  **💨 Wind:** {wind} kph  
**🛰️ Condition:** {condition}

**🌅 Sunrise:** {sunrise}  •  **🌇 Sunset:** {sunset}  
**🌙 Moon Phase:** {moon_phase}

**🕒 Next 6 Hours**  
{hourly_block_md}

---
*Last updated automatically every 6 hours.*
"""

# Replace in README.md
readme_path = "README.md"
with open(readme_path, "r", encoding="utf-8") as f:
    md = f.read()

new_md = re.sub(
    r"<!-- AUTO-WEATHER-DATA -->(.*?)<!-- AUTO-WEATHER-DATA-END -->",
    f"<!-- AUTO-WEATHER-DATA -->\n{weather_block}\n<!-- AUTO-WEATHER-DATA-END -->",
    md,
    flags=re.S
)

with open(readme_path, "w", encoding="utf-8") as f:
    f.write(new_md)

print("✅ Weather Updated.")
