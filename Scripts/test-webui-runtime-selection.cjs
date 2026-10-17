// Exercise the real refresh function and change handler without model loading.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(process.argv[2] || path.join(__dirname, '../src/genie_tts/WebUI/app.js'), 'utf8');
const start = source.indexOf('async function refreshRuntime() {');
const end = source.indexOf('async function refreshMemoryPolicy()', start);
const listenerStart = source.indexOf('  el("runtimeMode").addEventListener("change", () => {');
const listenerEnd = source.indexOf('\n  });', listenerStart) + '\n  });'.length;
assert.ok(start >= 0 && end > start && listenerStart >= 0 && listenerEnd > listenerStart);

function harness(fetchRuntime) {
  let change;
  const select = {
    value: 'cuda', dataset: {}, options: [{value: 'cpu'}, {value: 'cuda'}, {value: 'auto'}],
    addEventListener: (event, handler) => { assert.equal(event, 'change'); change = handler; },
  };
  const context = vm.createContext({
    config: {endpoints: {runtime: '/runtime'}}, el: () => select,
    apiJson: fetchRuntime, renderRuntime: () => {}, updateModeControls: () => {}, setBadge: () => {},
  });
  vm.runInContext(source.slice(start, end) + source.slice(listenerStart, listenerEnd), context);
  return {select, refresh: () => context.refreshRuntime(), change: () => change()};
}

test('first refresh reflects the actual CPU runtime', async () => {
  const ui = harness(async () => ({runtime_mode: 'cpu'}));
  await ui.refresh();
  assert.equal(ui.select.value, 'cpu');
});

test('polling preserves a user selection awaiting Apply', async () => {
  const ui = harness(async () => ({runtime_mode: 'cpu'}));
  await ui.refresh();
  ui.select.value = 'auto';
  ui.change();
  await ui.refresh();
  assert.equal(ui.select.value, 'auto');
});

test('a user change while the first request is pending is preserved', async () => {
  let complete;
  const ui = harness(() => new Promise((resolve) => { complete = resolve; }));
  const pending = ui.refresh();
  ui.select.value = 'auto';
  ui.change();
  complete({runtime_mode: 'cpu'});
  await pending;
  assert.equal(ui.select.value, 'auto');
});
