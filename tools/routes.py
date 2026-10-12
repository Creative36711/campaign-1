"""Маршруты для tools/route_sim.py: по одному на каждую концовку и вариант «Тишины».
Шаги: ('go', scene) · ('use', entity, подстрока опции, {rolls:[...], combat:'victory'|'defeat', dlg:[[...]]})
· ('talk', npc, [подстроки реплик], {knot, present, rolls}) · ('buy', npc, item, qty) · ('craft', recipe) · ('wait', ticks)."""

# общий «сюжетный» отрезок: ключ, клапан, затвор, открытие девятого яруса
CORE = [
    ('go', 'scene_gate_hall'),
    ('go', 'scene_pump_hall'),
    ('use', 'item_pump_engine', 'Снять с привода ключ'),
    ('go', 'scene_pump_shaft'),
    ('use', 'item_ladder', 'Спуститься по скобам'),
    ('use', 'item_niche', 'Обыскать нишу'),
    ('go', 'scene_pump_hall'),
    ('go', 'scene_flood_gallery'),
    ('go', 'scene_sluice'),
    ('use', 'item_sluice_mech', 'Установить клапан'),
    ('go', 'scene_office'),
    ('go', 'scene_archive'),
    ('use', 'item_shelf', 'Прочитать дело №136'),
]

ROUTES = {
    'pump_wright': {'prof': 'prof_wright', 'diff': 'diff_inspector', 'expect': 'ending_pump', 'steps': CORE + [
        ('go', 'scene_face'),
        ('talk', 'npc_resh', ['Затвор держит. Теперь отдай сердцевину.']),
        ('go', 'scene_pump_hall'),
        ('use', 'item_pump_engine', 'Вставить сердцевину'),
    ]},
}
