#!/usr/bin/env python3
"""Additional read-only regressions for the updated Chronicle format.
Checks declarations, media/alpha, live labels, loop contexts and resettable rewards.
These are static content checks, not a Chronicle Forge runtime playtest.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ["scenes", "entities", "rules", "arenas", "quests", "cutscenes", "recipes", "codex", "encounters"]
EXPECTED_AMBIENT = {"snd_crowd", "snd_deep_drone", "snd_drops", "snd_fire", "snd_pump_amb", "snd_rain", "snd_water_amb", "snd_wind", "snd_city_amb", "snd_shaft_amb"}
BAD_LABELS = {"Основное состояние", "Всегда", "Днём"}


def walk(obj, path=""):
    yield path, obj
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from walk(value, path + "/" + key)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            yield from walk(value, path + "/" + str(i))


def image_paths(value):
    for _, leaf in walk(value):
        if isinstance(leaf, str) and leaf.startswith("assets/"):
            yield leaf


def check_alpha(root, src, role, issues):
    path = root / src
    if not path.is_file():
        return  # Missing asset is reported separately.
    try:
        with Image.open(path) as image:
            if image.format != "PNG" or "A" not in image.getbands():
                issues.append(f"АЛЬФА {role}: {src} должен быть PNG с альфа-каналом")
                return
            alpha = image.getchannel("A")
            if alpha.getextrema()[0] != 0:
                issues.append(f"АЛЬФА {role}: {src} не содержит прозрачных пикселей")
            if role != "рамка":
                corners = [(0, 0), (image.width - 1, 0), (0, image.height - 1), (image.width - 1, image.height - 1)]
                if any(alpha.getpixel(pt) != 0 for pt in corners):
                    issues.append(f"АЛЬФА {role}: непрозрачные углы у {src}")
    except OSError as exc:
        issues.append(f"ИЗОБРАЖЕНИЕ {src}: {exc}")


def check(root: Path = ROOT) -> list[str]:
    issues = []
    manifest = json.loads((root / "manifest.json").read_text())
    campaign = json.loads((root / "campaign.json").read_text())
    sounds = {s["id"]: s for s in campaign["sounds"]}
    flags = {f["id"] for f in campaign["flags"]}
    documents = {"campaign.json": campaign, "world.json": json.loads((root / "world.json").read_text())}
    declared = set(documents)
    for section in SECTIONS:
        names = manifest.get(section, [])
        if len(set(names)) != len(names):
            issues.append(f"МАНИФЕСТ повтор файлов в {section}")
        for name in names:
            if Path(name).name != name:
                issues.append(f"МАНИФЕСТ {section}: нужен basename, а не путь {name}")
                continue
            rel = section + "/" + name
            path = root / rel
            if not path.is_file():
                issues.append(f"МАНИФЕСТ отсутствует {rel}")
                continue
            declared.add(rel)
            documents[rel] = json.loads(path.read_text())
            doc = documents[rel]
            if section == "encounters" and (not isinstance(doc, dict) or not isinstance(doc.get("encounter_tables"), list)):
                issues.append(f"ВСТРЕЧИ {rel}: требуется объект с encounter_tables")
            if section == "rules" and (not isinstance(doc, dict) or not isinstance(doc.get("conditions"), list) or not isinstance(doc.get("effects"), list)):
                issues.append(f"ПРАВИЛО {rel}: требуется объект с conditions и effects")
    if set(manifest.get("rules", [])) & set(manifest.get("encounters", [])):
        issues.append("МАНИФЕСТ файл встреч попал в rules")
    for section in ["rules", "encounters"]:
        for path in (root / section).glob("*.json"):
            if str(path.relative_to(root)) not in declared:
                issues.append(f"МАНИФЕСТ модуль не объявлен: {path.relative_to(root)}")
    for name in manifest["dialogues"]:
        ink = root / "dialogues" / name
        sidecar = ink.with_suffix(".dlg.json")
        if not ink.is_file() or not sidecar.is_file():
            issues.append(f"ДИАЛОГ нет пары Ink/конструктор для {name}")
            continue
        documents[str(sidecar.relative_to(root))] = json.loads(sidecar.read_text())
        for match in re.finditer(r'#\s*voice:\s*(\S+)', ink.read_text()):
            if not (root / match.group(1)).is_file():
                issues.append(f"МЕДИА {name}: нет {match.group(1)}")

    for filename, doc in documents.items():
        for path, value in walk(doc):
            if isinstance(value, str):
                if "\ufffd" in value:
                    at = value.index("\ufffd")
                    issues.append(f"ТЕКСТ {filename}{path}: повреждён UTF-8 «{value[max(0, at-25):at+30]}»")
                if value.startswith("assets/") and not (root / value).is_file():
                    issues.append(f"МЕДИА {filename}{path}: нет {value}")
            if not isinstance(value, dict):
                continue
            for key in ["sfx", "apply_sound", "remove_sound"]:
                sound = value.get(key)
                if sound in sounds and sounds[sound].get("loop") is True:
                    issues.append(f"ЗВУК {filename}{path}/{key}: фоновая петля используется как разовый эффект")
    for sound in campaign["sounds"]:
        expected = sound["id"] in EXPECTED_AMBIENT
        if sound.get("loop") is not expected:
            issues.append(f"LOOP {sound['id']}: ожидается {expected}")
    for track in campaign["music_tracks"]:
        if track.get("loop") is not True:
            issues.append(f"LOOP музыки {track['id']}: ожидается True")

    for name in manifest["scenes"]:
        scene = documents.get("scenes/" + name)
        if not scene:
            continue
        states = scene["states"]
        if not states or states[0].get("condition") is not None:
            issues.append(f"СОСТОЯНИЕ {scene['id']}: первым должен идти безусловный фон")
        if sum(state.get("condition") is None for state in states) != 1:
            issues.append(f"СОСТОЯНИЕ {scene['id']}: нужен ровно один безусловный фон")
        for state in states:
            if state.get("label") in BAD_LABELS:
                issues.append(f"НАЗВАНИЕ {scene['id']}/{state['id']}: служебная подпись видна игроку")
        for _, value in walk(scene):
            if isinstance(value, dict):
                cond = value.get("condition")
                if isinstance(cond, dict):
                    for key in ["flag", "not_flag"]:
                        if key in cond and cond[key] not in flags:
                            issues.append(f"ФЛАГ состояния {scene['id']}: {cond[key]}")
        for i, intro in enumerate(scene.get("narrative_intro", [])):
            if isinstance(intro, dict) and intro.get("sfx"):
                sound = intro["sfx"]
                if sound not in sounds and not (root / sound).is_file():
                    issues.append(f"ЗВУК интро {scene['id']}/{i}: нет {sound}")
        for layer in scene.get("ambient", []):
            for sound in layer.get("sounds", []) + ([layer["sound"]] if layer.get("sound") else []):
                if sound in sounds and sounds[sound].get("loop") is not True:
                    issues.append(f"ФОН {scene['id']}: {sound} не зациклен")
    for name in manifest["entities"]:
        entity = documents.get("entities/" + name)
        if not entity:
            continue
        for key in ["scene_sprite", "scene_sprite_states", "combat_figure", "combat_figure_states"]:
            for src in image_paths(entity.get(key)):
                check_alpha(root, src, entity["id"] + "/" + key, issues)
        if entity["id"] in {"npc_registrar", "npc_watchman", "npc_rotling", "item_dead_guard"} and entity.get("breathe") is not False:
            issues.append(f"ДЫХАНИЕ {entity['id']}: должно быть отключено")
    theme = campaign.get("theme", {})
    for src in image_paths(theme.get("menu", {}).get("title_art")):
        check_alpha(root, src, "эмблема", issues)
    for src in image_paths(theme.get("frame")):
        check_alpha(root, src, "рамка", issues)

    # Resettable prerequisites cannot protect repeatable XP/material rewards.
    clearable = {obj.get("flag") for doc in documents.values() for _, obj in walk(doc)
                 if isinstance(obj, dict) and obj.get("type") == "clear_flag"}
    for name in manifest["entities"]:
        entity = documents.get("entities/" + name, {})
        for option in entity.get("interact_options", []):
            if option.get("once"):
                continue
            gate_flags = {obj.get("flag") for _, obj in walk(option.get("conditions", []))
                          if isinstance(obj, dict) and obj.get("type") in {"flag_set", "flag_not_set"}}
            rewards = [obj for _, obj in walk(option.get("effects", [])) if isinstance(obj, dict)
                       and (obj.get("type") == "grant_xp" or obj.get("type") == "add_item")]
            if rewards and gate_flags and gate_flags <= clearable:
                issues.append(f"ФАРМ {entity.get('id')}/{option['label']}: награда защищена только сбрасываемыми флагами")
    return issues


if __name__ == "__main__":
    issues = check()
    for issue in issues:
        print(issue)
    print(f"Дополнительных проблем контента: {len(issues)}")
    raise SystemExit(1 if issues else 0)
