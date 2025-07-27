remove LST layer:
```json
"release": {
    "bindings": {
        "binding": [
        "controller_action remove_layer 18 0 0, , ",
        "controller_action remove_layer 37 0 0, , ",
        "controller_action remove_layer 80 0 0, , "
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
            "controller_action remove_layer 17 0 0, , ",
            "controller_action remove_layer 36 0 0, , ",
            "controller_action remove_layer 79 0 0, , "
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
                "binding": "controller_action CHANGE_PRESET 1 1 1, , "
            },
            "settings": {
                "haptic_intensity": "0"
            }
        },
        "chord": {
            "bindings": {
                "binding": "controller_action add_layer 76 0 0, , "
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
                "binding": "controller_action CHANGE_PRESET 1 1 1, , "
            },
            "settings": {
                "haptic_intensity": "0"
            }
        },
        "chord": {
            "bindings": {
                "binding": "controller_action add_layer 76 0 0, , "
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
