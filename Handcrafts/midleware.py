import re
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import AnonymousUser
from accounts.models import User
from channels.middleware import BaseMiddleware

@database_sync_to_async
def get_user_from_token(token_key):
    try:
        token = AccessToken(token_key)
        user = User.objects.get(id=token['user_id'])
        return user
    except Exception as e:
        print(f"Error retrieving user from token: {e}")
        return AnonymousUser()

class TokenAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        try:
            auth_header = dict(scope['headers'])[b'authorization'].decode('utf-8')
            token_match = re.match(r'Bearer (.+)', auth_header)
            if token_match:
                token_key = token_match.group(1)
                scope['user'] = await get_user_from_token(token_key)
            else:
                scope['user'] = AnonymousUser()
        except (KeyError, IndexError, ValueError):
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)