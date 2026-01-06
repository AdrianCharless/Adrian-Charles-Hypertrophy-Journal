import os
from flask import request, Response

def require_password():
    """
    HTTP Basic Auth.
    Set env vars:
      - APP_USERNAME (optional; default 'user')
      - APP_PASSWORD (required to enable protection)
    """
    password = os.getenv("APP_PASSWORD")
    if not password:
        return None  # if no password set, don't protect (useful for local dev)

    username = os.getenv("APP_USERNAME", "user")

    auth = request.authorization
    if not auth or auth.username != username or auth.password != password:
        return Response(
            "Unauthorized", 401,
            {"WWW-Authenticate": 'Basic realm="Gym Journal"'}
        )
    return None
