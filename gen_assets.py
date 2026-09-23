"""One-off script: generates icon.png / icon.ico / loading_art.png for the app."""
import math
from PIL import Image, ImageDraw, ImageFilter

VIOLET = (124, 92, 255)
PURPLE = (185, 140, 255)
AMBER = (255, 176, 89)
NEAR_BLACK = (10, 10, 13)
PANEL = (18, 18, 24)
EDGE = (36, 36, 48)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rounded_rect(draw, box, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


# ---------------------------------------------------------------
# 1) App icon: phone -> PC keystream mark, on a rounded dark square
# ---------------------------------------------------------------
def make_icon(size=512):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = int(size * 0.04)
    # background rounded square with subtle vertical gradient
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bgdraw = ImageDraw.Draw(bg)
    steps = size
    for y in range(steps):
        t = y / steps
        color = lerp(NEAR_BLACK, PANEL, t)
        bgdraw.line([(0, y), (size, y)], fill=color + (255,))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [pad, pad, size - pad, size - pad], radius=int(size * 0.22), fill=255
    )
    img.paste(bg, (0, 0), mask)
    draw = ImageDraw.Draw(img)
    rounded_rect(
        draw, [pad, pad, size - pad, size - pad], int(size * 0.22),
        outline=EDGE + (255,), width=max(2, size // 170)
    )

    cx, cy = size / 2, size / 2

    # phone (rounded rect) on the left
    ph_w, ph_h = size * 0.22, size * 0.40
    ph_x0, ph_y0 = cx - size * 0.24, cy - ph_h / 2
    ph_x1, ph_y1 = ph_x0 + ph_w, ph_y0 + ph_h
    rounded_rect(draw, [ph_x0, ph_y0, ph_x1, ph_y1], int(size * 0.045),
                 fill=(20, 20, 28, 255), outline=PURPLE + (255,), width=max(3, size // 110))
    # three little "key" lines inside phone
    for i, ky in enumerate([0.38, 0.5, 0.62]):
        yy = ph_y0 + ph_h * ky
        draw.line([(ph_x0 + ph_w * 0.22, yy), (ph_x1 - ph_w * 0.22, yy)],
                   fill=PURPLE + (255,), width=max(2, size // 170))

    # keyboard grid on the right (representing the PC)
    kb_w, kb_h = size * 0.34, size * 0.26
    kb_x0, kb_y0 = cx + size * 0.02, cy - kb_h / 2
    kb_x1, kb_y1 = kb_x0 + kb_w, kb_y0 + kb_h
    rounded_rect(draw, [kb_x0, kb_y0, kb_x1, kb_y1], int(size * 0.04),
                 fill=(20, 20, 28, 255), outline=AMBER + (255,), width=max(3, size // 110))
    cols, rows = 4, 3
    mgn = kb_w * 0.12
    cell_w = (kb_w - 2 * mgn) / cols
    cell_h = (kb_h - 2 * mgn) / rows
    for r in range(rows):
        for c in range(cols):
            x0 = kb_x0 + mgn + c * cell_w + cell_w * 0.12
            y0 = kb_y0 + mgn + r * cell_h + cell_h * 0.12
            x1 = kb_x0 + mgn + (c + 1) * cell_w - cell_w * 0.12
            y1 = kb_y0 + mgn + (r + 1) * cell_h - cell_h * 0.12
            rounded_rect(draw, [x0, y0, x1, y1], int(size * 0.008), fill=AMBER + (200,))

    # connecting arc / signal dots between phone and keyboard
    dot_y = cy
    for i, dx in enumerate([0.0, 0.045, 0.09]):
        r = size * (0.012 + i * 0.004)
        x = ph_x1 + size * (0.03 + dx)
        draw.ellipse([x - r, dot_y - r, x + r, dot_y + r], fill=PURPLE + (255 - i * 40,))

    return img


icon = make_icon(512)
icon.save("/home/claude/PhoneKeyboardBridge/assets_bundled/icon.png")
# multi-size .ico for Windows exe/taskbar
icon.save(
    "/home/claude/PhoneKeyboardBridge/assets_bundled/icon.ico",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)

# ---------------------------------------------------------------
# 2) Loading-screen artwork: abstract dark cinematic composition
# ---------------------------------------------------------------
def make_loading_art(w=760, h=760):
    img = Image.new("RGB", (w, h), NEAR_BLACK)
    # soft vertical gradient backdrop
    grad = Image.new("RGB", (w, h), NEAR_BLACK)
    gd = ImageDraw.Draw(grad)
    for y in range(h):
        t = y / h
        gd.line([(0, y), (w, y)], fill=lerp((20, 16, 30), NEAR_BLACK, t))
    img.paste(grad, (0, 0))

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    cx, cy = w * 0.5, h * 0.42

    # large soft glow circles
    for i, (r, color, alpha) in enumerate([
        (w * 0.34, VIOLET, 70), (w * 0.24, PURPLE, 60), (w * 0.15, AMBER, 45)
    ]):
        ang = i * 2.4
        ox, oy = cx + math.cos(ang) * w * 0.06, cy + math.sin(ang) * h * 0.06
        draw.ellipse([ox - r, oy - r, ox + r, oy + r], fill=color + (alpha,))

    overlay = overlay.filter(ImageFilter.GaussianBlur(w * 0.03))
    draw = ImageDraw.Draw(overlay)

    # thin concentric arcs (radar / signal motif)
    for i in range(5):
        r = w * (0.10 + i * 0.055)
        bbox = [cx - r, cy - r, cx + r, cy + r]
        draw.arc(bbox, start=200, end=340, fill=PURPLE + (160,), width=2)
        draw.arc(bbox, start=20, end=160, fill=AMBER + (100,), width=2)

    # small dot grid (keyboard motif) lower area
    dot_r = 4
    start_x, start_y = w * 0.30, h * 0.72
    for row in range(3):
        for col in range(8):
            x = start_x + col * (w * 0.055)
            y = start_y + row * (h * 0.045)
            draw.ellipse([x - dot_r, y - dot_r, x + dot_r, y + dot_r], fill=PURPLE + (140,))

    # thin outline phone shape, top right, subtle
    ph_w, ph_h = w * 0.16, h * 0.30
    ph_x0, ph_y0 = w * 0.68, h * 0.12
    draw.rounded_rectangle(
        [ph_x0, ph_y0, ph_x0 + ph_w, ph_y0 + ph_h], radius=int(w * 0.02),
        outline=PURPLE + (180,), width=3
    )

    combined = Image.alpha_composite(img.convert("RGBA"), overlay)
    return combined.convert("RGB")


art = make_loading_art()
art.save("/home/claude/PhoneKeyboardBridge/assets_bundled/loading_art.png")

print("done")
