#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Привязывает озвучку к репликам и кадрам катсцен.

Одновременно правит три места:
  * dialogues/<имя>.dlg.json — поле `voice` у строки реплики (конструктор);
  * dialogues/<имя>.ink     — тег `# voice: путь` в конце строки (движок);
  * cutscenes/*.json        — поле `voice` у слайда.

Сопоставление идёт по точному тексту реплики, поэтому текст клипа
должен совпадать с текстом строки один в один.
Запуск: python3 tools/patch_voice.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# диалог -> [(текст реплики, файл озвучки)]
LINES = {
    "ira": [("Ты насчёт помпы? Я уже всё рассказала старшине. Он велел не мешать.",
             "assets/voice/ira_1.mp3")],
    "kast": [("Дело сто тридцать семь. У тебя семьдесят два часа, дознаватель. Говори коротко.",
              "assets/voice/kast_1.mp3")],
    "resh": [("Ты пришёл меня арестовать или послушать? Арестовывать удобнее: "
              "для этого не надо понимать.", "assets/voice/resh_1.mp3"),
             ("Я снял сердцевину. Пока затвор не ходит, помпу пускать нельзя: "
              "вода пойдёт в восьмой и не вернётся.", "assets/voice/resh_2.mp3")],
    "vein": [("Ты пришёл с чужим жетоном и чужим сроком. Я помню всех, кто брал.",
              "assets/voice/vein_1.mp3"),
             ("Ты молчишь. Я слышала этот ответ от всех, кто брал. Он всегда означал «дам».",
              "assets/voice/vein_2.mp3")],
}

# катсцена -> [(индекс слайда, файл озвучки)]
SLIDES = {
    "cutscene_intro": [(0, "assets/voice/prologue_1.mp3"),
                       (1, "assets/voice/prologue_2.mp3"),
                       (2, "assets/voice/prologue_3.mp3")],
    "cutscene_final_vein": [(0, "assets/voice/final_vein_1.mp3")],
}


def load(p):
    return json.load(open(p, encoding="utf-8"))


def save(p, o):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, ensure_ascii=False, indent=1)


def patch_dlg(name, pairs):
    dpath = os.path.join(ROOT, "dialogues", name + ".dlg.json")
    if not os.path.exists(dpath):
        print("нет файла", dpath)
        return []
    doc = load(dpath)
    hit = set()
    for node in doc["nodes"]:
        for sec in node.get("sections", []) + [s for ch in node.get("choices", [])
                                                for s in ch.get("sections", [])]:
            for step in sec.get("steps", []):
                if step["kind"] != "line":
                    continue
                for text, vf in pairs:
                    if step["line"]["text"] == text:
                        step["line"]["voice"] = vf
                        hit.add(vf)
    save(dpath, doc)
    return hit


def patch_ink(name, pairs):
    ipath = os.path.join(ROOT, "dialogues", name + ".ink")
    if not os.path.exists(ipath):
        print("нет файла", ipath)
        return
    lines = open(ipath, encoding="utf-8").read().split("\n")
    for text, vf in pairs:
        base = text  # текст реплики без тегов
        done = False
        for i, ln in enumerate(lines):
            s = ln.strip()
            if not s or s.startswith(("EXTERNAL", "VAR", "===", "->", "+", "*", "~", "{", "- ")):
                continue
            # отсекаем уже существующие теги
            clean = s.split(" # ")[0].strip()
            if clean == base and "# voice:" not in s:
                lines[i] = s + " # voice: " + vf
                done = True
                break
        if not done:
            print(f"  ВНИМАНИЕ: в {name}.ink не найдена строка «{base[:40]}…»")

    with open(ipath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    for name, pairs in LINES.items():
        for _, vf in pairs:
            if not os.path.exists(os.path.join(ROOT, vf)):
                print("нет файла озвучки:", vf)
        hit = patch_dlg(name, pairs)
        patch_ink(name, pairs)
        print(f"{name}: озвучено реплик — {len(hit)} из {len(pairs)}")

    for cid, pairs in SLIDES.items():
        p = os.path.join(ROOT, "cutscenes", cid + ".json")
        if not os.path.exists(p):
            print("нет катсцены", cid)
            continue
        c = load(p)
        for idx, vf in pairs:
            c["slides"][idx]["voice"] = vf
        save(p, c)
        print(f"{cid}: озвучено слайдов — {len(pairs)}")


if __name__ == "__main__":
    main()
