scratch:

remove LST layer:
```json
"release": {
    "bindings": {
        "binding": [
            "controller_action remove_layer 10 0 0, , ",
            "controller_action remove_layer 73 0 0, , ",
            "controller_action remove_layer 78 0 0, , ",
            "controller_action add_layer 75 0 0, , "
        ]
    },
    "settings": {
        "haptic_intensity": "0"
    }
}
```
remove RST layer:
```json
"release": {
    "bindings": {
        "binding": [
            "controller_action remove_layer 9 0 0, , ",
            "controller_action remove_layer 71 0 0, , ",
            "controller_action remove_layer 77 0 0, , ",
            "controller_action add_layer 75 0 0, , "
        ]
    },
    "settings": {
        "haptic_intensity": "0"
    }
}
```

Modifier 2 Bumpers:
```json
"left_bumper": {
    "activators": {
        "release": {
            "bindings": {
                "binding": [
                    "controller_action CHANGE_PRESET 2 1 1, , ", // switch to gyro
                    "controller_action remove_layer 7 0 0, , ", // "L1: Modifier 0"
                    "controller_action remove_layer 8 0 0, , ", // "R1: Modifier 1"
                    "controller_action remove_layer 69 0 0, , ", // "L1: Tap Cover"
                    "controller_action remove_layer 70 0 0, , ", // "R1: Tap Cover"
                    "controller_action remove_layer 75 0 0, , ", // "L1&R1: Tap Cover"
                    "controller_action remove_layer 56 0 0, , ", // "L1!R1: Modifier 2"
                    "controller_action remove_layer 57 0 0, , " // "R1!L1: Modifier 2"
                ]
            },
            "settings": {
                "haptic_intensity": "0"
            }
        },
        "chord": {
            "bindings": {
                "binding": "controller_action add_layer 75 0 0, , "
            },
            "settings": {
                "chord_button": "1",
                "haptic_intensity": "3",
                "delay_start": "200",
                "interruptable": "0"
            }
        }
    },
    "disabled_activators": {}
},
"right_bumper": {
    "activators": {
        "release": {
                "bindings": {
                    "binding": [
                        "controller_action CHANGE_PRESET 2 1 1, , ", // switch to gyro
                        "controller_action remove_layer 7 0 0, , ", // "L1: Modifier 0"
                        "controller_action remove_layer 8 0 0, , ", // "R1: Modifier 1"
                        "controller_action remove_layer 69 0 0, , ", // "L1: Tap Cover"
                        "controller_action remove_layer 70 0 0, , ", // "R1: Tap Cover"
                        "controller_action remove_layer 75 0 0, , ", // "L1&R1: Tap Cover"
                        "controller_action remove_layer 56 0 0, , ", // "L1!R1: Modifier 2"
                        "controller_action remove_layer 57 0 0, , " // "R1!L1: Modifier 2"
                    ]
                },
            "settings": {
                "haptic_intensity": "0"
            }
        },
        "chord": {
            "bindings": {
                "binding": "controller_action add_layer 75 0 0, , "
            },
            "settings": {
                "chord_button": "2",
                "haptic_intensity": "3",
                "delay_start": "200",
                "interruptable": "0"
            }
        }
    },
    "disabled_activators": {}
}
```

Fn layer clean up functions:

```json
"activators": {
    "chord": [
        {
            "bindings": {
                "binding": "controller_action empty_binding, , "
            },
            "settings": {
                "chord_button": "15",
                "interruptable": "0"
            }
        },
        {
            "bindings": {
                "binding": "controller_action empty_binding, , "
            },
            "settings": {
                "chord_button": "14",
                "interruptable": "0"
            }
        }
    ],
    "Full_Press": {
        "bindings": {
            "binding": [
                "controller_action remove_layer 60 0 0, , ",
                "controller_action remove_layer 83 0 0, , "
            ]
        },
        "settings": {
            "hold_repeats": "1"
        }
    }
},
"disabled_activators": {}
```