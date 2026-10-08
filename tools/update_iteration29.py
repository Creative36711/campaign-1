#!/usr/bin/env python3
"""Idempotent data changes for the 2026-10-08 engine/task update.
Run only against this iteration's incoming campaign; later edits may supersede it.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / name).read_text())


def save(name, obj):
    (ROOT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def flag(name):
    return {"type": "flag_set", "flag": name}


def not_flag(name):
    return {"type": "flag_not_set", "flag": name}


def effect_step(e):
    return {"kind": "effect", "effect": e}


def main():
    camp = load("campaign.json")
    # Registry metadata is player-facing. Do not change flag IDs.
    replacements = {"Т��шина": "Тишина", "Трес�� жаровни": "Треск жаровни"}
    def clean(o):
        if isinstance(o, str):
            for a, b in replacements.items():
                o = o.replace(a, b)
            return o
        if isinstance(o, list):
            return [clean(v) for v in o]
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        return o
    camp = clean(camp)
    for entry in camp["sounds"]:
        entry["loop"] = "/amb/" in str(entry["src"])
    if not any(x["id"] == "sfx_fire" for x in camp["sounds"]):
        camp["sounds"].append({"id": "sfx_fire", "label": "Короткий треск огня",
                                "src": "assets/audio/sfx/sfx_fire.ogg", "loop": False})
    new_flags = [
        {"id": "case_registered", "label": "Дело во входящих",
         "description": "Регистратор присвоил сшитому делу входящий номер. Блокирует повторную платную регистрацию; читается в диалоге, шкафу дел и записи журнала."},
        {"id": "guard_body_recovered", "label": "Яров вынесен из воды",
         "description": "Дознаватель и Ира вынесли тело Стася на сухой уступ с помощью верёвки. Скрывает одно тело в двух ракурсах восьмого яруса; читается в осмотре и журнале. Не путать с возвратом жетона."},
    ]
    ids = {f["id"] for f in camp["flags"]}
    camp["flags"].extend(f for f in new_flags if f["id"] not in ids)
    save("campaign.json", camp)

    labels = {
        "scene_gate_hall": ["Свет в шлюзе", "Ночная смена"],
        "scene_gate_office": ["Дело на столе", "Сшитое дело"],
        "scene_pump_hall": ["Помпа молчит", "Помпа работает"],
        "scene_pump_shaft": ["Над чёрным провалом", "Спуск со страховкой"],
        "scene_pump_room": ["Каморка без хозяина", "Вскрытый шкафчик"],
        "scene_dry_row": ["У общего огня", "Ночной Сухой ряд"],
        "scene_flood_gallery": ["Вода у мостков", "Большая вода"],
        "scene_sluice": ["Вода давит на затвор", "Вода сброшена", "Клапан для затвора"],
        "scene_drift": ["Глухая штольня", "Открытый тайник"],
        "scene_face": ["Жила в породе", "Шов стянут", "Сердцевина вынута"],
        "scene_office": ["Приёмные часы", "Режим тишины"],
        "scene_archive": ["Папки под печатями", "Дело №136 раскрыто"],
    }
    for sid, names in labels.items():
        filename = f"scenes/{sid}.json"
        scene = load(filename)
        assert len(scene["states"]) == len(names)
        assert scene["states"][0].get("condition") is None
        for state, name in zip(scene["states"], names):
            state["label"] = name
        for intro in scene.get("narrative_intro", []):
            if isinstance(intro, dict) and intro.get("sfx") == "snd_fire":
                intro["sfx"] = "sfx_fire"
        for slot in scene["slots"]:
            if slot.get("default_entity") == "item_dead_guard":
                slot["environmental"] = False
                slot["condition"] = {"not_flag": "guard_body_recovered"}
                slot.update({"x": 258, "y": 488, "w": 370, "h": 154}
                            if sid == "scene_flood_gallery" else
                            {"x": 36, "y": 475, "w": 378, "h": 150})
        if sid == "scene_sluice":
            # Conditional states must be exclusive regardless of engine ordering.
            scene["states"][2]["condition"]["not_flag"] = "sluice_ready"
        if sid == "scene_flood_gallery":
            for layer in scene.get("ambient", []):
                for cond in layer.get("conditions", []):
                    if cond.get("flag") == "flood":
                        cond["flag"] = "downpour_flood"
        if sid == "scene_dry_row":
            for slot in scene["slots"]:
                if slot["id"] == "slot_dozh":
                    slot["x"] = 280
                if slot["id"] == "slot_zhuk":
                    slot.update({"x": 533, "y": 305, "w": 108, "h": 310})
                if slot["id"] == "slot_bench_row":
                    slot.update({"x": 440, "y": 438, "w": 85, "h": 100})
        save(filename, scene)

    # Automata and undead must not have the new living breathing animation.
    for eid in ["npc_registrar", "npc_watchman", "npc_rotling"]:
        name = f"entities/{eid}.json"
        npc = load(name)
        npc["breathe"] = False
        if eid == "npc_registrar":
            npc["description"] = "Архивный автомат из меди и латуни: два стеклянных глаза, счётчик в груди и голос, который не умеет врать, но умеет не договаривать."
        save(name, npc)
    # The canonical portrait shows the hook on his right hand.
    vex = load("entities/npc_vex.json")
    vex["description"] = vex["description"].replace("левой кисти", "правой кисти")
    save("entities/npc_vex.json", vex)

    guard = load("entities/item_dead_guard.json")
    guard.update({"scene_sprite": "assets/img/items/sprite_dead_guard.png",
                  "shadow": False, "breathe": False})
    examine = guard["interact_options"][0]
    check = next(e for e in examine["effects"] if e["type"] == "skill_check_gate")
    for e in check["success_effects"]:
        if e["type"] == "show_message":
            e["text"] = "Ты разжимаешь сведённые пальцы и снимаешь с сорванной цепочки номерной жетон: Стась Яров. Он умер не от воды — на затылке след удара."
    for e in check["fail_effects"]:
        if e["type"] == "show_message":
            e["text"] = "Тело не удаётся перевернуть: кирасу затянуло илом. Верёвкой его можно освободить, но это займёт два часа."
    compare = next(o for o in guard["interact_options"] if o["label"].startswith("Сверить жетон"))
    compare["hint"] = "Нужны установленный номер жетона и наряд стражи из архива"
    compare["conditions"] = [flag("clue_guard"), {"type": "has_item", "item": "item_roster"}]
    compare["effects"][0]["success_effects"][-1]["text"] = "Ярова нет среди двенадцати стражей Келла. Его пост — затвор восьмого, а весь взвод по наряду назначен на седьмой. Люди оказались внизу вопреки официальной бумаге."
    additions = [
        {"label": "Освободить тело верёвкой", "once": True,
         "hint": "2 ч и верёвка; жетон будет найден без повторного броска. Верёвка останется у тебя.",
         "sound": "snd_chain", "sound_volume": 0.6,
         "conditions": [not_flag("clue_guard"), {"type": "has_item", "item": "item_rope"}],
         "effects": [{"type": "advance_time", "ticks": 2}] + deepcopy(check["success_effects"])},
        {"label": "Осмотреть тело ещё раз", "hint": "Бесплатно; номер и причина смерти уже установлены",
         "conditions": [flag("clue_guard")], "sound": "snd_cloth",
         "message": "Сорванная цепочка и след удара говорят о борьбе до затопления. Жетон принадлежит Стасю Ярову; возвращённый сестре жетон не означает, что тело уже вынесено."},
        {"label": "Вынести Ярова из воды", "once": True,
         "hint": "2 ч; нужна Ира в отряде и верёвка. 15 опыта; верёвка не расходуется.",
         "sound": "snd_chain", "sound_volume": 0.65,
         "conditions": [flag("clue_guard"), not_flag("guard_body_recovered"),
                        {"type": "in_party", "entity": "npc_ira"},
                        {"type": "has_item", "item": "item_rope"}],
         "effects": [{"type": "set_flag", "flag": "guard_body_recovered"},
                     {"type": "advance_time", "ticks": 2},
                     {"type": "grant_xp", "points": 15},
                     {"type": "change_disposition", "target": "npc_ira", "delta": 5},
                     {"type": "journal_update", "quest": "quest_missing", "text_key": "j_recovered"}],
         "message": "Вы с Ирой обводите верёвку под кирасой и вытаскиваете Ярова на сухой уступ за галереей. Она укрывает брата своим плащом. Он больше не останется лежать в тяжёлой воде."},
    ]
    existing = {o["label"] for o in guard["interact_options"]}
    guard["interact_options"].extend(o for o in additions if o["label"] not in existing)
    save("entities/item_dead_guard.json", guard)
    missing = load("quests/quest_missing.json")
    missing["journal_entries"]["j_recovered"] = "С Ирой вы вынесли тело Стася из тяжёлой воды на сухой уступ за галереей. Вернуть жетон и вернуть человека — не одно и то же."
    save("quests/quest_missing.json", missing)
    rule = load("rules/rule_ira_brother.json")
    # stage_done already grants the intended 40 XP; do not award it twice.
    rule["effects"] = [e for e in rule["effects"] if e["type"] != "grant_xp"]
    save("rules/rule_ira_brother.json", rule)

    spoken = {
        3: "Расход мазута, смены мастера Реша Э. Пометка: «режим тишины — смотри приложение». Приложение изъято.",
        8: "Срок дознания по делу сто тридцать семь — семьдесят два часа. Чтение и разговор время не расходуют. Переходы и работа учитываются отдельно.",
        9: "Срок дознания не продлевают. Новая бумага не остановит воду. До истечения срока вы должны решить судьбу седьмой помпы.",
        10: "Материалы подшиты. Ставлю входящий штамп. Дело сто тридцать семь внесено в реестр. Изъятие оставит запись. Даже инспектор обязан указать основание.",
    }
    dlg = load("dialogues/registrar.dlg.json")
    ink_path = ROOT / "dialogues/registrar.ink"
    ink = ink_path.read_text()
    def update_lines(obj):
        nonlocal ink
        if isinstance(obj, dict):
            if isinstance(obj.get("voice"), str):
                for number, text in spoken.items():
                    if obj["voice"] == f"assets/voice/registrar_{number}.mp3":
                        ink = ink.replace(obj["text"], text)
                        obj["text"] = text
            for v in obj.values():
                update_lines(v)
        elif isinstance(obj, list):
            for v in obj:
                update_lines(v)
    update_lines(dlg)
    choices = dlg["nodes"][0]["choices"]
    roster = next(ch for ch in choices if any(st.get("effect", {}).get("item") == "item_roster"
                    for sec in ch.get("sections", []) for st in sec.get("steps", [])))
    roster["conds"] = [{"type": "has_item", "item": "item_plate"},
                        {"type": "flag", "flag": "clue_roster", "not": True}]
    ink = ink.replace('* { has_item("item_plate") }',
                      '* { has_item("item_plate") and not (get_flag("clue_roster")) }')
    register = next(ch for ch in choices if "сшито" in ch["text"])
    old_label = register["text"]
    register["text"] = "Зарегистрировать сшитое дело №137 (1 ч)."
    register["once"] = True
    register["conds"] = [{"type": "flag", "flag": "case_full"},
                          {"type": "flag", "flag": "case_registered", "not": True}]
    register["sections"][0]["steps"] = [register["sections"][0]["steps"][0],
                                         effect_step({"type": "fire_rule", "rule": "rule_register_case"})]
    ink = ink.replace(f'+ {{ get_flag("case_full") }} [{old_label}]',
                      f'* {{ get_flag("case_full") and not (get_flag("case_registered")) }} [{register["text"]}]')
    ink = ink.replace('    ~ unlock_codex("codex_case137")',
                      '    ~ fire_rule("rule_register_case")')
    repeat_label = "Перечитать полученный наряд."
    if not any(ch["text"] == repeat_label for ch in choices):
        text = "Взвод старшины Келла Ястреба, двенадцать человек, седьмой ярус, с двадцати до шести. Пометки о смене нет."
        choices.insert(-1, {"text": repeat_label, "goto": "stay",
                            "conds": [{"type": "flag", "flag": "clue_roster"}],
                            "sections": [{"steps": [{"kind": "line", "line": {
                                "text": text, "emotion": "calm", "voice": "assets/voice/registrar_5.mp3"}}]}]})
        insert = f'+ {{ get_flag("clue_roster") }} [{repeat_label}]\n    {text} # emotion: calm # voice: assets/voice/registrar_5.mp3\n    -> Начало_hub\n'
        ink = ink.replace('+ [Отключись.]', insert + '+ [Отключись.]')
    save("dialogues/registrar.dlg.json", dlg)
    ink_path.write_text(ink)

    save("rules/rule_register_case.json", {
        "id": "rule_register_case", "label": "Входящий номер дела №137", "once": True,
        "manual": True, "conditions": [flag("case_full"), not_flag("case_registered")],
        "effects": [{"type": "set_flag", "flag": "case_registered"},
                    {"type": "advance_time", "ticks": 1},
                    {"type": "unlock_codex", "entry": "codex_case137"},
                    {"type": "unlock_codex", "entry": "codex_registry"},
                    {"type": "journal_update", "quest": "quest_pump", "text_key": "j_registered"},
                    {"type": "grant_xp", "points": 10}], "chapter": "ch_signs"})
    pump = load("quests/quest_pump.json")
    pump["journal_entries"]["j_registered"] = "Сшитое дело №137 внесено во входящий реестр архива. Изъятие теперь оставит след в книге Регистратора. Это не продлевает срок и не заменяет решение о помпе."
    save("quests/quest_pump.json", pump)
    save("codex/codex_registry.json", {
        "id": "codex_registry", "label": "Входящий номер", "category": "chronicles",
        "text": "Штамп не делает бумагу правдой. Он делает её существование проверяемым. Сшитое дело №137 получило входящий номер: если Каст заберёт папку, в книге архива останется строка об изъятии. Регистратор хранит не человека и не справедливость, а последовательность записей. Этого недостаточно, чтобы остановить воду, но достаточно, чтобы следующее дело не начиналось с пустого шкафа. Регистрация занимает час; чтение уже выданного наряда — бесплатно.",
        "image": "assets/img/codex/codex_case137.jpg"})
    case = load("entities/item_case.json")
    if not any(o["label"] == "Сверить входящий номер" for o in case["interact_options"]):
        case["interact_options"].append({"label": "Сверить входящий номер", "effects": [], "sound": "snd_paper",
            "hint": "Бесплатно: проверить зарегистрированное дело", "conditions": [flag("case_registered")],
            "message": "Номер сто тридцать семь. Дата, подпись автомата, отметка о подшитых материалах. Папку ещё можно забрать, но нельзя сделать вид, что её никогда не было."})
    save("entities/item_case.json", case)
    manifest = load("manifest.json")
    for section, filename in [("rules", "rule_register_case.json"), ("codex", "codex_registry.json")]:
        if filename not in manifest[section]:
            manifest[section].append(filename)
    save("manifest.json", manifest)


if __name__ == "__main__":
    main()
