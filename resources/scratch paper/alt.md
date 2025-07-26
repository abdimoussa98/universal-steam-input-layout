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