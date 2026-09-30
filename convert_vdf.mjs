#!/usr/bin/env node
// Use the serializer shipped with pfwobcke.vscode-vdf, without a VS Code host.
import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join, resolve } from 'node:path';
import { stripTypeScriptTypes } from 'node:module';
import { pathToFileURL } from 'node:url';

export function loadConverter(extensionDir) {
  if (!extensionDir) {
    const root = join(homedir(), '.vscode', 'extensions');
    const names = readdirSync(root)
      .filter(name => /^pfwobcke\.vscode-vdf-\d/.test(name))
      .sort((a, b) => b.localeCompare(a, undefined, { numeric: true }));
    if (!names.length) {
      throw new Error('Install pfwobcke.vscode-vdf or pass --extension /path/to/extension.');
    }
    extensionDir = join(root, names[0]);
  }
  const manifest = JSON.parse(readFileSync(join(extensionDir, 'package.json'), 'utf8'));
  const sourceMap = JSON.parse(readFileSync(join(extensionDir, `${manifest.main}.map`), 'utf8'));
  const index = sourceMap.sources.findIndex(name => name.endsWith('/packages/vdf/src/VDF.ts'));
  if (index < 0 || !sourceMap.sourcesContent?.[index]) {
    throw new Error('This extension version does not include the expected VDF serializer source.');
  }
  // Only stringify is called: its dependencies are the two formatting enums.
  // Parser dependencies and the extension's VS Code activation code are not run.
  const source = sourceMap.sourcesContent[index]
    .replace(/^import .*\r?\n/gm, '')
    .replace('export class VDF', 'class VDF');
  const VDF = new Function('VDFIndentation', 'VDFNewLine',
    stripTypeScriptTypes(source) + '\nreturn VDF;'
  )({ Tabs: 0, Spaces: 1 }, { LF: 1, CRLF: 2 });
  return VDF;
}

// The extension stores VDF escape sequences verbatim in JSON. Preserve those,
// while escaping new quotes and line breaks introduced during ordinary editing.
function escapeString(value) {
  const escapes = { '\n': '\\n', '\r': '\\r', '\t': '\\t', '"': '\\"' };
  let result = '';
  for (let i = 0; i < value.length; i++) {
    const char = value[i];
    if (char === '\\') {
      const next = value[i + 1];
      if (next !== undefined && next.charCodeAt(0) >= 32) {
        result += char + next;
        i++;
      } else {
        result += '\\\\';
      }
    } else if (Object.hasOwn(escapes, char)) {
      result += escapes[char];
    } else if (char.charCodeAt(0) < 32) {
      throw new Error('Unsupported control character in a VDF string.');
    } else {
      result += char;
    }
  }
  return result;
}

function prepareObject(value, path = '$') {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${path}: expected an object; VDF values must be strings or objects.`);
  }
  const result = Object.create(null);
  for (const [key, item] of Object.entries(value)) {
    const escapedKey = escapeString(key);
    if (Object.hasOwn(result, escapedKey)) {
      throw new Error(`${path}: keys collide after VDF escaping.`);
    }
    const prepareValue = child => {
      if (typeof child === 'string') {
        if (/controller_action\s+\w+\s+\{\{/.test(child)) {
          throw new Error(`${path}.${key}: unresolved title token; run convert_runtime_ids.py to-ids first.`);
        }
        return escapeString(child);
      }
      return prepareObject(child, `${path}.${key}`);
    };
    if (Array.isArray(item)) {
      if (!item.length) throw new Error(`${path}.${key}: empty arrays cannot be represented in VDF.`);
      result[escapedKey] = item.map(prepareValue);
    } else {
      result[escapedKey] = prepareValue(item);
    }
  }
  return result;
}

// Compare the complete structural token stream, including duplicate keys,
// array order, empty blocks, and string contents, before writing any file.
function verifyOutput(data, output) {
  const expected = [];
  function visit(object) {
    for (const [key, values] of Object.entries(object)) {
      for (const value of Array.isArray(values) ? values : [values]) {
        expected.push(`"${key}"`);
        if (typeof value === 'string') {
          expected.push(`"${value}"`);
        } else {
          expected.push('{');
          visit(value);
          expected.push('}');
        }
      }
    }
  }
  visit(data);
  const token = /"(?:\\[^\r\n]|[^"\\\r\n])*"|[{}]|\s+/gy;
  const actual = [];
  let offset = 0;
  while (offset < output.length) {
    const match = token.exec(output);
    if (!match) throw new Error(`Invalid VDF output at character ${offset}.`);
    if (!/^\s+$/.test(match[0])) actual.push(match[0]);
    offset = token.lastIndex;
  }
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error('VDF verification failed: output changed keys, values, or their order.');
  }
}

export function convertJson(jsonText, VDF) {
  const data = prepareObject(JSON.parse(jsonText));
  const output = VDF.stringify(data, { indentation: 0, newLine: 1, tabSize: 4 });
  verifyOutput(data, output);
  return output;
}

function main(args) {
  let output;
  let extension;
  let input;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '-h' || args[i] === '--help') {
      console.log('Usage: node convert_vdf.mjs input.json [-o output.vdf] [--extension /path/to/extension]');
      return;
    }
    if (['-o', '--output', '--extension'].includes(args[i])) {
      const option = args[i];
      const value = args[++i];
      if (!value || value.startsWith('-')) throw new Error(`Missing value for ${option}.`);
      if (option === '--extension') extension = value;
      else output = value;
    } else if (args[i].startsWith('-') || input) {
      throw new Error(`Unexpected argument: ${args[i]}`);
    } else {
      input = args[i];
    }
  }
  if (!input || !/\.json$/i.test(input)) throw new Error('Supply one input.json file. Use --help for usage.');
  output ??= input.replace(/\.json$/i, '.vdf');
  if (!/\.vdf$/i.test(output)) throw new Error('The output filename must end in .vdf.');
  if (resolve(input) === resolve(output)) throw new Error('Input and output must be different files.');
  const converted = convertJson(readFileSync(input, 'utf8'), loadConverter(extension));
  writeFileSync(output, converted, 'utf8');
  console.log(`Wrote ${output} (verified keys, values, and order).`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    main(process.argv.slice(2));
  } catch (error) {
    console.error(`Conversion failed: ${error.message}`);
    process.exitCode = 1;
  }
}
