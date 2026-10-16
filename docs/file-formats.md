# File formats

- `.json` - Human-readable format for editing with these scripts
- `.vdf` - Valve Data Format used by Steam

Export JSON directly using the serializer from the installed
`pfwobcke.vscode-vdf` VS Code extension:

```bash
node tools/convert_vdf.mjs neptune/single-set-default_hold-gyro_latest.json
node tools/convert_vdf.mjs neptune/single-set-alternative_hold-gyro_latest.json
node tools/convert_vdf.mjs findings/2026-09-29-held-input-layer-transitions/rule-test.json
```

Each command writes/replaces the sibling `.vdf`, leaving the JSON intact. Use
`-o path/to/output.vdf` for a different destination. This requires Node.js with
`node:module.stripTypeScriptTypes` (tested on Node 26.7.0) and the installed
extension (tested on 5.12.3); no npm install or open VS Code window is needed.
It discovers the latest version under `~/.vscode/extensions`; use
`--extension /path/to/pfwobcke.vscode-vdf-version` for another location. The loader
uses the extension's bundled source map and reports an error if its structure
changes. Node may print an experimental API warning.

The exporter preserves repeated keys, binding order, and empty blocks, and checks
every output token before writing. It preserves existing VDF escape sequences
and escapes literal quotes, tabs, and line breaks introduced during JSON editing.
Like the extension, it uses JavaScript's JSON parsing and property order: use
arrays for repeated keys, and expect integer-like object keys in numeric order.
Unsupported values (including numbers, booleans, null, and empty arrays) and
unresolved `controller_action {{title}}` targets fail before writing.

Run the command-budget and layer-order checks before exporting, and use
`convert_runtime_ids.py to-ids` first when editing with title tokens. Only a
fresh load in Steam shows that Steam reads the file as written (assumptions A22
and A33). Converter tests: `node --test tests/node/test_convert_vdf.mjs`.

Both working layouts, to numeric IDs and back to titles:

```bash
python3 -m tools.convert_runtime_ids to-ids neptune/single-set-alternative_hold-gyro_latest.json &&
python3 -m tools.convert_runtime_ids to-ids neptune/single-set-default_hold-gyro_latest.json

python3 -m tools.convert_runtime_ids to-titles neptune/single-set-alternative_hold-gyro_latest.json &&
python3 -m tools.convert_runtime_ids to-titles neptune/single-set-default_hold-gyro_latest.json
```
