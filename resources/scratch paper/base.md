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