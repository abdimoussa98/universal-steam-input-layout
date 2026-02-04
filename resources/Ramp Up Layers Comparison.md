# Ramp Up Layers Comparison (After Sync)

This document compares the controller actions for Turning Ramp Up and Chorded Ramp Up layers in both the Default and Alternative layouts.

**Last Updated:** After running `sync_turning_to_chorded.py`

## Layout Context

| Layout | Trigger Buttons | Modifier Buttons | Chorded Activation |
|--------|-----------------|------------------|-------------------|
| **Default** | L2/R2 | L1/R1 | When L2/R2 full pull held |
| **Alternative** | L1/R1 | L2/R2 | When L1/R1 held |

---

# Default Layout

## Turning Ramp Up 0 (Default) - SYNCED

| Input | Group | Mode | Actions |
|-------|-------|------|---------|
| **L2 Full Pull** | 412 | trigger | **Empty** (trigger already held) |
| **R2 Full Pull** | 413 | trigger | **Empty** (trigger already held) |
| **L1** | 414 | switches | `remove Turning Ramp Up 0` → `remove Gyro Off` → `remove L2` → `remove (Gyro) L2` → `remove R2` → `remove (Gyro) R2` → `add L1: Modifier 0` |
| **R1** | 414 | switches | `remove Turning Ramp Up 0` → `remove Gyro Off` → `remove L2` → `remove (Gyro) L2` → `remove R2` → `remove (Gyro) R2` → `add R1: Modifier 1` |
| **Stick Edge (250ms)** | 423 | joystick | `add Turning Ramp Up 1` |
| **Stick Edge Release** | 423 | joystick | `remove Turning Ramp Up 0` → `remove Gyro Off` |
| **Gyro** | 554 | disabled | Disabled |

## Turning Ramp Up 1 (Default) - SYNCED

| Input | Group | Mode | Actions |
|-------|-------|------|---------|
| **L2 Full Pull** | 540 | trigger | **Empty** (trigger already held) |
| **R2 Full Pull** | 541 | trigger | **Empty** (trigger already held) |
| **L1** | 542 | switches | `remove Turning Ramp Up 1` → `remove Turning Ramp Up 0` → `remove Gyro Off` → `remove L2` → `remove (Gyro) L2` → `remove R2` → `remove (Gyro) R2` → `add L1: Modifier 0` |
| **R1** | 542 | switches | `remove Turning Ramp Up 1` → `remove Turning Ramp Up 0` → `remove Gyro Off` → `remove L2` → `remove (Gyro) L2` → `remove R2` → `remove (Gyro) R2` → `add R1: Modifier 1` |
| **Stick Edge Release** | 551 | joystick | `remove Turning Ramp Up 1` → `remove Turning Ramp Up 0` → `remove Gyro Off` |
| **Gyro** | 555 | disabled | Disabled |

## Chorded Ramp Up 0 (Default) - GOLD STANDARD

| Input | Group | Mode | Actions |
|-------|-------|------|---------|
| **L2 Full Pull** | 643 | trigger | **Empty** (trigger already held) |
| **R2 Full Pull** | 644 | trigger | **Empty** (trigger already held) |
| **L1** | 645 | switches | `remove Chorded Ramp Up 0` → `remove Gyro Off` → `remove L2` → `remove (Gyro) L2` → `remove R2` → `remove (Gyro) R2` → `add L1: Modifier 0` |
| **R1** | 645 | switches | `remove Chorded Ramp Up 0` → `remove Gyro Off` → `remove L2` → `remove (Gyro) L2` → `remove R2` → `remove (Gyro) R2` → `add R1: Modifier 1` |
| **Stick Edge (250ms)** | 664 | joystick | `add Chorded Ramp Up 1` |
| **Stick Edge Release** | 664 | joystick | `remove Chorded Ramp Up 0` → `remove Gyro Off` |

## Chorded Ramp Up 1 (Default) - GOLD STANDARD

| Input | Group | Mode | Actions |
|-------|-------|------|---------|
| **L2 Full Pull** | 965 | trigger | **Empty** (trigger already held) |
| **R2 Full Pull** | 966 | trigger | **Empty** (trigger already held) |
| **L1** | 967 | switches | `remove Chorded Ramp Up 1` → `remove Chorded Ramp Up 0` → `remove Gyro Off` → `remove L2` → `remove (Gyro) L2` → `remove R2` → `remove (Gyro) R2` → `add L1: Modifier 0` |
| **R1** | 967 | switches | `remove Chorded Ramp Up 1` → `remove Chorded Ramp Up 0` → `remove Gyro Off` → `remove L2` → `remove (Gyro) L2` → `remove R2` → `remove (Gyro) R2` → `add R1: Modifier 1` |
| **Stick Edge Release** | 976 | joystick | `remove Chorded Ramp Up 1` → `remove Chorded Ramp Up 0` → `remove Gyro Off` |

---

# Alternative Layout

## Turning Ramp Up 0 (Alternative) - SYNCED

| Input | Group | Mode | Actions |
|-------|-------|------|---------|
| **L2 Full Pull** | 412 | trigger | `remove Turning Ramp Up 0` → `remove Gyro Off` → `remove L1` → `remove (Gyro) L1` → `remove R1` → `remove (Gyro) R1` → `add L2: Modifier 0` |
| **R2 Full Pull** | 413 | trigger | `remove Turning Ramp Up 0` → `remove Gyro Off` → `remove L1` → `remove (Gyro) L1` → `remove R1` → `remove (Gyro) R1` → `add R2: Modifier 1` |
| **L1** | 414 | switches | **Empty** (trigger already held) |
| **R1** | 414 | switches | **Empty** (trigger already held) |
| **Stick Edge (250ms)** | 423 | joystick | `add Turning Ramp Up 1` |
| **Stick Edge Release** | 423 | joystick | `remove Turning Ramp Up 0` → `remove Gyro Off` |
| **Gyro** | 554 | disabled | Disabled |

## Turning Ramp Up 1 (Alternative) - SYNCED

| Input | Group | Mode | Actions |
|-------|-------|------|---------|
| **L2 Full Pull** | 540 | trigger | `remove Turning Ramp Up 1` → `remove Turning Ramp Up 0` → `remove Gyro Off` → `remove L1` → `remove (Gyro) L1` → `remove R1` → `remove (Gyro) R1` → `add L2: Modifier 0` |
| **R2 Full Pull** | 541 | trigger | `remove Turning Ramp Up 1` → `remove Turning Ramp Up 0` → `remove Gyro Off` → `remove L1` → `remove (Gyro) L1` → `remove R1` → `remove (Gyro) R1` → `add R2: Modifier 1` |
| **L1** | 542 | switches | **Empty** (trigger already held) |
| **R1** | 542 | switches | **Empty** (trigger already held) |
| **Stick Edge Release** | 551 | joystick | `remove Turning Ramp Up 1` → `remove Turning Ramp Up 0` → `remove Gyro Off` |
| **Gyro** | 555 | disabled | Disabled |

## Chorded Ramp Up 0 (Alternative) - GOLD STANDARD

| Input | Group | Mode | Actions |
|-------|-------|------|---------|
| **L2 Full Pull** | 643 | trigger | `remove Chorded Ramp Up 0` → `remove Gyro Off` → `remove L1` → `remove (Gyro) L1` → `remove R1` → `remove (Gyro) R1` → `add L2: Modifier 0` |
| **R2 Full Pull** | 644 | trigger | `remove Chorded Ramp Up 0` → `remove Gyro Off` → `remove L1` → `remove (Gyro) L1` → `remove R1` → `remove (Gyro) R1` → `add R2: Modifier 1` |
| **L1** | 645 | switches | **Empty** (trigger already held) |
| **R1** | 645 | switches | **Empty** (trigger already held) |
| **Stick Edge (250ms)** | 664 | joystick | `add Chorded Ramp Up 1` |
| **Stick Edge Release** | 664 | joystick | `remove Chorded Ramp Up 0` → `remove Gyro Off` |

## Chorded Ramp Up 1 (Alternative) - GOLD STANDARD

| Input | Group | Mode | Actions |
|-------|-------|------|---------|
| **L2 Full Pull** | 965 | trigger | `remove Chorded Ramp Up 1` → `remove Chorded Ramp Up 0` → `remove Gyro Off` → `remove L1` → `remove (Gyro) L1` → `remove R1` → `remove (Gyro) R1` → `add L2: Modifier 0` |
| **R2 Full Pull** | 966 | trigger | `remove Chorded Ramp Up 1` → `remove Chorded Ramp Up 0` → `remove Gyro Off` → `remove L1` → `remove (Gyro) L1` → `remove R1` → `remove (Gyro) R1` → `add R2: Modifier 1` |
| **L1** | 967 | switches | **Empty** (trigger already held) |
| **R1** | 967 | switches | **Empty** (trigger already held) |
| **Stick Edge Release** | 976 | joystick | `remove Chorded Ramp Up 1` → `remove Chorded Ramp Up 0` → `remove Gyro Off` |

---

# Sync Status Summary

All Turning Ramp Up layers now match the Chorded Ramp Up pattern:

| Layer | Default Layout | Alternative Layout |
|-------|---------------|-------------------|
| Turning Ramp Up 0 | SYNCED | SYNCED |
| Turning Ramp Up 1 | SYNCED | SYNCED |
| Chorded Ramp Up 0 | GOLD STANDARD | GOLD STANDARD |
| Chorded Ramp Up 1 | GOLD STANDARD | GOLD STANDARD |

## Pattern Summary

For both Turning and Chorded Ramp Up layers:

1. **Trigger inputs** (the buttons that activate Chorded mode) are **Empty**
2. **Modifier inputs** clean up:
   - The ramp up layer(s)
   - Gyro Off layer
   - Both trigger layers and their Gyro variants
   - Then add the modifier layer
3. **Stick Edge Release** removes ramp up layers and Gyro Off
