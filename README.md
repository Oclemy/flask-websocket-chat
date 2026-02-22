# flask-websocket-chat
Real-time multi-user chat app. Open multiple tabs to see messages broadcast instantly.

## requirements.txt

```
flask
flask-sock
gunicorn
```

## Deployment

Railway deploy note: For your Procfile (or Railway start command), use:

```
gunicorn --worker-class=gevent app:app
```
