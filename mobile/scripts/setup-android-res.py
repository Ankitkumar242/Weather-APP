"""Populate Android mipmap and drawable asset folders from mobile/assets/icon.png."""

import os
from PIL import Image

RES_DIR = os.path.join("mobile", "android", "app", "src", "main", "res")
ASSETS_DIR = os.path.join("mobile", "assets")

icon_path = os.path.join(ASSETS_DIR, "icon.png")
if not os.path.exists(icon_path):
    print("Error: source icon.png not found")
    exit(1)

icon_img = Image.open(icon_path)

densities = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}

for folder, size in densities.items():
    target_dir = os.path.join(RES_DIR, folder)
    os.makedirs(target_dir, exist_ok=True)
    resized = icon_img.resize((size, size), Image.Resampling.LANCZOS)
    resized.save(os.path.join(target_dir, "ic_launcher.png"))
    resized.save(os.path.join(target_dir, "ic_launcher_round.png"))

# Splash drawable
drawable_dir = os.path.join(RES_DIR, "drawable")
os.makedirs(drawable_dir, exist_ok=True)
splash_path = os.path.join(ASSETS_DIR, "splash.png")
if os.path.exists(splash_path):
    splash_img = Image.open(splash_path)
    splash_img.resize((1080, 1920), Image.Resampling.LANCZOS).save(os.path.join(drawable_dir, "splash.png"))

print("Populated Android mipmap icons and drawable splash successfully.")
