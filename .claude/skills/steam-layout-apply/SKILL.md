---
name: steam-layout-apply
description: Finalize an edited Steam Input layout for loading into Steam. Runs pre-flight checks, converts {{Base::Title}} tokens back to numeric runtime IDs with convert_runtime_ids.py to-ids, confirms nothing was left unresolved, and hands off the JSON → VDF step. Use this whenever edits to a layout JSON in this repo are finished and it needs to go back into Steam, or when the user asks to run to-ids, finalize, export, or produce a VDF.
---

# Finalize a layout for Steam

## 1. Run the pre-flight check

```bash
python3 - path/to/layout.json <<'EOF'
import json, sys, collections
cm = json.load(open(sys.argv[1]))["controller_mappings"]
order = list(cm["actions"]) + list(cm["action_layers"])
keys = [int(k.split("_")[1]) for k in cm["action_layers"]]
dups = [t for t, n in collections.Counter(v["title"] for v in cm["action_layers"].values()).items() if n > 1]
print("layer order:  ", "OK" if keys == sorted(keys) else "OUT OF ORDER (list order != Preset_ numeric order)")
print("preset blocks:", "OK" if [p["name"] for p in cm["preset"]] == order else "MISMATCH (not in actions + layers order)")
print("preset ids:   ", "OK" if [p["id"] for p in cm["preset"]] == [str(i) for i in range(len(cm["preset"]))] else "not sequential 0..N")
print("dup titles:   ", dups or "none")
EOF
```

Continue only if every line is `OK` and `dup titles` is `none`:

- **Out of order or mismatched:** the generated IDs could be resolved against the wrong ordering on a fresh load, which silently swaps layers. Normalize first, while the file is still in title form. The procedure is in the `steam-layout-prep` skill and `findings/2026-07-11-layer-order-swap/FINDINGS.md`.
- **Duplicate titles:** every duplicate token becomes the ID of the *last* layer with that title. `to-ids` gives no warning about this. Stop and tell the user. The fix is to rename the layers, and then work out which `{{Base::<title>}}` tokens belong to which layer.

## 2. Convert titles to IDs

```bash
python3 convert_runtime_ids.py to-ids path/to/layout.json                                   # in place
python3 convert_runtime_ids.py to-ids path/to/layout.json --output path/to/layout_final.json
```

The script prints `Warning: Could not find runtime ID for '<title>'` for any token that doesn't match a current `Parent::Title`. The usual cause is a renamed layer. Those tokens stay in the file unchanged.

## 3. Verify nothing is left unresolved

```bash
grep -c 'controller_action [A-Za-z_]* {{' path/to/layout_final.json   # must print 0
```

## 4. Hand off for Steam

1. **JSON → VDF:** the user converts the file with the VS Code extension `pfwobcke.vscode-vdf`. This step can't be scripted from this repo.
2. **Test on a fresh load:** the user loads the layout and spot-checks the binds on any layers that were added, renamed, or reordered. Checking in the live editing session isn't enough, because there layers are resolved by handle and swaps don't show up.
3. **Return to editing:** to keep working, run `to-titles` again (see `steam-layout-prep`).

## Guardrails

- `to-ids` only checks that tokens resolve. It doesn't check that each bind targets the layer you intended, so review `add_layer` / `remove_layer` targets in title form before converting.
- If you renamed a set or layer, every token for it must use the new `Parent::Title` exactly.
- Don't reorder `actions` / `action_layers` after converting to IDs.

## References

- Converter: `convert_runtime_ids.py`
- Runtime ID rules and the load-order caveat: `README.md`, `resources/Steam Input JSON Structure.md`
