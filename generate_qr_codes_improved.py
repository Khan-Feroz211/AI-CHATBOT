#!/usr/bin/env python3
"""
Generate QR codes with clear labels and high-DPI output for reliable scanning.
This script will fall back to built-in fonts if a system TTF isn't available.
"""

import sqlite3
from pathlib import Path
import qrcode
import pyotp
from PIL import Image, ImageDraw, ImageFont

DB_PATH = Path("chatbot_data") / "chatbot.db"
QR_DIR = Path("qr_codes")
QR_DIR.mkdir(exist_ok=True)

print("Generating improved QR codes (with label and high-DPI)...")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT id, username, mfa_secret FROM users WHERE username LIKE 'demo%' AND mfa_enabled = 1")
accounts = cur.fetchall()

if not accounts:
    print("No demo accounts with MFA enabled found.")
    conn.close()
    raise SystemExit(0)

# Try to find a reasonable TTF font (DejaVu or Segoe), fallback to default
possible_fonts = [
    r"C:\\Windows\\Fonts\\segoeui.ttf",
    r"C:\\Windows\\Fonts\\arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
font_path = None
for p in possible_fonts:
    pth = Path(p)
    if pth.exists():
        font_path = str(pth)
        break

for user_id, username, secret in accounts:
    print(f"Generating for {username} (id={user_id})")
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=username, issuer_name="AI Project Assistant")

    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Add a small label below the QR code with the username and partial secret
    label_text = f"{username} — key: {secret[:8]}..."
    draw = ImageDraw.Draw(img)

    # Choose font size based on image width
    img_w, img_h = img.size
    font_size = max(10, img_w // 15)
    try:
        if font_path:
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    try:
        text_w, text_h = draw.textsize(label_text, font=font)
    except Exception:
        # Pillow versions differ; fallback to font.getsize
        try:
            text_w, text_h = font.getsize(label_text)
        except Exception:
            # Final fallback
            text_w, text_h = (img_w // 2, 12)
    # Create new image with space for label
    padding = 10
    new_h = img_h + text_h + padding * 2
    new_img = Image.new("RGB", (img_w, new_h), "white")
    new_img.paste(img, (0, 0))
    draw = ImageDraw.Draw(new_img)
    text_x = (img_w - text_w) // 2
    text_y = img_h + padding
    draw.text((text_x, text_y), label_text, fill="black", font=font)

    # Save as PNG with explicit DPI metadata
    out_file = QR_DIR / f"mfa_{username}_qr_improved.png"
    new_img.save(out_file, format="PNG", dpi=(300, 300))
    print(f" Saved: {out_file} ({out_file.stat().st_size} bytes)")

conn.close()
print("Done. Improved QR images saved to qr_codes/")
