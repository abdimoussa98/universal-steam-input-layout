import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { convertJson, loadConverter } from '../../tools/convert_vdf.mjs';

// Exercise the installed converter; a missing extension must fail this suite.
const VDF = await loadConverter();
const convert = value => convertJson(JSON.stringify(value), VDF);
const cli = fileURLToPath(new URL('../../tools/convert_vdf.mjs', import.meta.url));

test('preserves repeated bindings, group order, and empty blocks', () => {
  const result = convert({ controller_mappings: {
    group: [
      { id: '8', bindings: { binding: ['key_press A', 'key_press B'] } },
      { id: '3', settings: {} },
    ],
    preset: {},
  } });

  assert.equal((result.match(/^\t"group"$/gm) ?? []).length, 2);
  assert.equal((result.match(/^\t\t\t"binding"/gm) ?? []).length, 2);
  assert.ok(result.indexOf('"8"') < result.indexOf('"3"'));
  assert.ok(result.indexOf('"key_press A"') < result.indexOf('"key_press B"'));
  assert.match(result, /\t\t"settings"\n\t\t\{\n\t\t\}/);
  assert.match(result, /\t"preset"\n\t\{\n\t\}/);
  assert.ok(result.endsWith('\n'));
  assert.ok(!result.includes('\r'));
});

test('escapes actual control characters and quotes without doubling VDF escapes', () => {
  const result = convert({ root: {
    text: 'line\nnext\rreturn\ttab "quoted"',
    escaped: String.raw`already \"quoted\" and \n escaped`,
    path: String.raw`C:\Games\Steam`,
    escaped_path: String.raw`C:\\Games\\Steam`,
  } });

  assert.ok(result.includes(String.raw`"line\nnext\rreturn\ttab \"quoted\""`));
  assert.ok(result.includes(String.raw`"already \"quoted\" and \n escaped"`));
  assert.ok(result.includes(String.raw`"C:\Games\Steam"`));
  assert.ok(result.includes(String.raw`"C:\\Games\\Steam"`));
});

test('rejects values that the extension would silently lose or change', () => {
  for (const value of [null, 42, true, false, [], [['nested']]]) {
    assert.throws(() => convert({ root: { value } }), undefined, JSON.stringify(value));
  }
  for (const value of [null, [], 'text', 42]) {
    assert.throws(() => convert(value), undefined, `root ${JSON.stringify(value)}`);
  }
  assert.throws(() => convertJson('{broken json', VDF));
});

test('rejects unresolved controller action targets', () => {
  assert.throws(() => convert({ root: { bindings: {
    binding: 'controller_action add_layer {{title}} 0 0, , ',
  } } }));
});

test('rejects malformed or structurally changed converter output', () => {
  const source = JSON.stringify({ root: { binding: ['first', 'second'] } });
  for (const rendered of [
    '"root" { "binding" "second" "binding" "first" }',
    '"root" { "binding" "first" }',
    '"root" { "binding" "first" "binding" "second"',
  ]) {
    assert.throws(() => convertJson(source, { stringify: () => rendered }));
  }
});

test('CLI writes a sibling or explicit output and preserves existing output on failure', () => {
  const temporary = mkdtempSync(join(tmpdir(), 'convert-vdf-test-'));
  try {
    const input = join(temporary, 'layout.json');
    const sibling = join(temporary, 'layout.vdf');
    const explicit = join(temporary, 'custom.vdf');
    const data = { root: { binding: ['first', 'second'], settings: {} } };
    writeFileSync(input, JSON.stringify(data));
    execFileSync(process.execPath, [cli, input], { stdio: 'pipe' });
    assert.equal(readFileSync(sibling, 'utf8'), convert(data));

    const extensions = join(homedir(), '.vscode', 'extensions');
    const installed = readdirSync(extensions)
      .filter(name => /^pfwobcke\.vscode-vdf-\d/.test(name))
      .sort((a, b) => b.localeCompare(a, undefined, { numeric: true }))[0];
    assert.ok(installed, 'The installed VDF extension is required');
    execFileSync(process.execPath,
      [cli, input, '-o', explicit, '--extension', join(extensions, installed)],
      { stdio: 'pipe' });
    assert.equal(readFileSync(explicit, 'utf8'), convert(data));

    writeFileSync(input, JSON.stringify({ root: { invalid: 42 } }));
    writeFileSync(explicit, 'keep this existing output\n');
    assert.throws(() => execFileSync(process.execPath,
      [cli, input, '-o', explicit], { stdio: 'pipe' }));
    assert.equal(readFileSync(explicit, 'utf8'), 'keep this existing output\n');
  } finally {
    rmSync(temporary, { recursive: true, force: true });
  }
});
