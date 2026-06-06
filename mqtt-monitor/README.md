# MQTT Monitor

Simple MQTT monitor website.


## WebSocket access from outside the Docker network

```
Browser ──    HTTP   ──►   nginx:80/*  ──► static files
        ── WebSocket ──► nginx:80/mqtt ──► broker:9001 (ws proxy)
```

- traffic pointed directly at the server is given access to the static web app
- traffic pointed at `/mqtt` is proxied to the broker via WebSocket (via HTTP/1.1 protocol switching)
