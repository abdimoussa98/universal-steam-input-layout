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