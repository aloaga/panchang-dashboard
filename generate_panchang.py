import os
import requests
from PIL import Image, ImageDraw, ImageFont
import datetime
import pytz
import urllib.request
import json

# 1. Download Devanagari Font
font_path = "NotoSansDevanagari.ttf"
if not os.path.exists(font_path):
    urllib.request.urlretrieve("https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf", font_path)

# 2. Authenticate with ProKerala
token_res = requests.post(
    "https://api.prokerala.com/token",
    data={
        "grant_type": "client_credentials",
        "client_id": os.environ["PROKERALA_CLIENT_ID"],
        "client_secret": os.environ["PROKERALA_CLIENT_SECRET"]
    }
)
access_token = token_res.json().get("access_token")

# 3. Fetch Data with Strict ISO Formatting
ist = pytz.timezone('Asia/Kolkata')
now = datetime.datetime.now(ist).replace(microsecond=0)

headers = {"Authorization": f"Bearer {access_token}"}
params = {
    "ayanamsa": 1,
    "coordinates": "22.5726,88.3639",
    "datetime": now.isoformat(), 
    "la": "hi"
}

res = requests.get("https://api.prokerala.com/v2/astrology/panchang", headers=headers, params=params)
data = res.json()

# 4. Safe Data Extraction
data_block = data.get('data', {})

def get_name(key):
    try:
        return data_block.get(key, [{}])[0].get('name', "उपलब्ध नहीं")
    except:
        return "उपलब्ध नहीं"

def get_end_time(key):
    try:
        iso_str = data_block.get(key, [{}])[0].get('end', '')
        return format_time(iso_str)
    except:
        return "उपलब्ध नहीं"

def format_time(iso_str):
    if not iso_str: return "उपलब्ध नहीं"
    try:
        dt = datetime.datetime.fromisoformat(iso_str).astimezone(ist)
        time_str = dt.strftime("%I:%M")
        ampm = "पूर्वाह्न" if dt.hour < 12 else "अपराह्न"
        return f"{time_str} {ampm}"
    except:
        return "उपलब्ध नहीं"

# Extract names
tithi = get_name('tithi')
nakshatra = get_name('nakshatra')
yoga = get_name('yoga')
karana = get_name('karana')

# Extract new specific data points
vaara = data_block.get('vaara', 'उपलब्ध नहीं')
try:
    paksha = data_block.get('tithi', [{}])[0].get('paksha', '')
except:
    paksha = ""
    
tithi_end = get_end_time('tithi')
nakshatra_end = get_end_time('nakshatra')

sunrise = format_time(data_block.get('sunrise', ""))
sunset = format_time(data_block.get('sunset', ""))
moonrise = format_time(data_block.get('moonrise', ""))
moonset = format_time(data_block.get('moonset', ""))

# 5. Draw the Full Dashboard Canvas (800x480 Landscape)
image = Image.new('1', (800, 480), 255)
draw = ImageDraw.Draw(image)

# Slightly reduced header font to comfortably fit the Day and Paksha
font_header = ImageFont.truetype(font_path, 40) 
font_title = ImageFont.truetype(font_path, 38)
font_text = ImageFont.truetype(font_path, 30)
font_small = ImageFont.truetype(font_path, 22) 

# Main Outer Border
draw.rectangle((10, 10, 790, 470), outline=0, width=6)

# Header Section (Now includes Day of the week and Paksha)
display_date = now.strftime('%d / %m / %Y')
header_text = f"कोलकाता : {vaara}, {display_date} | {paksha}"
draw.text((60, 25), header_text, font=font_header, fill=0)
draw.line((10, 90, 790, 90), fill=0, width=4)

# Left Column (Tithi & Nakshatra now include End Times)
draw.text((120, 110), "दैनिक पंचांग", font=font_title, fill=0)
draw.line((40, 165, 360, 165), fill=0, width=2)

draw.text((40, 185), f"तिथि: {tithi}", font=font_text, fill=0)
draw.text((40, 220), f"({tithi_end} तक)", font=font_small, fill=0)

draw.text((40, 260), f"नक्षत्र: {nakshatra}", font=font_text, fill=0)
draw.text((40, 295), f"({nakshatra_end} तक)", font=font_small, fill=0)

draw.text((40, 340), f"योग: {yoga}", font=font_text, fill=0)
draw.text((40, 400), f"करण: {karana}", font=font_text, fill=0)

# Vertical Center Divider
draw.line((400, 90, 400, 470), fill=0, width=4)

# Right Column (Unchanged)
draw.text((500, 110), "सूर्य और चंद्र", font=font_title, fill=0)
draw.line((440, 165, 760, 165), fill=0, width=2)
draw.text((440, 190), f"सूर्योदय:   {sunrise}", font=font_text, fill=0)
draw.text((440, 250), f"सूर्यास्त:   {sunset}", font=font_text, fill=0)
draw.text((440, 310), f"चंद्रोदय:   {moonrise}", font=font_text, fill=0)
draw.text((440, 370), f"चंद्रास्त:   {moonset}", font=font_text, fill=0)

# Export to ESP32 Binary format
os.makedirs("public", exist_ok=True)
with open("public/display.bin", "wb") as f:
    f.write(image.tobytes())
