#!/usr/bin/env python3
"""make_og.py — генерирует site/og-image.png (1200×630) в стиле сайта.

Зависимость: Pillow (pip install pillow). Запуск: python site/make_og.py
Шрифты берутся системные (macOS Helvetica/Arial); правь пути под свою ОС при необходимости.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

W, H = 1200, 630
BG = (14, 17, 23); FG = (230, 237, 243); MUTED = (154, 167, 180)
ACCENT = (76, 194, 196); ACCENT2 = (124, 131, 255)
OUT = os.path.join(os.path.dirname(__file__), "og-image.png")


def font(size, bold=False):
    for path, idx in [("/System/Library/Fonts/Helvetica.ttc", 1 if bold else 0),
                      ("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold
                       else "/System/Library/Fonts/Supplemental/Arial.ttf", 0)]:
        try:
            return ImageFont.truetype(path, size, index=idx)
        except Exception:
            pass
    return ImageFont.load_default()


def main():
    img = Image.new("RGBA", (W, H), BG + (255,))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([250, -260, 950, 260], fill=ACCENT2 + (90,))
    gd.ellipse([-150, 350, 500, 800], fill=ACCENT + (55,))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(140)))
    d = ImageDraw.Draw(img)
    PAD = 80

    d.rectangle([PAD, 70, PAD + 70, 78], fill=ACCENT)
    ft = font(132, bold=True)
    d.text((PAD, 150), "AI ", font=ft, fill=FG)
    d.text((PAD + d.textlength("AI ", font=ft), 150), "Native", font=ft, fill=ACCENT)
    d.text((PAD, 320), "От основ до агентных систем", font=font(46), fill=FG)
    d.text((PAD, 408), "Build It · Use It · Ship It", font=font(34, bold=True), fill=ACCENT)

    fb = font(30); bx, by = PAD, 500
    for b in ["13 фаз", "59 уроков", "офлайн · мульти-провайдер"]:
        w = d.textlength(b, font=fb)
        d.rounded_rectangle([bx, by, bx + w + 44, by + 56], radius=28,
                            fill=(28, 35, 48, 255), outline=(42, 49, 60, 255), width=2)
        d.text((bx + 22, by + 12), b, font=fb, fill=MUTED)
        bx += w + 60
    d.text((PAD, H - 64), "Технический self-paced курс · LLM · агенты · MCP · FinOps",
           font=font(24), fill=MUTED)

    img.convert("RGB").save(OUT, "PNG")
    print("saved", OUT)


if __name__ == "__main__":
    main()
