import os
import requests
from PIL import Image, ImageDraw, ImageFont
import datetime
import pytz
import urllib.request

# 1. Download Devanagari Font for Hindi Text Support
font_path = "NotoSansDevanagari.ttf"
if not os.path.exists(font_path):
    print("Downloading Hindi font...")
    urllib.request.urlretrieve("https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf", font_path)

# 2. Authenticate with ProKerala
print("Authenticating with ProKerala...")
token_res = requests.post(
    "https://api.prokerala.com/token",
    data={
        "grant_type": "client_credentials",
        "client_id": os.environ["PROKERALA_CLIENT_ID"],
        "client_secret": os.environ["PROKERALA_CLIENT_SECRET"]
    }
)
access_token = token_res.json()["access_token"]

# 3. Fetch Panchang for Kolkata in Hindi
print("Fetching Panchang data...")
ist = pytz.timezone('Asia/Kolkata')
now = datetime.datetime.now(ist)

headers = {"Authorization": f"Bearer {access_token}"}
params = {
    "ayanamsa": 1,
    "coordinates": "22.5726,88.3639",
    "datetime": now.isoformat(),
    "la": "hi"  # This parameter tells ProKerala to return Hindi text!
}
res = requests.get("https://api.prokerala.com/v2/astrology/panchang", headers=headers, params=params)
data = res.json()

# Extract Data Safely
try:
    panchang = data.get('data', {}).get('panchang', {})
    tithi = panchang.get('tithi', [{}])[0].get('name', 'N/A')
    nakshatra = panchang.get('nakshatra', [{}])[0].get('name', 'N/A')
except:
    tithi = "त्रुटि" # Hindi for Error
    nakshatra = "त्रुटि"

# 4. Draw the Canvas (800x480)
print("Drawing image...")
image = Image.new('1', (800, 480), 255) # 255 is white background
draw = ImageDraw.Draw(image)

# Load fonts with specific sizes
font_title = ImageFont.truetype(font_path, 45)
font_text = ImageFont.truetype(font_path, 35)

# Draw Hindi Text
# We use DD/MM/YYYY format so numbers stay universal
display_date = now.strftime('%d/%m/%Y')

draw.text((30, 30), f"कोलकाता पंचांग : {display_date}", font=font_title, fill=0)
draw.line((30, 95, 770, 95), fill=0, width=4) # A separation line

draw.text((30, 130), f"तिथि: {tithi}", font=font_text, fill=0)
draw.text((30, 200), f"नक्षत्र: {nakshatra}", font=font_text, fill=0)

# 5. Export to ESP32 Binary format
print("Saving binary file...")
os.makedirs("public", exist_ok=True)
with open("public/display.bin", "wb") as f:
    f.write(image.tobytes())
print("Done!")
