#!/usr/bin/env python3
"""How many games bind each keyboard key by default, from keymap.io's controls library.

Downloads every game's controls page (cached), reads the table of default PC
keys and the table of controller buttons, and prints:

  1. for each key, the number of games that bind it by default
  2. bindings that are a combination of keys
  3. what the games put on the controller's two stick clicks

Usage:
    python3 key_share.py [--cache DIR] > key-share.txt

A key counts once per game, however many actions it has there. Games with
fewer than nine PC bindings are skipped, and Tekken 8, whose table is arcade
notation and not keys.
"""
import argparse
import collections
import html
import os
import re
import tempfile
import time
import urllib.request

SITE = "https://keymap.io"
AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
EXCLUDE = {"tekken-8"}
MIN_BINDINGS = 9

NAMED = {
    "left shift": "Shift", "shift": "Shift", "right shift": "RShift",
    "left ctrl": "Ctrl", "ctrl": "Ctrl", "right ctrl": "RCtrl",
    "left alt": "Alt", "alt": "Alt", "caps lock": "Caps", "space": "Space", "tab": "Tab",
    "enter": "Enter", "escape": "Esc", "esc": "Esc", "backspace": "Backspace", "delete": "Delete",
    "home": "Home", "end": "End", "page up": "PgUp", "page down": "PgDn", "print screen": "PrtSc",
    "mouse 1": "Mouse1", "left click": "Mouse1", "left mouse": "Mouse1", "click": "Mouse1",
    "mouse 2": "Mouse2", "mouse 3": "Mouse3", "mouse 4": "Mouse4", "mouse 5": "Mouse5",
    "scroll up": "WheelUp", "scroll down": "WheelDn", "scroll": "Wheel",
    "up arrow": "Up", "down arrow": "Down", "left arrow": "Left", "right arrow": "Right",
    "arrow keys": "Arrows",
}
DIGITS = "1234567890"


def fetch(url, path):
    if not os.path.exists(path) or not os.path.getsize(path):
        request = urllib.request.Request(url, headers={"User-Agent": AGENT})
        with urllib.request.urlopen(request, timeout=30) as response, open(path, "wb") as out:
            out.write(response.read())
        time.sleep(0.4)
    with open(path, encoding="utf-8") as page:
        return page.read()


def text(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def tables(page):
    """Each table as (header cells, body rows)."""
    for table in re.findall(r"<table.*?</table>", page, re.S):
        rows = [[text(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, re.S)]
                for row in re.findall(r"<tr.*?</tr>", table, re.S)]
        rows = [r for r in rows if r]
        if rows:
            yield [c.lower() for c in rows[0]], rows[1:]


def read_game(page):
    """(PC bindings as (action, key string), controller bindings as (action, Xbox button))."""
    pc, pad = [], []
    for head, rows in tables(page):
        if head[:2] == ["action", "default key"]:
            pc += [(r[0], r[1]) for r in rows if len(r) > 1]
        elif head[0] == "action" and "xbox" in head and "pc" not in head:
            column = head.index("xbox")
            pad += [(r[0], r[column]) for r in rows if len(r) > column]
    return pc, pad


def one_key(token):
    """A single key name, or a range such as 1–9, as a list of keys."""
    token = re.sub(r"^(hold|double-tap)\s+", "", token.strip(), flags=re.I).strip()
    if token.lower() in NAMED:
        return [NAMED[token.lower()]]
    if re.fullmatch(r"[A-Z]|\d|F\d{1,2}|[`\-=/.,\[\];']", token):
        return [token]
    digits = re.fullmatch(r"(\d)\s*[–-]\s*(\d)", token)
    if digits:
        return list(DIGITS[DIGITS.index(digits.group(1)):DIGITS.index(digits.group(2)) + 1])
    f_keys = re.fullmatch(r"F(\d+)\s*[–-]\s*F(\d+)", token)
    if f_keys:
        return [f"F{i}" for i in range(int(f_keys.group(1)), int(f_keys.group(2)) + 1)]
    if re.fullmatch(r"[WASD ]{7}", token):
        return list("WASD")
    return []


def keys_of(key_string):
    """(keys, combinations) of one binding. "Left Ctrl + Q / W" is Ctrl+Q and Ctrl+W."""
    s = re.sub(r"\(.*?\)", " ", key_string)
    s = re.sub(r"→.*", " ", s)
    s = s.replace(", then ", " / ").replace(" or ", " / ").replace(", ", " / ")
    keys, combos, prefix = [], [], None
    for alternative in s.split(" / "):
        parts = [one_key(p) for p in alternative.split(" + ")]
        if len(parts) > 1 and all(parts):
            prefix = tuple(p[0] for p in parts[:-1])
            new = [prefix + (last,) for last in parts[-1]]
        elif len(parts) == 1 and prefix and re.fullmatch(r"\s*[A-Z0-9]\s*", alternative):
            new = [prefix + (parts[0][0],)]
        else:
            new = []
            for part in parts:
                keys += part
        for combo in new:
            combos.append(combo)
            keys += combo
    return keys, combos


def stick_side(button):
    """'L' or 'R' if the Xbox button cell is a stick click."""
    for part in re.split(r"\s*/\s*|\s+or\s+|,\s*", button):
        match = re.search(r"\b(LS|RS)\b\s*\((press|click)", part, re.I)
        if match:
            return "L" if match.group(1).upper() == "LS" else "R"
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--cache", default=os.path.join(tempfile.gettempdir(), "keymap-io-cache"))
    args = parser.parse_args()
    os.makedirs(args.cache, exist_ok=True)

    index = fetch(f"{SITE}/controls/", os.path.join(args.cache, "_index.html"))
    slugs = sorted(set(re.findall(r'href="/controls/([a-z0-9-]+)/"', index)))
    games = {}
    for slug in slugs:
        pc, pad = read_game(fetch(f"{SITE}/controls/{slug}/", os.path.join(args.cache, f"{slug}.html")))
        games[slug] = (pc, pad)
    counted = {s: g for s, g in games.items() if len(g[0]) >= MIN_BINDINGS and s not in EXCLUDE}
    total = len(counted)

    per_key = collections.defaultdict(lambda: collections.defaultdict(list))
    combo_games = collections.defaultdict(set)
    for slug, (pc, _) in counted.items():
        for action, key_string in pc:
            keys, combos = keys_of(key_string)
            for key in keys:
                per_key[key][slug].append(action)
            for combo in combos:
                combo_games[combo].add(slug)

    print(f"Source: {SITE}/controls/ ({len(slugs)} games listed, {total} counted)")
    print(f"Counted: {', '.join(sorted(counted))}\n")
    print("1. Games that bind each key by default\n")
    print(f"{'key':9s}{'games':>5s}{'share':>7s}  most common actions")
    for key in sorted(per_key, key=lambda k: (-len(per_key[k]), k)):
        actions = collections.Counter(re.split(r" \(| /| ·", a)[0].strip().lower()[:28]
                                      for acts in per_key[key].values() for a in acts)
        top = ", ".join(f"{a} x{c}" if c > 1 else a for a, c in actions.most_common(3))
        print(f"{key:9s}{len(per_key[key]):5d}{100 * len(per_key[key]) / total:6.0f}%  {top}")

    print("\n2. Bindings that are a combination of keys\n")
    first = collections.Counter()
    for combo, where in sorted(combo_games.items(), key=lambda item: (-len(item[1]), item[0])):
        first[combo[0]] += len(where)
        if len(where) > 1:
            print(f"   {' + '.join(combo):22s}{len(where)} games")
    single = sum(1 for where in combo_games.values() if len(where) == 1)
    print(f"   {single} more combinations appear in one game each")
    print("   first key of a combination, over all of them: "
          + ", ".join(f"{k} {c}" for k, c in first.most_common()))

    print("\n3. Controller stick clicks (Xbox column)\n")
    for side, name in (("L", "Left"), ("R", "Right")):
        rows = [(slug, action) for slug, (_, pad) in games.items()
                for action, button in pad if stick_side(button) == side]
        print(f"   {name} stick click: {len({slug for slug, _ in rows})} games")
        for slug, action in rows:
            print(f"      {slug:24s}{action[:60]}")
    interact = collections.Counter()
    for _, (_, pad) in games.items():
        for action, button in pad:
            if (re.search(r"\b(interact|use|pick up|loot)\b", action, re.I)
                    and not re.search(r"item|ability|skill|potion|heal|consum|stim|gadget|equipment", action, re.I)):
                button = re.sub(r"\(.*?\)", "", button).strip()
                interact["a face button" if button in ("A", "B", "X", "Y")
                         else "a stick click" if re.search(r"\b(LS|RS)\b", button) else "something else"] += 1
    print(f"\n   Interact or use is on: " + ", ".join(f"{k} {c}" for k, c in interact.most_common()))


if __name__ == "__main__":
    main()
