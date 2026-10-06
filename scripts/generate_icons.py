"""Generate crisp PWA icons and SVG logo for SkyPulse."""

import os
from PIL import Image, ImageDraw

ICONS_DIR = os.path.join("app", "static", "icons")
os.makedirs(ICONS_DIR, exist_ok=True)

# 1. Generate crisp vector SVG Logo
SVG_CONTENT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0F172A" />
      <stop offset="50%" stop-color="#1E293B" />
      <stop offset="100%" stop-color="#0F172A" />
    </linearGradient>
    <linearGradient id="sunGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FCD34D" />
      <stop offset="100%" stop-color="#F59E0B" />
    </linearGradient>
    <linearGradient id="cloudGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#60A5FA" />
      <stop offset="100%" stop-color="#2563EB" />
    </linearGradient>
    <linearGradient id="pulseGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#38BDF8" />
      <stop offset="50%" stop-color="#A855F7" />
      <stop offset="100%" stop-color="#38BDF8" />
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Background base rounded card -->
  <rect width="512" height="512" rx="108" fill="url(#bgGrad)" />

  <!-- Sun Rays & Disc -->
  <circle cx="340" cy="180" r="76" fill="url(#sunGrad)" opacity="0.95" filter="url(#glow)" />
  
  <!-- Cloud Body -->
  <path d="M150 330 
           h210 
           a55 55 0 0 0 0-110 
           a82 82 0 0 0-155-25 
           a60 60 0 0 0-55 135 z" 
        fill="url(#cloudGrad)" 
        opacity="0.95" />

  <!-- Weather Pulse Wave (EKG / Frequency Line) -->
  <path d="M 100 360 
           L 180 360 
           L 210 310 
           L 245 400 
           L 280 290 
           L 315 375 
           L 345 360 
           L 412 360" 
        fill="none" 
        stroke="url(#pulseGrad)" 
        stroke-width="18" 
        stroke-linecap="round" 
        stroke-linejoin="round" 
        filter="url(#glow)" />
</svg>
"""

with open(os.path.join(ICONS_DIR, "logo.svg"), "w", encoding="utf-8") as f:
    f.write(SVG_CONTENT)

with open(os.path.join(ICONS_DIR, "icon.svg"), "w", encoding="utf-8") as f:
    f.write(SVG_CONTENT)

print("Generated logo.svg and icon.svg")


def create_icon(size: int, maskable: bool = False) -> Image.Image:
    """Create a high-resolution PIL icon."""
    img = Image.new("RGBA", (size, size), (15, 23, 42, 255))
    draw = ImageDraw.Draw(img)

    scale = size / 512.0
    # Safe area margin for maskable icon is 10-15% padding on each side
    offset = 0 if not maskable else int(size * 0.1)
    effective_scale = scale * (0.8 if maskable else 1.0)
    base_x = offset if maskable else 0
    base_y = offset if maskable else 0

    # Draw rounded gradient card if not maskable (maskables use full bleed solid/gradient)
    if not maskable:
        corner_r = int(108 * scale)
        draw.rounded_rectangle(
            [(0, 0), (size, size)],
            radius=corner_r,
            fill=(15, 23, 42, 255),
        )

    # 1. Sun circle
    sun_cx = int(base_x + 340 * effective_scale)
    sun_cy = int(base_y + 180 * effective_scale)
    sun_r = int(72 * effective_scale)
    draw.ellipse(
        [sun_cx - sun_r, sun_cy - sun_r, sun_cx + sun_r, sun_cy + sun_r],
        fill=(245, 158, 11, 255),  # Amber-500
    )

    # 2. Cloud puffs (circles + base)
    cloud_color = (37, 99, 235, 255)  # Blue-600
    # Center big circle
    c_cx = int(base_x + 235 * effective_scale)
    c_cy = int(base_y + 245 * effective_scale)
    c_r = int(80 * effective_scale)
    draw.ellipse([c_cx - c_r, c_cy - c_r, c_cx + c_r, c_cy + c_r], fill=cloud_color)

    # Left puff
    c_left_x = int(base_x + 160 * effective_scale)
    c_left_y = int(base_y + 275 * effective_scale)
    c_left_r = int(58 * effective_scale)
    draw.ellipse(
        [c_left_x - c_left_r, c_left_y - c_left_r, c_left_x + c_left_r, c_left_y + c_left_r],
        fill=cloud_color,
    )

    # Right puff
    c_right_x = int(base_x + 315 * effective_scale)
    c_right_y = int(base_y + 275 * effective_scale)
    c_right_r = int(52 * effective_scale)
    draw.ellipse(
        [c_right_x - c_right_r, c_right_y - c_right_r, c_right_x + c_right_r, c_right_y + c_right_r],
        fill=cloud_color,
    )

    # Base cloud fill
    draw.rectangle(
        [
            int(base_x + 160 * effective_scale),
            int(base_y + 270 * effective_scale),
            int(base_x + 325 * effective_scale),
            int(base_y + 330 * effective_scale),
        ],
        fill=cloud_color,
    )

    # 3. Pulse EKG wave
    points = [
        (int(base_x + 90 * effective_scale), int(base_y + 355 * effective_scale)),
        (int(base_x + 180 * effective_scale), int(base_y + 355 * effective_scale)),
        (int(base_x + 210 * effective_scale), int(base_y + 305 * effective_scale)),
        (int(base_x + 245 * effective_scale), int(base_y + 395 * effective_scale)),
        (int(base_x + 280 * effective_scale), int(base_y + 285 * effective_scale)),
        (int(base_x + 315 * effective_scale), int(base_y + 370 * effective_scale)),
        (int(base_x + 345 * effective_scale), int(base_y + 355 * effective_scale)),
        (int(base_x + 420 * effective_scale), int(base_y + 355 * effective_scale)),
    ]
    pulse_width = max(3, int(16 * effective_scale))
    draw.line(points, fill=(56, 189, 248, 255), width=pulse_width, joint="curve")

    return img


# Generate all sizes
create_icon(192, maskable=False).save(os.path.join(ICONS_DIR, "icon-192.png"))
create_icon(512, maskable=False).save(os.path.join(ICONS_DIR, "icon-512.png"))
create_icon(192, maskable=True).save(os.path.join(ICONS_DIR, "icon-maskable-192.png"))
create_icon(512, maskable=True).save(os.path.join(ICONS_DIR, "icon-maskable-512.png"))
create_icon(180, maskable=False).save(os.path.join(ICONS_DIR, "apple-touch-icon.png"))
create_icon(32, maskable=False).save(os.path.join(ICONS_DIR, "favicon.png"))

print("Generated icon-192.png, icon-512.png, maskables, and apple-touch-icon.png successfully.")

