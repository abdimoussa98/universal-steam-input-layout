scratch:

remove LST layer:
```json
"release": {
    "bindings": {
        "binding": [
            "controller_action remove_layer 24 0 0, , ",
            "controller_action remove_layer 74 0 0, , ",
            "controller_action remove_layer 82 0 0, , "
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
            "controller_action remove_layer 23 0 0, , ",
            "controller_action remove_layer 72 0 0, , ",
            "controller_action remove_layer 81 0 0, , "
        ]
    },
    "settings": {
        "haptic_intensity": "0"
    }
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
                "controller_action remove_layer 62 0 0, , ",
                "controller_action remove_layer 85 0 0, , "
            ]
        },
        "settings": {
            "hold_repeats": "1"
        }
    }
},
"disabled_activators": {}
```