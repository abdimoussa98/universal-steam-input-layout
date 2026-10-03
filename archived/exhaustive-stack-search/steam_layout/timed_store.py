"""Durable breadth-first states and replay witnesses for timed layer search.

The search supplies states with normalized clocks. This module preserves every
field of those states and binds the database to the search's complete identity.
An expansion and all of its newly discovered states commit together.
"""
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sqlite3

from .timed_model import Activation, Shift, TimedState


FORMAT_VERSION = 2


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _integer(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _control(value):
    if (not isinstance(value, (list, tuple)) or len(value) != 2 or
            not all(isinstance(part, str) and part for part in value)):
        raise ValueError("a control must contain two nonempty strings")
    return tuple(value)


def _fields(value, names, context):
    if not isinstance(value, dict) or set(value) != set(names):
        raise ValueError(f"invalid {context} fields")


def _decimal(value):
    if not isinstance(value, (str, Decimal)):
        raise ValueError("analog values must be decimal strings")
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise ValueError("invalid analog value") from None
    if not result.is_finite() or not 0 <= result <= 32767:
        raise ValueError("analog values must be finite and between 0 and 32767")
    # Decimal.normalize() rounds under the ambient decimal context. Formatting
    # and trimming zeros instead preserves arbitrary precision exactly.
    if not result:
        return "0"
    formatted = format(result, "f")
    return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted


def encode_state(state):
    """Return canonical JSON, including exact decimal analog magnitudes."""
    if not isinstance(state, TimedState):
        raise ValueError("expected a TimedState")
    payload = {
        "now_ms": state.now_ms,
        "stack": list(state.stack),
        "held": [list(c) for c in sorted(state.held)],
        "analog_values": [[list(c), _decimal(v)] for c, v in state.analog_values],
        "activations": [{"entry_id": a.entry_id, "deadline_ms": a.deadline_ms,
                         "stage": a.stage, "fired": a.fired} for a in state.activations],
        "shifts": [{"control": list(s.control), "source": s.source,
                    "group": s.group, "entry_id": s.entry_id} for s in state.shifts],
    }
    # Apply the same validation to writes and reads, rather than storing states
    # which can only fail when a saved search is resumed.
    decode_state(payload)
    return _json(payload)


def decode_state(payload):
    """Restore a state; reject malformed or incompatible state records."""
    if isinstance(payload, str):
        payload = json.loads(payload)
    _fields(payload, ("now_ms", "stack", "held", "analog_values", "activations", "shifts"),
            "timed state")
    now_ms = _integer(payload["now_ms"], "now_ms")
    for name in ("stack", "held", "analog_values", "activations", "shifts"):
        if not isinstance(payload[name], list):
            raise ValueError(f"{name} must be a list")
    stack = tuple(_integer(layer, "layer") for layer in payload["stack"])
    if not stack or stack[0] != 0 or len(set(stack)) != len(stack):
        raise ValueError("stack must start with Base and contain distinct layers")
    held = tuple(_control(c) for c in payload["held"])
    if len(set(held)) != len(held):
        raise ValueError("held controls must be distinct")
    analog = []
    for item in payload["analog_values"]:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError("invalid analog value pair")
        analog.append((_control(item[0]), Decimal(_decimal(item[1]))))
    if len({c for c, _ in analog}) != len(analog):
        raise ValueError("analog controls must be distinct")
    activations = []
    for item in payload["activations"]:
        _fields(item, ("entry_id", "deadline_ms", "stage", "fired"), "activation")
        if not isinstance(item["entry_id"], str) or not item["entry_id"]:
            raise ValueError("activation entry_id must be a nonempty string")
        if item["deadline_ms"] is not None:
            _integer(item["deadline_ms"], "deadline_ms", now_ms)
        if item["stage"] not in ("start", "repeat", "done"):
            raise ValueError("invalid activation stage")
        if not isinstance(item["fired"], bool):
            raise ValueError("activation fired must be a boolean")
        activations.append(Activation(**item))
    if len({a.entry_id for a in activations}) != len(activations):
        raise ValueError("activation entries must be distinct")
    shifts = []
    for item in payload["shifts"]:
        _fields(item, ("control", "source", "group", "entry_id"), "shift")
        if any(not isinstance(item[key], str) or not item[key]
               for key in ("source", "group", "entry_id")):
            raise ValueError("shift source, group and entry_id must be nonempty strings")
        shifts.append(Shift(_control(item["control"]), item["source"], item["group"], item["entry_id"]))
    return TimedState(now_ms, stack, frozenset(held), tuple(analog), tuple(activations), tuple(shifts))


class TimedStore:
    """A resumable FIFO search frontier with atomic, bounded expansions.

    ``identity`` must include everything determining the runtime and its event
    alphabet; exact canonical JSON equality is required to resume. New stores
    only accept missing files or zero-byte files. They never replace a database.
    """

    def __init__(self, path, model, identity, resume=False):
        if not isinstance(identity, dict):
            raise ValueError("search identity must be a dictionary")
        self.identity = json.loads(_json(identity))
        identity_json = _json(self.identity)
        self.database_path = Path(path)
        self.model = model
        self._connection = None
        if resume:
            if not self.database_path.is_file() or not self.database_path.stat().st_size:
                raise ValueError("cannot resume: timed search database does not exist or is empty")
        else:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation closes the gap between checking and opening a
            # new file; an existing zero-byte file (e.g. mkstemp) is also safe.
            try:
                with self.database_path.open("xb"):
                    pass
            except FileExistsError:
                if not self.database_path.is_file() or self.database_path.stat().st_size:
                    raise ValueError("timed search database already exists; use resume") from None
        connection = sqlite3.connect(self.database_path.resolve().as_uri() + "?mode=rw", uri=True,
                                     isolation_level=None)
        self._connection = connection
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            if resume:
                self._check_identity(identity_json)
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")
            if not resume:
                with self._transaction():
                    connection.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                    connection.execute("""CREATE TABLE states (
                        id INTEGER PRIMARY KEY,
                        state TEXT NOT NULL UNIQUE,
                        parent INTEGER REFERENCES states(id),
                        event TEXT,
                        expanded INTEGER NOT NULL DEFAULT 0 CHECK (expanded IN (0, 1)),
                        CHECK ((parent IS NULL) = (event IS NULL)))""")
                    connection.execute("CREATE INDEX frontier ON states(id) WHERE expanded = 0")
                    connection.executemany("INSERT INTO metadata(key, value) VALUES (?, ?)",
                                           (("format", str(FORMAT_VERSION)), ("identity", identity_json),
                                            ("seeded", "false"), ("count", "0"),
                                            ("expanded_count", "0")))
                    # These counters change in the same transaction as states.
                    # Repeated budget/progress checks must not scan the growing
                    # state table on every expansion.
                    connection.execute("""CREATE TRIGGER state_inserted AFTER INSERT ON states
                        BEGIN
                          UPDATE metadata SET value = value + 1 WHERE key = 'count';
                          UPDATE metadata SET value = value + NEW.expanded WHERE key = 'expanded_count';
                        END""")
                    connection.execute("""CREATE TRIGGER state_expanded AFTER UPDATE OF expanded ON states
                        BEGIN
                          UPDATE metadata SET value = value + NEW.expanded - OLD.expanded
                            WHERE key = 'expanded_count';
                        END""")
                    connection.execute("""CREATE TRIGGER state_deleted AFTER DELETE ON states
                        BEGIN
                          UPDATE metadata SET value = value - 1 WHERE key = 'count';
                          UPDATE metadata SET value = value - OLD.expanded WHERE key = 'expanded_count';
                        END""")
        except BaseException:
            self.close()
            raise

    def _check_identity(self, expected):
        try:
            metadata = dict(self._connection.execute("SELECT key, value FROM metadata"))
        except sqlite3.DatabaseError as exc:
            raise ValueError("not a timed search database") from exc
        if metadata.get("format") != str(FORMAT_VERSION):
            raise ValueError("incompatible timed search database format")
        if metadata.get("identity") != expected:
            raise ValueError("timed search identity mismatch: model, layout or options changed")
        if metadata.get("seeded") not in ("true", "false"):
            raise ValueError("invalid timed search initialization metadata")
        try:
            counts = tuple(int(metadata[key]) for key in ("count", "expanded_count"))
        except (KeyError, ValueError):
            raise ValueError("invalid timed search count metadata") from None
        # A single scan on resume validates persisted counters. The running
        # search uses only the constant-size metadata table thereafter.
        actual = self._connection.execute("SELECT COUNT(*), COALESCE(SUM(expanded), 0) FROM states").fetchone()
        if counts != actual:
            raise ValueError("timed search state counts do not match database contents")

    @contextmanager
    def _transaction(self):
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            yield
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise

    def close(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @property
    def count(self):
        return int(self._connection.execute("SELECT value FROM metadata WHERE key = 'count'").fetchone()[0])

    @property
    def expanded_count(self):
        return int(self._connection.execute("SELECT value FROM metadata WHERE key = 'expanded_count'").fetchone()[0])

    @property
    def seeded(self):
        return self._connection.execute("SELECT value FROM metadata WHERE key = 'seeded'").fetchone()[0] == "true"

    @property
    def complete(self):
        return self.seeded and self.pending() is None

    def _insert(self, payload, parent, event):
        row = self._connection.execute("SELECT id FROM states WHERE state = ?", (payload,)).fetchone()
        if row is not None:
            return row[0], False
        cursor = self._connection.execute("INSERT INTO states(state, parent, event) VALUES (?, ?, ?)",
                                          (payload, parent, event))
        return cursor.lastrowid, True

    @staticmethod
    def _event(event):
        if not isinstance(event, dict):
            raise ValueError("a witness event must be a dictionary")
        return _json(event)

    def _require_id(self, state_id):
        _integer(state_id, "state id", 1)
        row = self._connection.execute("SELECT expanded FROM states WHERE id = ?", (state_id,)).fetchone()
        if row is None:
            raise KeyError(f"unknown timed state {state_id}")
        return row[0]

    def add(self, state, parent=None, event=None):
        """Insert one state; duplicates retain their first, shortest witness."""
        payload = encode_state(state)
        if (parent is None) != (event is None):
            raise ValueError("a state must have both a parent and an event, or neither")
        event_json = None if event is None else self._event(event)
        with self._transaction():
            if parent is not None:
                self._require_id(parent)
            return self._insert(payload, parent, event_json)

    def seed(self, states):
        """Atomically insert every initial state and mark initialization done."""
        payloads = [encode_state(state) for state in states]
        with self._transaction():
            if self.seeded:
                raise ValueError("timed search roots have already been seeded")
            ids = [self._insert(payload, None, None)[0] for payload in payloads]
            self._connection.execute("UPDATE metadata SET value = 'true' WHERE key = 'seeded'")
        return ids

    def mark_seeded(self):
        """Declare roots complete after callers using ``add`` have added them."""
        with self._transaction():
            self._connection.execute("UPDATE metadata SET value = 'true' WHERE key = 'seeded'")

    def pending(self):
        row = self._connection.execute("SELECT id, state FROM states WHERE expanded = 0 ORDER BY id LIMIT 1").fetchone()
        return None if row is None else (row[0], decode_state(row[1]))

    def commit_expansion(self, state_id, successors, max_states=None):
        """Commit every unique successor and the expansion, or change nothing.

        Return false if the total state budget would be exceeded. Such a parent
        remains pending, so raising the budget and resuming cannot lose edges.
        Already expanded parents are harmless to retry and return true.
        """
        if max_states is not None:
            _integer(max_states, "max_states")
        payloads = {}
        for state, event in successors:
            payloads.setdefault(encode_state(state), self._event(event))
        with self._transaction():
            if self._require_id(state_id):
                return True
            newcomers = [(payload, event) for payload, event in payloads.items()
                         if self._connection.execute("SELECT id FROM states WHERE state = ?", (payload,)).fetchone() is None]
            if max_states is not None and self.count + len(newcomers) > max_states:
                return False
            self._connection.executemany("INSERT INTO states(state, parent, event) VALUES (?, ?, ?)",
                                          ((payload, state_id, event) for payload, event in newcomers))
            self._connection.execute("UPDATE states SET expanded = 1 WHERE id = ?", (state_id,))
        return True

    def iter_states(self):
        for state_id, payload in self._connection.execute("SELECT id, state FROM states ORDER BY id"):
            yield state_id, decode_state(payload)

    def get(self, state_id):
        _integer(state_id, "state id", 1)
        row = self._connection.execute("SELECT state FROM states WHERE id = ?", (state_id,)).fetchone()
        if row is None:
            raise KeyError(f"unknown timed state {state_id}")
        return decode_state(row[0])

    def trace(self, state_id):
        """Return the parent-chain physical events, in replay order."""
        return [event for _, _, event in self.path(state_id) if event is not None]

    def path(self, state_id):
        """Return (id, state, incoming event) records from root to destination."""
        _integer(state_id, "state id", 1)
        result = []
        while True:
            row = self._connection.execute("SELECT parent, event, state FROM states WHERE id = ?", (state_id,)).fetchone()
            if row is None:
                raise KeyError(f"unknown timed state {state_id}")
            parent, event, payload = row
            result.append((state_id, decode_state(payload), None if event is None else json.loads(event)))
            if parent is None:
                return list(reversed(result))
            if parent >= state_id:
                raise ValueError("invalid timed search witness parent chain")
            state_id = parent
