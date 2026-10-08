#!/usr/bin/env python3
"""Idempotent balance/story fixes discovered in the current audit.
No historic balance patch scripts are invoked. Entity and campaign IDs stay stable.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / name).read_text())


def save(name, doc):
    (ROOT / name).write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")


def main():
    camp = load("campaign.json")
    for track in camp["music_tracks"]:
        track["loop"] = True
    for feat in camp["progression"]["feats"]:
        if feat["id"] == "feat_hands":
            feat["description"] = "+10 к ремонту и +3 к максимальному здоровью. Прибавки даются один раз при выборе черты."
        elif feat["id"] == "feat_lungs":
            feat["description"] = "После пережитой гнили тело становится крепче: +1 к телосложению. Расход воздуха не меняется."
    for need in camp["needs"]:
        if need["id"] == "need_warmth":
            need["description"] = "Сырость подземных ярусов забирает тепло каждый час. В конторе на поверхности оно возвращается; внизу помогают печка, уголь и общий огонь."
        elif need["id"] == "need_thirst":
            need["description"] = "Запас чистой воды. Флягу можно купить у Векса или Дожа, а кипяток получить у печки за уголь и час работы."
    for ability in camp["abilities"]:
        if ability["id"] == "ability_howl":
            ability["description"] = "Глухой вой сбивает ритм: на два боевых раунда труднее целиться и бить. Новых псов не вызывает."
            ability["status"] = "status_howl"
    if not any(s["id"] == "status_howl" for s in camp["statuses"]):
        camp["statuses"].append({
            "id": "status_howl", "label": "Пепельный вой", "short_label": "Вой",
            "description": "Вой сбивает ритм: −5 к клинку, кулачному бою и стрельбе на два раунда. Мировое время и здоровье не затрагивает.",
            "scope": "combat", "duration": 2,
            "skill_mods": [{"skill": sk, "delta": -5} for sk in ["blade", "brawl", "shoot"]],
            "apply_message": "Глухой вой на миг сбивает ритм движений.",
            "expire_message": "Ты снова слышишь собственное дыхание."})
    if not any(f["id"] == "vein_brace_rewarded" for f in camp["flags"]):
        camp["flags"].append({
            "id": "vein_brace_rewarded", "label": "Бандаж освоен",
            "description": "За первую успешную установку бандажа уже выданы 15 опыта и 10 тепла. Флаг не снимается при ослаблении цепи; исключает бесконечные награды. Читается в правиле награды подъёмника."})
    save("campaign.json", camp)

    hoist = load("entities/item_hoist.json")
    brace = next(o for o in hoist["interact_options"] if o["label"] == "Стянуть шов Жилы цепным бандажом")
    gate = next(e for e in brace["effects"] if e["type"] == "skill_check_gate")
    gate["success_effects"] = [e for e in gate["success_effects"]
                                if e["type"] not in {"grant_xp", "change_need"}]
    if not any(e.get("rule") == "rule_vein_brace_reward" for e in gate["success_effects"]):
        gate["success_effects"].insert(2, {"type": "fire_rule", "rule": "rule_vein_brace_reward"})
    brace["hint"] = "Ремонт 45; при срыве 1 ч. Награда за первую установку — один раз; ослаблять и стягивать цепь можно снова."
    save("entities/item_hoist.json", hoist)
    save("rules/rule_vein_brace_reward.json", {
        "id": "rule_vein_brace_reward", "label": "Первая установка бандажа",
        "once": True, "manual": True,
        "conditions": [{"type": "flag_set", "flag": "vein_braced"},
                       {"type": "flag_not_set", "flag": "vein_brace_rewarded"}],
        "effects": [{"type": "set_flag", "flag": "vein_brace_rewarded"},
                    {"type": "grant_xp", "points": 15},
                    {"type": "change_need", "need": "need_warmth", "delta": 10}],
        "chapter": "ch_deep"})
    manifest = load("manifest.json")
    if "rule_vein_brace_reward.json" not in manifest["rules"]:
        manifest["rules"].append("rule_vein_brace_reward.json")
    save("manifest.json", manifest)

    encounters = load("encounters/encounters.json")
    for table in encounters["encounter_tables"]:
        for entry in table["entries"]:
            for enemy in entry.get("enemies", []):
                enemy["count_max"] = 1
                enemy["count_min"] = 1
            if entry.get("type") == "combat" and entry["enemies"][0]["entity"] == "npc_ashhound":
                entry["intro"] = "Из-под арки выходит один пёс. Его стая осталась в темноте."
            if table["id"] == "enc_deep" and entry.get("type") == "combat":
                entry["intro"] = "У рельса шевелится гнилец: он идёт на свет лампы."
    save("encounters/encounters.json", encounters)

    guard = load("entities/item_dead_guard.json")
    guard["description"] = "Страж Надзора у самой воды возле затвора. В сведённых пальцах зажата сорванная цепочка."
    compare = next(o for o in guard["interact_options"] if o["label"].startswith("Сверить жетон"))
    compare["effects"][0]["success_effects"][-1]["text"] = "В наряде Яров числится на седьмом ярусе, а тело найдено у затвора восьмого. Возле фамилии — прочерк: со смены не вышел, в сводку не подан. Его спуск не внесли в книгу."
    save("entities/item_dead_guard.json", guard)
    hound = load("codex/codex_hound.json")
    hound["text"] = "Одичавшие дворняги нижних ярусов. Шерсть серая от пепла, глаза красные от воды. Держатся стаей, но узкий проход обычно перекрывает один пёс. Его глухой вой сбивает ритм на два раунда: труднее целиться и бить. Вой не вызывает новую стаю и не заражает удушьем. Укус неглубокий; опаснее дать псу загнать себя в угол."
    save("codex/codex_hound.json", hound)


if __name__ == "__main__":
    main()
