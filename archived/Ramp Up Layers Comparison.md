# Ramp Up Layers Comparison (After Sync and Rename)

This document compares the controller actions for Turning Ramp Up and (Gyro) Turning Ramp Up layers in both the Default and Alternative layouts.

**Last Updated:** After running `sync_turning_to_chorded.py` and `rename_chorded_to_gyro_ramp_up.py`

## Layer Names

| Old Name | New Name |
|----------|----------|
| Chorded Ramp Up 0 | (Gyro) Turning Ramp Up 0 |
| Chorded Ramp Up 1 | (Gyro) Turning Ramp Up 1 |

## Layout Context

| Layout | Trigger Buttons | Modifier Buttons | Gyro Trigger Layers |
|--------|-----------------|------------------|---------------------|
| **Default** | L2/R2 | L1/R1 | (Gyro) L2, (Gyro) R2 |
| **Alternative** | L1/R1 | L2/R2 | (Gyro) L1, (Gyro) R1 |

## Chord Activator Behavior

When the stick hits the edge while a trigger is held (chord):

| Layer Type | Chord Adds |
|------------|------------|
| Non-gyro trigger layer (L2/R2 in default, L1/R1 in alternative) | **Turning Ramp Up 0** |
| Gyro trigger layer ((Gyro) L2/(Gyro) R2 in default) | **(Gyro) Turning Ramp Up 0** |

---

# Default Layout

## Turning Ramp Up 0 (Default)

| Input | Group | Mode | Actions |
|-------|-------|------|---------|
| **L2 Full Pull** | 412 | trigger | **Empty** (trigger already held) |
| **R2 Full Pull** | 413 | trigger | **Empty** (trigger already held) |
| **L1** | 414 | switches | `remove Turning Ramp Up 0` → `remove Gyro Off` → `remove L2` → `remove (Gyro) L2` → `remove R2` → `remove (Gyro) R2` → `add L1: Modifier 0` |
| **R1** | 414 | switches | `remove Turning Ramp Up 0` → `remove Gyro Off` → `remove L2` → `remove (Gyro) L2` → `remove R2` → `remove (Gyro) R2` → `add R1: Modifier 1` |
| **Stick Edge (250ms)** | 423 | joystick | `add Turning Ramp Up 1` |
| **Stick Edge Release** | 423 | joystick | `remove Turning Ramp Up 0` → `remove Gyro Off` |
| **Gyro** | 554 | disabled | Disabled |

## Turning Ramp Up 1 (Default)

| Input | Group | Mode | Actions |
|-------|-------|------|---------|
| **L2 Full Pull** | 540 | trigger | **Empty** (trigger already held) |
| **R2 Full Pull** | 541 | trigger | **Empty** (trigger already held) |
| **L1** | 542 | switches | `remove Turning Ramp Up 1` → `remove Turning Ramp Up 0` → `remove Gyro Off` → `remove L2` → `remove (Gyro) L2` → `remove R2` → `remove (Gyro) R2` → `add L1: Modifier 0` |
| **R1** | 542 | switches | `remove Turning Ramp Up 1` → `remove Turning Ramp Up 0` → `remove Gyro Off` → `remove L2` → `remove (Gyro) L2` → `remove R2` → `remove (Gyro) R2` → `add R1: Modifier 1` |
| **Stick Edge Release** | 551 | joystick | `remove Turning Ramp Up 1` → `remove Turning Ramp Up 0` → `remove Gyro Off` |
| **Gyro** | 555 | disabled | Disabled |

## (Gyro) Turning Ramp Up 0 (Default) - formerly Chorded Ramp Up 0

| Input | Group | Mode | Actions |
|-------|-------|------|---------|
| **L2 Full Pull** | 643 | trigger | **Empty** (trigger already held) |
| **R2 Full Pull** | 644 | trigger | **Empty** (trigger already held) |
| **L1** | 645 | switches | `remove (Gyro) Turning Ramp Up 0` → `remove Gyro Off` → `remove L2` → `remove (Gyro) L2` → `remove R2` → `remove (Gyro) R2` → `add L1: Modifier 0` |
| **R1** | 645 | switches | `remove (Gyro) Turning Ramp Up 0` → `remove Gyro Off` → `remove L2` → `remove (Gyro) L2` → `remove R2` → `remove (Gyro) R2` → `add R1: Modifier 1` |
| **Stick Edge (250ms)** | 664 | joystick | `add (Gyro) Turning Ramp Up 1` |
| **Stick Edge Release** | 664 | joystick | `remove (Gyro) Turning Ramp Up 0` → `remove Gyro Off` |

## (Gyro) Turning Ramp Up 1 (Default) - formerly Chorded Ramp Up 1

| Input | Group | Mode | Actions |
|-------|-------|------|---------|
| **L2 Full Pull** | 965 | trigger | **Empty** (trigger already held) |
| **R2 Full Pull** | 966 | trigger | **Empty** (trigger already held) |
| **L1** | 967 | switches | `remove (Gyro) Turning Ramp Up 1` → `remove (Gyro) Turning Ramp Up 0` → `remove Gyro Off` → `remove L2` → `remove (Gyro) L2` → `remove R2` → `remove (Gyro) R2` → `add L1: Modifier 0` |
| **R1** | 967 | switches | `remove (Gyro) Turning Ramp Up 1` → `remove (Gyro) Turning Ramp Up 0` → `remove Gyro Off` → `remove L2` → `remove (Gyro) L2` → `remove R2` → `remove (Gyro) R2` → `add R1: Modifier 1` |
| **Stick Edge Release** | 976 | joystick | `remove (Gyro) Turning Ramp Up 1` → `remove (Gyro) Turning Ramp Up 0` → `remove Gyro Off` |

---

# Alternative Layout

## Turning Ramp Up 0 (Alternative)

| Input | Group | Mode | Actions |
|-------|-------|------|---------|
| **L2 Full Pull** | 412 | trigger | `remove Turning Ramp Up 0` → `remove Gyro Off` → `remove L1` → `remove (Gyro) L1` → `remove R1` → `remove (Gyro) R1` → `add L2: Modifier 0` |
| **R2 Full Pull** | 413 | trigger | `remove Turning Ramp Up 0` → `remove Gyro Off` → `remove L1` → `remove (Gyro) L1` → `remove R1` → `remove (Gyro) R1` → `add R2: Modifier 1` |
| **L1** | 414 | switches | **Empty** (trigger already held) |
| **R1** | 414 | switches | **Empty** (trigger already held) |
| **Stick Edge (250ms)** | 423 | joystick | `add Turning Ramp Up 1` |
| **Stick Edge Release** | 423 | joystick | `remove Turning Ramp Up 0` → `remove Gyro Off` |
| **Gyro** | 554 | disabled | Disabled |

## Turning Ramp Up 1 (Alternative)

| Input | Group | Mode | Actions |
|-------|-------|------|---------|
| **L2 Full Pull** | 540 | trigger | `remove Turning Ramp Up 1` → `remove Turning Ramp Up 0` → `remove Gyro Off` → `remove L1` → `remove (Gyro) L1` → `remove R1` → `remove (Gyro) R1` → `add L2: Modifier 0` |
| **R2 Full Pull** | 541 | trigger | `remove Turning Ramp Up 1` → `remove Turning Ramp Up 0` → `remove Gyro Off` → `remove L1` → `remove (Gyro) L1` → `remove R1` → `remove (Gyro) R1` → `add R2: Modifier 1` |
| **L1** | 542 | switches | **Empty** (trigger already held) |
| **R1** | 542 | switches | **Empty** (trigger already held) |
| **Stick Edge Release** | 551 | joystick | `remove Turning Ramp Up 1` → `remove Turning Ramp Up 0` → `remove Gyro Off` |
| **Gyro** | 555 | disabled | Disabled |

## (Gyro) Turning Ramp Up 0 (Alternative) - formerly Chorded Ramp Up 0

| Input | Group | Mode | Actions |
|-------|-------|------|---------|
| **L2 Full Pull** | 643 | trigger | `remove (Gyro) Turning Ramp Up 0` → `remove Gyro Off` → `remove L1` → `remove (Gyro) L1` → `remove R1` → `remove (Gyro) R1` → `add L2: Modifier 0` |
| **R2 Full Pull** | 644 | trigger | `remove (Gyro) Turning Ramp Up 0` → `remove Gyro Off` → `remove L1` → `remove (Gyro) L1` → `remove R1` → `remove (Gyro) R1` → `add R2: Modifier 1` |
| **L1** | 645 | switches | **Empty** (trigger already held) |
| **R1** | 645 | switches | **Empty** (trigger already held) |
| **Stick Edge (250ms)** | 664 | joystick | `add (Gyro) Turning Ramp Up 1` |
| **Stick Edge Release** | 664 | joystick | `remove (Gyro) Turning Ramp Up 0` → `remove Gyro Off` |

## (Gyro) Turning Ramp Up 1 (Alternative) - formerly Chorded Ramp Up 1

| Input | Group | Mode | Actions |
|-------|-------|------|---------|
| **L2 Full Pull** | 965 | trigger | `remove (Gyro) Turning Ramp Up 1` → `remove (Gyro) Turning Ramp Up 0` → `remove Gyro Off` → `remove L1` → `remove (Gyro) L1` → `remove R1` → `remove (Gyro) R1` → `add L2: Modifier 0` |
| **R2 Full Pull** | 966 | trigger | `remove (Gyro) Turning Ramp Up 1` → `remove (Gyro) Turning Ramp Up 0` → `remove Gyro Off` → `remove L1` → `remove (Gyro) L1` → `remove R1` → `remove (Gyro) R1` → `add R2: Modifier 1` |
| **L1** | 967 | switches | **Empty** (trigger already held) |
| **R1** | 967 | switches | **Empty** (trigger already held) |
| **Stick Edge Release** | 976 | joystick | `remove (Gyro) Turning Ramp Up 1` → `remove (Gyro) Turning Ramp Up 0` → `remove Gyro Off` |

---

# How Ramp Up Layers Are Activated

## From Base Layer (no trigger held)
- Stick edge → **Turning Ramp Up 0**
- Stick edge (250ms) → **Turning Ramp Up 1**

## From Non-Gyro Trigger Layer (L2/R2 in default, L1/R1 in alternative)
- Stick edge + chord → **Turning Ramp Up 0**
- Stick edge + chord (250ms) → **Turning Ramp Up 1**

## From Gyro Trigger Layer ((Gyro) L2/(Gyro) R2 in default)
- Stick edge + chord → **(Gyro) Turning Ramp Up 0**
- Stick edge + chord (250ms) → **(Gyro) Turning Ramp Up 1**

---

# Summary

| Layer | Purpose |
|-------|---------|
| **Turning Ramp Up 0/1** | Speed boost when stick at edge (no gyro context) |
| **(Gyro) Turning Ramp Up 0/1** | Speed boost when stick at edge (gyro trigger context) |

Both layer types now have identical action patterns - the only difference is which context they're activated from and their names.
