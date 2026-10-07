#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Выравнивает слоты и зоны переходов по нарисованным объектам фонов.

Правки внесены по визуальному аудиту превью (tools/visual_preview.py):
прямоугольники слотов/навигации кладутся на фактически нарисованные
объекты и линии пола, чтобы НПС стояли на полу, а хотспоты предметов
совпадали с нарисованными вещами.
Запуск: python3 tools/fix_slot_placement.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# scene_id -> {slot_id: (x, y, w, h)}
SLOTS = {
    "scene_pump_hall": {
        "slot_ira": (100, 300, 240, 360),        # ноги на пол у пульта, не на тумбу
        "slot_pump": (500, 100, 450, 460),       # по корпусу помпы с маховиком
        "slot_door_resh": (1030, 225, 110, 235), # по нарисованной двери каморки
    },
    "scene_pump_room": {
        "slot_stove": (215, 345, 185, 235),      # по буржуйке с топкой
        "slot_notes": (450, 350, 480, 210),      # по столу с чертежами
        "slot_locker": (960, 90, 265, 610),      # по всему шкафу до пола
    },
    "scene_pump_shaft": {
        "slot_winch": (470, 30, 310, 190),       # барабан лебёдки с балкой
        "slot_ladder": (785, 140, 375, 520),     # скобы лестницы по диагонали
        "slot_niche": (150, 175, 210, 295),      # арка ниши в кладке
    },
    "scene_sluice": {
        "slot_gate_mech": (440, 90, 430, 555),   # полотно затвора с маховиком
        "slot_dead_guard": (90, 400, 240, 240),  # кираса погибшего на полке
    },
    "scene_flood_gallery": {
        "slot_corpse": (250, 450, 220, 210),     # мешок/тело guard у завала
        "slot_debris": (0, 390, 250, 270),       # сам завал слева, не вода
        "slot_pipes": (820, 150, 290, 360),      # гребёнка труб с вентилями
    },
    "scene_dry_row": {
        "slot_dozh": (190, 360, 240, 330),       # ноги на камни перед прилавком
        "slot_ayla": (860, 350, 240, 310),       # ноги на пол у правой палатки
        "slot_zhuk": (600, 245, 150, 200),       # рост по перспективе прохода
        "slot_brazier": (645, 445, 140, 145),    # по жаровне с углями
        "slot_bench_row": (440, 415, 145, 130),  # по нарисованной скамье
    },
    "scene_gate_hall": {
        "slot_vex": (900, 320, 210, 300),        # ноги на пол перед затвором
        "slot_board": (460, 415, 95, 100),      # доска с бумагами на столбе
        "slot_crate": (270, 495, 160, 130),      # штабель ящиков у лестницы
        "slot_guest": (560, 340, 200, 320),      # гостевой слот на полу прохода
    },
    "scene_gate_office": {
        "slot_case": (55, 135, 235, 470),        # шкаф-картотека слева целиком
        "slot_cot": (300, 390, 165, 230),        # койка с одеялом вдоль стены
        "slot_bench": (1000, 420, 280, 280),     # верстак с тисками, без буржуйки
    },
    "scene_office": {
        "slot_kast": (250, 340, 240, 320),       # перед столом, не внутри стола
    },
    "scene_drift": {
        "slot_vent": (275, 30, 150, 160),        # круглая решётка вентиляции
        "slot_marker": (365, 245, 130, 160),     # щит «14» с кирками
    },
    "scene_face": {
        "slot_hoist": (990, 80, 220, 600),       # вся стойка лебёдки с блоком
        "slot_resh": (55, 330, 240, 350),        # не встык со слотом жилы
    },
}

# scene_id -> {label перехода: (x, y, w, h)}
NAV = {
    "scene_pump_hall": {"В каморку мастера": (1025, 460, 120, 70),
                        "На схему ярусов": (20, 665, 220, 50)},
    "scene_pump_room": {"В машинный зал": (0, 60, 150, 510)},
    "scene_pump_shaft": {"Подняться в машинный зал": (990, 0, 240, 130)},
    "scene_flood_gallery": {"К затвору": (400, 260, 170, 150),
                          "В сухой ряд": (5, 140, 170, 240)},
    "scene_gate_hall": {"На схему ярусов": (20, 600, 160, 100)},
    "scene_gate_office": {"В шлюзовую камеру": (690, 140, 165, 240)},
    "scene_archive": {"На схему ярусов": (250, 630, 220, 85)},
    "scene_drift": {"В забой": (700, 300, 240, 220)},
}

# слоты, которых не должно быть в отдельных состояниях сцены
SLOT_CONDITIONS = {
    ("scene_face", "slot_vein"): {
        "type": "not",
        "condition": {
            "type": "or",
            "conditions": [
                {"type": "flag_set", "flag": "vein_braced"},
                {"type": "flag_set", "flag": "core_taken"},
            ],
        },
    },
}


def main():
    for scene_id, slots in SLOTS.items():
        path = os.path.join(ROOT, "scenes", scene_id + ".json")
        sc = json.load(open(path, encoding="utf-8"))
        for sl in sc.get("slots", []):
            if sl["id"] in slots:
                x, y, w, h = slots[sl["id"]]
                sl["x"], sl["y"], sl["w"], sl["h"] = x, y, w, h
            key = (scene_id, sl["id"])
            if key in SLOT_CONDITIONS:
                sl["condition"] = SLOT_CONDITIONS[key]
        for nv in sc.get("navigation", []):
            if nv.get("label") in NAV.get(scene_id, {}):
                x, y, w, h = NAV[scene_id][nv["label"]]
                nv["area"] = {"x": x, "y": y, "w": w, "h": h}
        json.dump(sc, open(path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print("patched", scene_id)


if __name__ == "__main__":
    main()
