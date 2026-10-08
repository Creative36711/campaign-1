#!/usr/bin/env python3
"""Current filter lifecycle and unvoiced chronology corrections; idempotent.

NeedCondition can express AND, not an OR between unequipped/exhausted masks.
A maintained protection flag avoids an empty mask suppressing air loss forever.
No unsupported duration=0 or persistent-location rule conditions are used.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT / path).read_text())

def save(path, data):
    (ROOT / path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def main():
    campaign = load('campaign.json')
    if not any(f['id'] == 'filter_protected' for f in campaign['flags']):
        campaign['flags'].append({'id': 'filter_protected', 'label': 'Дыхатель работает',
            'description': 'Исправный дыхатель надет. Автоматически снимается при опустевших банках или снятии маски; подавляет убыль дыхания, но не расход других потребностей.'})
    air = next(n for n in campaign['needs'] if n['id'] == 'need_air')
    air['decay_when'] = [{'type': 'in_location', 'locations': ['loc_ward8', 'loc_deep9']},
                         {'type': 'flag', 'flag': 'filter_protected', 'not': True}]
    air['description'] = 'Запас дыхания. На восьмом и девятом ярусах он убывает, если нет исправного надетого дыхателя. Пустая маска не защищает; выше восьмого запас восстанавливается.'
    spent = next(s for s in campaign['statuses'] if s['id'] == 'status_filter_spent')
    spent['description'] = 'Пустая маска не защищает от расхода дыхания. После нового входа на девятый ярус четыре часа кашля: −1 здоровья за час, −10 к следствию и вниманию. На верхнем воздухе кашель снимается.'
    save('campaign.json', campaign)

    fresh_air = ['loc_gate', 'loc_pump7', 'loc_surface']
    outside_deep = fresh_air + ['loc_ward8']
    exhaustion = load('rules/rule_filter_exhausted.json')
    exhaustion['trigger'] = 'enter_scene'
    exhaustion['conditions'][-1] = {'type': 'or', 'conditions': [
        {'type': 'player_enters_location', 'location': loc} for loc in outside_deep]}
    save('rules/rule_filter_exhausted.json', exhaustion)
    bank1 = load('rules/rule_filter_bank1.json')
    bank1['effects'][1]['text'] = 'Маска шипит: первая банка работает на штольню. У слепого забоя придётся переключиться на вторую; её хватит и на подъём.'
    save('rules/rule_filter_bank1.json', bank1)
    spent_rule = load('rules/rule_filter_spent.json')
    spent_rule['effects'][1]['text'] = 'Маска хрипит впустую: банок нет. Запас дыхания снова убывает. Первые четыре часа спуска — кашель и мутное внимание; переснаряди обойму на верстаке.'
    save('rules/rule_filter_spent.json', spent_rule)

    new_rules = [
        {'id': 'rule_filter_protect', 'label': 'Исправный дыхатель надет',
         'conditions': [{'type': 'equipped', 'item': 'item_filter'},
                        {'type': 'flag_not_set', 'flag': 'filter_exhausted'},
                        {'type': 'flag_not_set', 'flag': 'filter_protected'}],
         'effects': [{'type': 'set_flag', 'flag': 'filter_protected'}]},
        {'id': 'rule_filter_unprotect', 'label': 'Дыхатель перестал защищать',
         'conditions': [{'type': 'flag_set', 'flag': 'filter_protected'},
                        {'type': 'or', 'conditions': [
                            {'type': 'flag_set', 'flag': 'filter_exhausted'},
                            {'type': 'not', 'condition': {'type': 'equipped', 'item': 'item_filter'}}]}],
         'effects': [{'type': 'clear_flag', 'flag': 'filter_protected'}]},
        {'id': 'rule_filter_clear_cough', 'label': 'Кашель отпускает на верхнем воздухе',
         'trigger': 'enter_scene',
         'conditions': [{'type': 'has_status', 'status': 'status_filter_spent'},
                        {'type': 'or', 'conditions': [
                            {'type': 'player_enters_location', 'location': loc} for loc in fresh_air]}],
         'effects': [{'type': 'remove_status', 'target': 'player', 'status': 'status_filter_spent'}]},
    ]
    manifest = load('manifest.json')
    for rule in new_rules:
        rule.update(once=False, manual=False, chapter='ch_deep')
        rule.setdefault('trigger', 'always')
        name = rule['id'] + '.json'
        save('rules/' + name, rule)
        if name not in manifest['rules']:
            manifest['rules'].append(name)
    save('manifest.json', manifest)

    for name, text in [
        ('rule_roster_got', 'Список подтверждает двенадцать человек на седьмом ярусе, с двадцати до шести. Пометки о смене нет. Теперь запись можно сопоставить со свидетельствами.'),
        ('rule_ira_story', 'Ты записываешь время: восемнадцать сорок — мастер в шахте, девятнадцать десять — помпа встала, двадцать ноль-ноль — в зал вошла стража. Между остановкой и приходом взвода — пятьдесят минут, которые наряд пока не объясняет.')]:
        rule = load('rules/' + name + '.json')
        next(e for e in rule['effects'] if e['type'] == 'show_message')['text'] = text
        save('rules/' + name + '.json', rule)
    cot = load('entities/item_cot.json')
    cot['interact_options'][0]['hint'] = 'Восемь часов из семидесяти двух: +2 здоровья, +15 тепла, запас сна до полной шкалы. Голод и жажда за эти часы продолжают расти.'
    save('entities/item_cot.json', cot)
    face = load('scenes/scene_face.json')
    face['states'][1]['condition']['not_flag'] = 'core_taken'
    save('scenes/scene_face.json', face)

if __name__ == '__main__':
    main()
