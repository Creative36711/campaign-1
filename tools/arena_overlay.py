#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Оверлей гекс-сетки арены поверх изображения (вид сверху).

Рисует сетку odd-r (pointy-top) с номерами «col,row» и подсветкой
текущих blocked/difficult/spawn из JSON арены, чтобы визуально
сопоставить препятствия на картинке с гексами.
Запуск: python3 tools/arena_overlay.py <img> <arena_id|cols rows size> [out]
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    FONT = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
except OSError:
    FONT = ImageFont.load_default()


def grid(cols, rows, size, W=1280, H=720):
    w = math.sqrt(3) * size
    width = w * (cols + 0.5)
    height = 1.5 * size * (rows - 1) + 2 * size
    ox = (W - width) / 2 + w / 2
    oy = (H - height) / 2 + size
    cent = {}
    for r in range(rows):
        for c in range(cols):
            x = ox + w * (c + 0.5 * (r % 2))
            y = oy + 1.5 * size * r
            cent[(c, r)] = (x, y)
    return cent


def hexpts(cx, cy, size):
    pts = []
    for k in range(6):
        a = math.radians(60 * k + 30)
        pts.append((cx + size * math.cos(a), cy + size * math.sin(a)))
    return pts


def main():
    img, spec = sys.argv[1], sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(
        os.path.dirname(ROOT), "_preview",
        "arena_%s.png" % os.path.basename(img).split('.')[0])
    if spec.endswith('.json'):
        d = json.load(open(os.path.join(ROOT, 'arenas', spec)))
        hg = d['hex_grid']
        cols, rows, size = hg['cols'], hg['rows'], hg['hex_size']
        blocked = {tuple(h) for h in hg['blocked_hexes']}
        diff = {tuple(h) for h in hg['difficult_terrain']}
        sp_p = {tuple(h) for h in d['spawn_zones']['player']['hexes']}
        sp_e = {tuple(h) for h in d['spawn_zones']['enemy']['hexes']}
    else:
        cols, rows, size = (int(v) for v in spec.split(','))
        blocked = diff = sp_p = sp_e = set()
    im = Image.open(img if os.path.isabs(img) else os.path.join(ROOT, img))
    im = im.convert('RGBA').resize((1280, 720), Image.LANCZOS)
    d2 = ImageDraw.Draw(im, 'RGBA')
    cent = grid(cols, rows, size)
    for (c, r), (x, y) in cent.items():
        pts = hexpts(x, y, size - 1)
        fill = None
        if (c, r) in blocked:
            fill = (255, 40, 40, 110)
        elif (c, r) in diff:
            fill = (255, 220, 0, 90)
        elif (c, r) in sp_p:
            fill = (40, 255, 120, 110)
        elif (c, r) in sp_e:
            fill = (40, 160, 255, 110)
        d2.polygon(pts, outline=(255, 255, 255, 200), fill=fill)
        d2.text((x - 12, y - 8), "%d,%d" % (c, r), font=FONT,
                fill=(255, 255, 255, 235))
    im.convert('RGB').save(out, quality=90)
    print('wrote', out)


if __name__ == '__main__':
    main()
