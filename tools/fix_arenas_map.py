#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Заменяет фоны арен на ортогональные виды сверху и пересаживает
гекс-данные (препятствия/трудный проход/спавны) на фактически
нарисованные объекты, а также ставит маркеры локаций нарисованной
схемы ярусов в world.json на свои ярусы.
Запуск: python3 tools/fix_arenas_map.py
"""
import json
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREV = os.path.join(os.path.dirname(ROOT), "_preview")

ARENAS = {
    "arena_pump": {
        "src": "arena_pump_top.png",
        "blocked": [(3, 1), (4, 1), (5, 1), (3, 2), (4, 2), (5, 2), (3, 3),
                    (4, 3), (5, 3), (3, 4), (4, 4), (5, 4), (3, 5), (4, 5),
                    (5, 5), (6, 1), (7, 1), (8, 1), (9, 1), (7, 4), (8, 4)],
        "difficult": [(2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (9, 3), (10, 3),
                      (9, 4), (10, 4), (9, 5), (10, 5)],
        "player": [(0, 2), (0, 3), (0, 4)],
        "enemy": [(11, 1), (11, 3), (11, 5)],
    },
    "arena_office": {
        "src": "arena_office_top.png",
        "blocked": [(0, 2), (0, 3), (1, 1), (2, 1), (1, 2), (2, 2), (1, 3),
                    (2, 3), (1, 4), (2, 4)],
        "difficult": [],
        "player": [(0, 1), (0, 4)],
        "enemy": [(9, 2), (9, 3)],
    },
    "arena_gate": {
        "src": "arena_gate_top.png",
        "blocked": [(3, 0), (4, 0), (5, 0), (6, 0), (4, 1), (5, 1), (1, 3),
                    (8, 3), (0, 4), (0, 5)],
        "difficult": [(0, 0), (1, 0), (1, 1), (2, 1), (3, 2), (3, 3), (6, 2),
                      (6, 3), (3, 4), (4, 4), (4, 5), (5, 5)],
        "player": [(0, 1), (0, 2), (0, 3)],
        "enemy": [(9, 1), (9, 2), (9, 4)],
    },
    "arena_sluice": {
        "src": "arena_sluice_top.png",
        "blocked": [(4, 0), (5, 0), (4, 1), (5, 1), (4, 2), (5, 2), (6, 2),
                    (4, 3), (5, 3), (4, 4), (5, 4), (4, 5), (5, 5)],
        "difficult": [(0, 0), (1, 0), (2, 0), (3, 0), (6, 0), (7, 0), (8, 0),
                      (9, 0), (0, 5), (1, 5), (2, 5), (3, 5), (6, 5), (7, 5),
                      (8, 5), (9, 5), (9, 4)],
        "player": [(0, 2), (0, 3), (0, 4)],
        "enemy": [(9, 1), (9, 2), (9, 3)],
    },
    "arena_gallery": {
        "src": "arena_gallery_top.png",
        "blocked": [(2, 1), (4, 1), (8, 1), (10, 1), (2, 4), (4, 4), (8, 4),
                    (10, 4)],
        "difficult": [(1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (7, 2), (8, 2),
                      (9, 2), (10, 2), (11, 2), (1, 3), (2, 3), (3, 3), (4, 3),
                      (5, 3), (7, 3), (8, 3), (9, 3), (10, 3), (11, 3), (6, 2),
                      (6, 3), (0, 5), (1, 5)],
        "player": [(0, 0), (0, 1), (0, 2)],
        "enemy": [(11, 1), (11, 4), (10, 5)],
    },
    "arena_deep": {
        "src": "arena_deep_top.png",
        "blocked": [(1, 2), (9, 2), (4, 3), (8, 3), (8, 4), (9, 6)],
        "difficult": [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0),
                      (7, 0), (8, 0), (9, 0), (9, 3), (7, 4), (4, 6), (5, 6),
                      (6, 6), (7, 6), (5, 7), (6, 7), (0, 6), (1, 6), (0, 7),
                      (1, 7)],
        "player": [(0, 2), (0, 3), (0, 4)],
        "enemy": [(9, 1), (9, 5), (9, 7)],
    },
}

MAP_POSITIONS = {
    "loc_surface": (390, 95),    # верх левого ствола: контора Надзора
    "loc_gate": (860, 290),      # правый ствол, седьмой ярус: шлюз
    "loc_pump7": (900, 440),     # правый ствол, машинные ряды: седьмая помпа
    "loc_ward8": (400, 520),     # низ левого ствола: Сухой ряд восьмого
    "loc_deep9": (650, 650),     # затоп: светящаяся жила девятого яруса
}


def main():
    for aid, cfg in ARENAS.items():
        src = os.path.join(PREV, cfg["src"])
        dst = os.path.join(ROOT, "assets", "img", aid + ".jpg")
        im = Image.open(src).convert("RGB")
        if im.size != (1280, 720):
            im = im.resize((1280, 720), Image.LANCZOS)
        im.save(dst, quality=90)
        path = os.path.join(ROOT, "arenas", aid + ".json")
        d = json.load(open(path, encoding="utf-8"))
        hg = d["hex_grid"]
        hg["blocked_hexes"] = [list(h) for h in cfg["blocked"]]
        hg["difficult_terrain"] = [list(h) for h in cfg["difficult"]]
        d["spawn_zones"]["player"]["hexes"] = [list(h) for h in cfg["player"]]
        d["spawn_zones"]["enemy"]["hexes"] = [list(h) for h in cfg["enemy"]]
        json.dump(d, open(path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print("arena fixed:", aid)
    w = json.load(open(os.path.join(ROOT, "world.json"), encoding="utf-8"))
    for loc in w["regions"][0]["locations"]:
        if loc["id"] in MAP_POSITIONS:
            x, y = MAP_POSITIONS[loc["id"]]
            loc["position"] = {"x": x, "y": y}
            print("map marker:", loc["id"], x, y)
    json.dump(w, open(os.path.join(ROOT, "world.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
