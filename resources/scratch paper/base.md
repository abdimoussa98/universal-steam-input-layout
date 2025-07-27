scratch:

remove LST layer:
```json
"release": {
    "bindings": {
        "binding": [
            "controller_action remove_layer 10 0 0, , ",
            "controller_action remove_layer 73 0 0, , ",
            "controller_action remove_layer 78 0 0, , "
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
            "controller_action remove_layer 77 0 0, , "
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
                "binding": "controller_action CHANGE_PRESET 2 1 1, , "
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
                "binding": "controller_action CHANGE_PRESET 2 1 1, , "
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
},
```
