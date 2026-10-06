"""Generate high-resolution source assets for Capacitor @capacitor/assets."""

import os
from PIL import Image, ImageDraw

ASSETS_DIR = os.path.join("mobile", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# 1. Generate 1024x1024 App Icon
icon = Image.new("RGBA", (1024, 1024), (15, 23, 42, 255))
draw = ImageDraw.Draw(icon)

# Rounded background
draw.rounded_rectangle([(0, 0), (1024, 1024)], radius=216, fill=(15, 23, 42, 255))

# Sun
sun_cx = int(340 * 2)
sun_cy = int(180 * 2)
sun_r = int(72 * 2)
draw.ellipse([sun_cx - sun_r, sun_cy - sun_r, sun_cx + sun_r, sun_cy + sun_r], fill=(245, 158, 11, 255))

# Cloud
cloud_color = (37, 99, 235, 255)
c_cx, c_cy, c_r = int(235 * 2), int(245 * 2), int(80 * 2)
draw.ellipse([c_cx - c_r, c_cy - c_r, c_cx + c_r, c_cy + c_r], fill=cloud_color)

c_left_x, c_left_y, c_left_r = int(160 * 2), int(275 * 2), int(58 * 2)
draw.ellipse([c_left_x - c_left_r, c_left_y - c_left_r, c_left_x + c_left_r, c_left_y + c_left_r], fill=cloud_color)

c_right_x, c_right_y, c_right_r = int(315 * 2), int(275 * 2), int(52 * 2)
draw.ellipse([c_right_x - c_right_r, c_right_y - c_right_r, c_right_x + c_right_r, c_right_y + c_right_r], fill=cloud_color)

draw.rectangle([int(160 * 2), int(270 * 2), int(325 * 2), int(330 * 2)], fill=cloud_color)

# Pulse wave
points = [
    (int(90 * 2), int(355 * 2)),
    (int(180 * 2), int(355 * 2)),
    (int(210 * 2), int(305 * 2)),
    (int(245 * 2), int(395 * 2)),
    (int(280 * 2), int(285 * 2)),
    (int(315 * 2), int(370 * 2)),
    (int(345 * 2), int(355 * 2)),
    (int(420 * 2), int(355 * 2)),
]
draw.line(points, fill=(56, 189, 248, 255), width=32, joint="curve")

icon.save(os.path.join(ASSETS_DIR, "icon.png"))
icon.save(os.path.join(ASSETS_DIR, "icon-foreground.png"))

# Background
bg = Image.new("RGBA", (1024, 1024), (15, 23, 42, 255))
bg.save(os.path.join(ASSETS_DIR, "icon-background.png"))

# 2. Splash screen (2732x2732 centered brand)
splash = Image.new("RGBA", (2732, 2732), (15, 23, 42, 255))
# Paste scaled icon at center
scaled_icon = icon.resize((800, 800), Image.Resampling.LANCZOS)
paste_x = (2732 - 800) // 2
paste_y = (2732 - 800) // 2
splash.paste(scaled_icon, (paste_x, paste_y), scaled_icon)
splash.save(os.path.join(ASSETS_DIR, "splash.png"))

print("Generated mobile assets: icon.png, icon-foreground.png, icon-background.png, splash.png")
