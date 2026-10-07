#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Контактные листы персонажей: все состояния портрета + спрайт в один ряд.

Нужны для визуального аудита единства облика: один и тот же персонаж
должен быть узнаваем в каждом кадре мимики и в спрайте сцены.
Запуск: python3 tools/character_sheets.py [каталог_вывода]
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(ROOT), "_preview", "sheets")
os.makedirs(OUT, exist_ok=True)
H = 240
try:
    FONT = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
except OSError:
    FONT = ImageFont.load_default()


def thumb(path, h=H, checker=False):
    im = Image.open(os.path.join(ROOT, path))
    im = im.convert("RGBA")
    if checker:
        bg = Image.new("RGBA", im.size, (30, 30, 30, 255))
        bg.paste(im, (0, 0), im)
        im = bg
    k = h / im.height
    im = im.resize((max(1, int(im.width * k)), h), Image.LANCZOS)
    return im


def sheet(title, items, out_name):
    """items: list of (label, path, checker)"""
    thumbs = []
    for label, path, checker in items:
        if not path or not os.path.exists(os.path.join(ROOT, path)):
            continue
        thumbs.append((label, thumb(path, checker=checker)))
    if not thumbs:
        return
    pad = 8
    lab_h = 26
    W = sum(t.width for _, t in thumbs) + pad * (len(thumbs) + 1)
    canvas = Image.new("RGB", (W, H + lab_h + pad * 2), (245, 245, 245))
    d = ImageDraw.Draw(canvas)
    x = pad
    for label, t in thumbs:
        canvas.paste(t, (x, pad + lab_h))
        d.text((x + 2, pad + 4), label, font=FONT, fill=(20, 20, 20))
        x += t.width + pad
    canvas.save(os.path.join(OUT, out_name))
    print("wrote", os.path.join(OUT, out_name))


def main():
    ents = {}
    for f in sorted(os.listdir(os.path.join(ROOT, "entities"))):
        e = json.load(open(os.path.join(ROOT, "entities", f), encoding="utf-8"))
        ents[e["id"]] = e
    order = ["npc_ira", "npc_kast", "npc_kell", "npc_resh", "npc_vein",
             "npc_vex", "npc_dozh", "npc_ayla", "npc_zhuk", "npc_registrar",
             "npc_thug", "npc_watchman", "npc_ashhound", "npc_rotling",
             "player_hero"]
    for eid in order:
        e = ents.get(eid)
        if not e:
            continue
        items = []
        port = e.get("portrait") or {}
        for emo in ["neutral", "calm", "thoughtful", "angry", "sad", "afraid"]:
            if port.get(emo):
                items.append((emo, port[emo], False))
        if e.get("scene_sprite"):
            items.append(("SPRITE", e["scene_sprite"], True))
        sheet(eid, items, "char_%s.png" % eid)
    # архетипы героя из char_creation
    cj = json.load(open(os.path.join(ROOT, "campaign.json"), encoding="utf-8"))
    cc = (cj.get("campaign") or cj).get("char_creation") or {}
    for p in cc.get("portraits", []):
        items = []
        for emo in ["neutral", "calm", "thoughtful", "angry", "sad", "afraid"]:
            src = (p.get("portrait") or p.get("portraits") or {})
            if isinstance(src, dict) and src.get(emo):
                items.append((emo, src[emo], False))
        if items:
            sheet("hero_" + str(p.get("id") or p.get("archetype")),
                  items, "char_hero_%s.png" % (p.get("id") or p.get("archetype")))


if __name__ == "__main__":
    main()
