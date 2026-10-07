#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Визуальный стенд кампании: симулирует рендер сцены движком Chronicle Forge.

Кладёт фон состояния сцены, поверх — прямоугольники слотов и зон перехода,
а для слотов с НПС-спрайтом рисует спрайт по регламенту движка:
высота спрайта = h слота * sprite_scale (1 по умолчанию), по горизонтали —
центр слота, ноги (низ альфа-bbox) — на нижней границе слота.

Результат — PNG в каталоге превью (вне git) для визуальной проверки расстановки.
Запуск: python3 tools/visual_preview.py [каталог_вывода]
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(ROOT), "_preview")
os.makedirs(OUT, exist_ok=True)

try:
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    FONT_S = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
except OSError:
    FONT = FONT_S = ImageFont.load_default()


def load(path):
    return Image.open(os.path.join(ROOT, path)).convert("RGBA")


def sprite_feet_box(spr, slot):
    """Прямоугольник спрайта в слоте по регламенту движка."""
    scale = slot.get("sprite_scale") or 1.0
    target_h = slot["h"] * scale
    bbox = spr.getbbox()
    if bbox:
        spr = spr.crop(bbox)
    k = target_h / spr.height
    w = int(round(spr.width * k))
    h = int(round(target_h))
    spr = spr.resize((w, h), Image.LANCZOS)
    cx = slot["x"] + slot["w"] / 2.0
    x0 = int(round(cx - w / 2.0))
    y0 = int(round(slot["y"] + slot["h"] - h))
    return spr, x0, y0


def compose_scene(sc, state, out_path, with_sprites=True):
    img_path = state.get("image")
    if not img_path:
        return None
    bg = load(img_path)
    W, H = sc.get("canvas", {"w": 1280, "h": 720})["w"], sc["canvas"]["h"]
    if bg.size != (W, H):
        bg = bg.resize((W, H), Image.LANCZOS)
    canvas = bg.copy()
    ents = {}
    for f in sorted(os.listdir(os.path.join(ROOT, "entities"))):
        e = json.load(open(os.path.join(ROOT, "entities", f), encoding="utf-8"))
        ents[e["id"]] = e
    if with_sprites:
        for sl in sc.get("slots", []):
            ent = ents.get(sl.get("default_entity") or "")
            spr_path = (ent or {}).get("scene_sprite")
            if not spr_path:
                continue
            spr = load(spr_path)
            spr, x0, y0 = sprite_feet_box(spr, sl)
            canvas.alpha_composite(spr, (x0, y0))
    d = ImageDraw.Draw(canvas)
    for sl in sc.get("slots", []):
        has_spr = bool((ents.get(sl.get("default_entity") or "") or {}).get("scene_sprite"))
        col = (255, 60, 60, 255) if has_spr else (255, 190, 0, 255)
        d.rectangle([sl["x"], sl["y"], sl["x"] + sl["w"], sl["y"] + sl["h"]],
                    outline=col, width=3)
        d.text((sl["x"] + 4, sl["y"] + 4), sl["id"], font=FONT, fill=col)
    for nv in sc.get("navigation", []):
        a = nv.get("area", {})
        d.rectangle([a["x"], a["y"], a["x"] + a["w"], a["y"] + a["h"]],
                    outline=(0, 220, 255, 255), width=3)
        d.text((a["x"] + 4, a["y"] + a["h"] - 18), nv.get("label", "")[:24],
               font=FONT_S, fill=(0, 220, 255, 255))
    canvas.convert("RGB").save(out_path, quality=88)
    return out_path


def main():
    for f in sorted(os.listdir(os.path.join(ROOT, "scenes"))):
        sc = json.load(open(os.path.join(ROOT, "scenes", f), encoding="utf-8"))
        states = sc.get("states", [])
        base = [s for s in states if s.get("condition") is None] or states[-1:]
        for st in states:
            tag = "BASE" if st in base else st["id"]
            p = compose_scene(sc, st, os.path.join(
                OUT, "scene_%s__%s.png" % (sc["id"], tag)),
                with_sprites=(st in base))
            if p:
                print("wrote", p)


if __name__ == "__main__":
    main()
