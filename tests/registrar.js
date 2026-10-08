'use strict';
// Actual compiled Ink with a persistent campaign-flag ledger across NEW stories.
// The ledger covers deterministic external calls, not the Forge runtime/UI.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {Compiler, Story} = require('inkjs/full');
process.on('uncaughtException', error => { console.error(error.message); process.exitCode = 1; });
const root = path.resolve(__dirname, '..');
const read = p => JSON.parse(fs.readFileSync(path.join(root, p), 'utf8'));
const compiled = new Compiler(fs.readFileSync(path.join(root, 'dialogues/registrar.ink'), 'utf8')).Compile().ToJson();
function ledger() { return {flags: new Set(), items: {}, fired: new Set(), codex: new Set(), stages: new Set(), ticks: 0, xp: 0}; }
function allows(w, conditions) {
  return (conditions || []).every(c => {
    if(c.type === 'flag_set') return w.flags.has(c.flag);
    if(c.type === 'flag_not_set') return !w.flags.has(c.flag);
    if(c.type === 'quest_at_stage') return w.stages.has(c.quest + '/' + c.stage);
    if(c.type === 'variable_compare') return false; // Additional clues are outside this small test.
    throw new Error('Unexpected condition: ' + c.type);
  });
}
function effects(w, list) {
  for(const e of list || []) {
    if(e.type === 'set_flag') w.flags.add(e.flag);
    else if(e.type === 'advance_time') w.ticks += e.ticks;
    else if(e.type === 'grant_xp') w.xp += e.points;
    else if(e.type === 'unlock_codex') w.codex.add(e.entry);
    else if(e.type === 'fire_rule') fire(w, e.rule);
    else if(e.type === 'advance_quest') {
      const key = e.quest + '/' + e.stage;
      if(!w.stages.has(key)) {
        w.stages.add(key);
        const stage = read('quests/' + e.quest + '.json').stages.find(s => s.id === e.stage);
        effects(w, stage.on_enter_effects);
      }
    } else if(!['change_variable','change_disposition','show_message','play_sound','journal_update'].includes(e.type)) {
      throw new Error('Unexpected effect: ' + e.type);
    }
  }
}
function fire(w, id) {
  const r = read('rules/' + id + '.json');
  if(r.once && w.fired.has(id) || !allows(w, r.conditions)) return;
  if(r.once) w.fired.add(id);
  effects(w, r.effects);
}
function drain(story) {
  let lines = [], n = 0;
  while(story.canContinue) {
    if(++n > 100) throw new Error('Nonterminating registrar continuation');
    lines.push(story.Continue().trim());
  }
  return lines;
}
function fresh(w) {
  const s = new Story(compiled);
  s.BindExternalFunction('add_item', (id, qty) => { w.items[id] = (w.items[id] || 0) + qty; return 0; }, false);
  s.BindExternalFunction('advance_time', t => { w.ticks += t; return 0; }, false);
  s.BindExternalFunction('fire_rule', id => { fire(w, id); return 0; }, false);
  s.BindExternalFunction('set_flag', id => { w.flags.add(id); return 0; }, false);
  s.BindExternalFunction('unlock_codex', id => { w.codex.add(id); return 0; }, false);
  s.BindExternalFunction('has_item', id => (w.items[id] || 0) > 0);
  s.BindExternalFunction('get_flag', id => w.flags.has(id));
  s.ChoosePathString('Начало');
  drain(s);
  return s;
}
function has(s, text) { return s.currentChoices.some(c => c.text.includes(text)); }
function choose(s, text) {
  const c = s.currentChoices.find(c => c.text.includes(text));
  assert(c, 'Missing choice: ' + text);
  s.ChooseChoiceIndex(c.index);
  return drain(s);
}
let tests = 0;
function test(name, fn) { fn(); tests++; console.log('ок: ' + name); }

test('Без пломбы нет наряда, времени и награды', () => {
  const w = ledger(), s = fresh(w);
  choose(s, 'Наряд стражи');
  assert.equal(w.items.item_roster || 0, 0);
  assert.equal(w.ticks, 0); assert.equal(w.xp, 0);
});
test('Наряд выдаётся ровно один раз даже в новом разговоре', () => {
  const w = ledger(); w.items.item_plate = 1;
  choose(fresh(w), 'Наряд стражи');
  assert.equal(w.items.item_roster, 1); assert.equal(w.ticks, 1); assert.equal(w.xp, 40);
  const next = fresh(w);
  assert(!has(next, 'Наряд стражи'));
  choose(next, 'Перечитать полученный наряд');
  assert.equal(w.items.item_roster, 1); assert.equal(w.ticks, 1); assert.equal(w.xp, 40);
});
test('Разговор с регистратором не регистрирует несшитое дело', () => {
  const w = ledger(); assert(!has(fresh(w), 'Зарегистрировать'));
  assert.equal(w.ticks, 0); assert.equal(w.xp, 0);
});
test('Регистрация ровно один час и десять XP во всех разговорах', () => {
  const w = ledger(); w.flags.add('case_full');
  choose(fresh(w), 'Зарегистрировать');
  assert(w.flags.has('case_registered')); assert(w.codex.has('codex_registry'));
  assert.equal(w.ticks, 1); assert.equal(w.xp, 10);
  assert(!has(fresh(w), 'Зарегистрировать'));
  fire(w, 'rule_register_case'); assert.equal(w.ticks, 1); assert.equal(w.xp, 10);
});
test('Повтор ведомости и дела 136 бесплатен', () => {
  const w = ledger(), s = fresh(w);
  choose(s, 'Ведомость'); choose(s, 'Ведомость');
  choose(s, 'Дело сто тридцать шесть'); choose(fresh(w), 'Дело сто тридцать шесть');
  assert.equal(w.ticks, 0); assert.equal(w.xp, 0);
  assert(w.codex.has('codex_case136'));
});
console.log(`\n${tests} регрессий Ink пройдено; это не движковый плейтест.`);
