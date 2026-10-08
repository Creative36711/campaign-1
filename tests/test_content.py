"""Data-level regressions, not a reimplementation/playtest of Chronicle Forge.

The small harness only runs the deterministic effects/conditions needed by these
regressions. Unknown effects are recorded, not silently treated as game behavior.
Run: .venv/bin/python -m unittest discover -s tests -v
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.content_checks import check, check_alpha


def load(path):
    return json.loads((ROOT / path).read_text())


class EffectHarness:
    """State for selected deterministic effects; no time/AI/combat simulation."""
    def __init__(self, success=True):
        self.flags = set()
        self.equipment = set()
        self.statuses = set()
        self.event_location = None
        self.items = Counter()
        self.variables = Counter()
        self.party = set()
        self.quests = {}
        self.quest_visits = set()
        self.fired = set()
        self.once_options = set()
        self.needs = Counter(need_warmth=50)
        self.xp = self.ticks = 0
        self.success = success
        self.codex, self.journal = set(), {}
        self.observed = []

    def allows(self, conditions):
        for cond in conditions or []:
            kind = cond['type']
            if kind in ('flag_set', 'flag_not_set', 'flag'):
                result = cond['flag'] in self.flags
                if kind == 'flag_not_set' or cond.get('not'):
                    result = not result
            elif kind in ('or', 'and'):
                result = any(self.allows([x]) for x in cond['conditions']) if kind == 'or' else self.allows(cond['conditions'])
            elif kind == 'not':
                result = not self.allows([cond['condition']])
            elif kind == 'equipped':
                result = cond['item'] in self.equipment
            elif kind == 'has_status':
                result = cond['status'] in self.statuses
            elif kind == 'player_enters_location':
                result = cond['location'] == self.event_location
            elif kind == 'has_item':
                result = self.items[cond['item']] >= cond.get('min_quantity', 1)
            elif kind == 'in_party':
                result = cond['entity'] in self.party
            elif kind == 'variable_compare':
                lhs, rhs = self.variables[cond['var']], cond['value']
                result = {'>=': lhs >= rhs, '>': lhs > rhs, '==': lhs == rhs,
                          '<=': lhs <= rhs, '<': lhs < rhs, '!=': lhs != rhs}[cond['operator']]
            elif kind == 'quest_at_stage':
                result = self.quests.get(cond['quest']) == cond['stage']
            else:
                raise AssertionError('Condition outside this regression harness: ' + kind)
            if not result:
                return False
        return True

    def stage(self, quest, stage):
        self.quests[quest] = stage
        key = (quest, stage)
        if key not in self.quest_visits:
            self.quest_visits.add(key)
            q = load('quests/' + quest + '.json')
            self.effects(next(s for s in q['stages'] if s['id'] == stage).get('on_enter_effects', []))

    def rule(self, rule_id):
        rule = load('rules/' + rule_id + '.json')
        if rule.get('once') and rule_id in self.fired:
            return
        if not self.allows(rule.get('conditions', [])):
            return
        if rule.get('once'):
            self.fired.add(rule_id)
        self.effects(rule['effects'])

    def effects(self, effects):
        for effect in effects:
            kind = effect['type']
            if kind == 'set_flag':
                self.flags.add(effect['flag'])
            elif kind == 'clear_flag':
                self.flags.discard(effect['flag'])
            elif kind in ('add_item', 'remove_item'):
                qty = effect.get('quantity', effect.get('qty', 1))
                self.items[effect['item']] += qty if kind == 'add_item' else -qty
            elif kind == 'change_variable':
                self.variables[effect['var']] += effect['delta']
            elif kind == 'set_variable':
                self.variables[effect['var']] = effect['value']
            elif kind == 'advance_time':
                self.ticks += effect['ticks']
            elif kind == 'grant_xp':
                self.xp += effect['points']
            elif kind == 'change_need':
                self.needs[effect['need']] += effect['delta']
            elif kind == 'fire_rule':
                self.rule(effect['rule'])
            elif kind == 'advance_quest':
                self.stage(effect['quest'], effect['stage'])
            elif kind == 'start_quest':
                if effect['quest'] not in self.quests:
                    q = load('quests/' + effect['quest'] + '.json')
                    self.stage(q['id'], q['stages'][0]['id'])
            elif kind == 'skill_check_gate':
                self.effects(effect['success_effects'] if self.success else effect['fail_effects'])
            elif kind == 'apply_status':
                self.statuses.add(effect['status'])
            elif kind == 'remove_status':
                self.statuses.discard(effect['status'])
            elif kind == 'unlock_codex':
                self.codex.add(effect['entry'])
            elif kind == 'journal_update':
                self.journal[(effect['quest'], effect['text_key'])] = True
            elif kind in ('show_message', 'change_disposition', 'play_sound'):
                self.observed.append(effect)
            else:
                raise AssertionError('Effect outside this regression harness: ' + kind)

    def interact(self, entity, label):
        options = [o for o in load('entities/' + entity + '.json')['interact_options'] if o['label'] == label]
        for option in options:
            key = (entity, label)
            if option.get('once') and key in self.once_options:
                continue
            if not self.allows(option.get('conditions', [])):
                continue
            if option.get('once'):
                self.once_options.add(key)
            self.effects(option['effects'])
            return True
        return False


class ContentRegressions(unittest.TestCase):
    def test_complete_static_checks(self):
        self.assertEqual(check(ROOT), [])

    def test_campaign_identity_preserved(self):
        self.assertEqual(load('campaign.json')['id'], 'b7305faa-8e10-4d26-96bb-f1b5ed5e493f')

    def test_all_creation_budgets(self):
        campaign = load('campaign.json')
        cc = campaign['char_creation']
        stats = {'STR', 'CON', 'SIZ', 'DEX', 'INT', 'POW', 'CHA'}
        allowed = [s['id'] for s in campaign['skills'] if s['id'] not in cc['forbidden_skills']]
        for profession in cc['professions']:
            self.assertEqual(set(profession['stats']), stats)
            self.assertEqual(sum(v - cc['stat_limits']['min'] for v in profession['stats'].values()), cc['total_points'])
            for calling in cc['callings']:
                spent = 0
                for skill in allowed:
                    floor = max(cc['skill_floor'], 25 if skill in cc['mandatory_skills'] else 0)
                    floor += profession.get('skill_bonus', {}).get(skill, 0)
                    value = calling['skills'].get(skill, floor)
                    self.assertGreaterEqual(value, floor)
                    self.assertLessEqual(value, cc['skill_cap'])
                    spent += value - floor
                self.assertEqual(spent, cc['skill_points'], (profession['id'], calling['id']))

    def test_scene_state_priority_is_exclusive(self):
        for name, flags, expected in [
            ('scene_sluice', {'valve_found', 'sluice_ready'}, 'state_drained'),
            ('scene_face', {'vein_braced', 'core_taken'}, 'state_collared'),
        ]:
            scene = load('scenes/' + name + '.json')
            active = [s['id'] for s in scene['states'][1:]
                      if (not s['condition'].get('flag') or s['condition']['flag'] in flags)
                      and (not s['condition'].get('not_flag') or s['condition']['not_flag'] not in flags)]
            self.assertEqual(active, [expected])
            self.assertIsNone(scene['states'][0]['condition'])

    def test_corpse_shares_one_clue_between_both_views(self):
        model = EffectHarness()
        self.assertTrue(model.interact('item_dead_guard', 'Осмотреть тело'))
        self.assertFalse(model.interact('item_dead_guard', 'Осмотреть тело'))
        model.items['item_rope'] = 1
        self.assertFalse(model.interact('item_dead_guard', 'Освободить тело верёвкой'))
        self.assertEqual(model.items['item_guard_token'], 1)
        self.assertEqual(model.variables['clues'], 1)
        self.assertEqual(model.ticks, 1)
        self.assertTrue(model.interact('item_dead_guard', 'Обыскать карманы'))
        self.assertFalse(model.interact('item_dead_guard', 'Обыскать карманы'))
        self.assertEqual(model.items['item_mark'], 7)

    def test_failed_corpse_check_has_deterministic_rope_fallback(self):
        model = EffectHarness(success=False)
        self.assertTrue(model.interact('item_dead_guard', 'Осмотреть тело'))
        self.assertEqual(model.items['item_guard_token'], 0)
        self.assertFalse(model.interact('item_dead_guard', 'Освободить тело верёвкой'))
        model.items['item_rope'] = 1
        self.assertTrue(model.interact('item_dead_guard', 'Освободить тело верёвкой'))
        self.assertEqual(model.items['item_guard_token'], 1)
        self.assertEqual(model.items['item_rope'], 1)
        self.assertEqual(model.ticks, 3)
        self.assertFalse(model.interact('item_dead_guard', 'Освободить тело верёвкой'))

    def test_token_return_rewards_40_not_80(self):
        model = EffectHarness()
        model.interact('item_dead_guard', 'Осмотреть тело')
        model.rule('rule_ira_brother')
        self.assertEqual(model.xp, 40)
        self.assertEqual(model.items['item_guard_token'], 0)
        self.assertNotIn('guard_body_recovered', model.flags)
        model.rule('rule_ira_brother')
        self.assertEqual(model.xp, 40)
        self.assertEqual(model.items['item_tonic'], 2)

    def test_body_recovery_needs_ira_and_rope_and_is_once(self):
        model = EffectHarness()
        model.interact('item_dead_guard', 'Осмотреть тело')
        self.assertFalse(model.interact('item_dead_guard', 'Вынести Ярова из воды'))
        model.items['item_rope'] = 1
        self.assertFalse(model.interact('item_dead_guard', 'Вынести Ярова из воды'))
        model.party.add('npc_ira')
        self.assertTrue(model.interact('item_dead_guard', 'Вынести Ярова из воды'))
        self.assertFalse(model.interact('item_dead_guard', 'Вынести Ярова из воды'))
        self.assertEqual(model.xp, 15)
        self.assertEqual(model.ticks, 3)
        for name in ['scene_sluice', 'scene_flood_gallery']:
            slot = next(s for s in load('scenes/' + name + '.json')['slots'] if s.get('default_entity') == 'item_dead_guard')
            self.assertEqual(slot['condition'], {'not_flag': 'guard_body_recovered'})
            self.assertFalse(slot['environmental'])

    def test_roster_required_for_comparison(self):
        model = EffectHarness()
        model.flags.add('clue_guard')
        self.assertFalse(model.interact('item_dead_guard', 'Сверить жетон со списком смены'))
        model.items['item_roster'] = 1
        self.assertTrue(model.interact('item_dead_guard', 'Сверить жетон со списком смены'))
        self.assertEqual(model.xp, 10)

    def test_registration_once_and_one_hour(self):
        model = EffectHarness()
        model.rule('rule_register_case')
        self.assertEqual(model.ticks, 0)
        model.flags.add('case_full')
        model.rule('rule_register_case')
        model.rule('rule_register_case')
        self.assertEqual(model.ticks, 1)
        self.assertEqual(model.xp, 10)
        self.assertIn('codex_registry', model.codex)
        self.assertIn(('quest_pump', 'j_registered'), model.journal)

    def test_brace_release_cycle_does_not_farm_xp_or_warmth(self):
        model = EffectHarness()
        for _ in range(6):
            self.assertTrue(model.interact('item_hoist', 'Стянуть шов Жилы цепным бандажом'))
            self.assertTrue(model.interact('item_hoist', 'Ослабить цепной бандаж на Жиле'))
        self.assertEqual(model.xp, 15)
        self.assertEqual(model.needs['need_warmth'], 60)
        self.assertIn('vein_brace_rewarded', model.flags)

    def test_loop_sound_not_used_in_fire_intro(self):
        sounds = {s['id']: s for s in load('campaign.json')['sounds']}
        for name in ['scene_dry_row', 'scene_gate_office']:
            sound = load('scenes/' + name + '.json')['narrative_intro'][0]['sfx']
            self.assertEqual(sound, 'sfx_fire')
            self.assertFalse(sounds[sound]['loop'])
        self.assertTrue(sounds['snd_fire']['loop'])

    def test_howl_is_not_world_choking_or_damage(self):
        campaign = load('campaign.json')
        howl = next(a for a in campaign['abilities'] if a['id'] == 'ability_howl')
        status = next(s for s in campaign['statuses'] if s['id'] == howl['status'])
        self.assertEqual(status['scope'], 'combat')
        self.assertEqual(status['duration'], 2)
        self.assertNotIn('dot', status)
        self.assertNotEqual(status['id'], 'status_choke')

    def test_random_encounters_cannot_spawn_old_pairs(self):
        for table in load('encounters/encounters.json')['encounter_tables']:
            for entry in table['entries']:
                for enemy in entry.get('enemies', []):
                    self.assertEqual(enemy['count_min'], 1)
                    self.assertEqual(enemy['count_max'], 1)

    def test_empty_filter_does_not_protect_after_cough_expires(self):
        model = EffectHarness()
        model.equipment.add('item_filter')
        model.rule('rule_filter_protect')
        self.assertIn('filter_protected', model.flags)
        model.flags.update(['filter_bank_1', 'filter_bank_2'])
        # A world/scene update inside the deep is NOT a positive exit event.
        model.rule('rule_filter_exhausted')
        self.assertNotIn('filter_exhausted', model.flags)
        model.event_location = 'loc_ward8'
        model.rule('rule_filter_exhausted')
        model.rule('rule_filter_unprotect')
        self.assertIn('filter_exhausted', model.flags)
        self.assertNotIn('filter_protected', model.flags)
        model.event_location = 'loc_deep9'
        model.rule('rule_filter_spent')
        model.statuses.discard('status_filter_spent')  # After the defined 4-hour cough.
        model.rule('rule_filter_protect')
        self.assertNotIn('filter_protected', model.flags)
        air = next(n for n in load('campaign.json')['needs'] if n['id'] == 'need_air')
        self.assertEqual(air['decay_when'][1], {'type': 'flag', 'flag': 'filter_protected', 'not': True})

    def test_filter_refill_removes_cough_and_restores_protection(self):
        model = EffectHarness()
        model.equipment.add('item_filter')
        model.items.update(item_filter=1, item_coal=1, item_cloth=1)
        model.flags.update(['filter_bank_1', 'filter_bank_2', 'filter_exhausted'])
        model.statuses.add('status_filter_spent')
        self.assertTrue(model.interact('item_bench', 'Сменить банки в дыхателе'))
        model.rule('rule_filter_protect')
        self.assertIn('filter_protected', model.flags)
        self.assertNotIn('filter_exhausted', model.flags)
        self.assertNotIn('status_filter_spent', model.statuses)
        self.assertEqual(model.ticks, 1)
        self.assertEqual(model.items['item_coal'], 0)
        self.assertEqual(model.items['item_cloth'], 0)

    def test_unequipping_mask_and_upper_air_cough_clear(self):
        model = EffectHarness()
        model.equipment.add('item_filter')
        model.rule('rule_filter_protect')
        model.equipment.clear()
        model.rule('rule_filter_unprotect')
        self.assertNotIn('filter_protected', model.flags)
        model.statuses.add('status_filter_spent')
        model.event_location = 'loc_pump7'
        model.rule('rule_filter_clear_cough')
        self.assertNotIn('status_filter_spent', model.statuses)

    def test_package_file_list_is_complete_and_canonical(self):
        from tools.pack import collect_files
        files = collect_files(ROOT)
        self.assertIn('encounters/encounters.json', files)
        self.assertNotIn('rules/encounters.json', files)
        self.assertIn('assets/img/items/sprite_dead_guard.png', files)
        self.assertIn('assets/audio/sfx/sfx_fire.ogg', files)
        self.assertEqual(len(files), len(set(files)))
        self.assertTrue(all(not f.startswith(('__chronicle_ai__/', 'tools/', 'tests/')) for f in files))
        self.assertFalse(any(f.endswith('.chronicle') for f in files))

    def test_current_design_doc_copy_matches_campaign(self):
        self.assertEqual(load('campaign.json')['design_doc'], (ROOT/'tools/design_doc.md').read_text())

    def test_alpha_check_rejects_opaque_png(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Image.new('RGB', (4, 4), 'green').save(root / 'bad.png')
            issues = []
            check_alpha(root, 'bad.png', 'спрайт', issues)
            self.assertEqual(len(issues), 1)

    def test_time_graph_uses_arrival_scene_not_room_shortcut(self):
        from tools.time_budget import build_graph
        graph = build_graph()
        self.assertEqual(graph['scene_pump_hall']['scene_dry_row'], 2)
        self.assertNotIn('scene_flood_gallery', graph['scene_pump_hall'])
        self.assertNotIn('scene_sluice', graph['scene_pump_hall'])
        # From the shaft one must walk to the map exit, not teleport directly.
        self.assertNotIn('scene_dry_row', graph['scene_pump_shaft'])


if __name__ == '__main__':
    unittest.main()
