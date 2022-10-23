import asyncpg
import logging
from aiohttp import web
from utils import generate_response
from db_wrapper import DbWrapper

async def is_token_valid(user_id, token_to_compare, connection_pool: asyncpg.Pool):
    token_from_db = await DbWrapper.get_token(user_id)
    tkn = token_from_db['tkn']
    return token_to_compare == tkn

# define endpoints that can be used only by app or only by ust tokens exclusively
endpoints = {'app': ['/sign_up', '/sign_in'], 'ust': ['/unsign_from_session', '/sign_up_for_session'], 'adm': []}

# define endpoints that can be used by both of the tokens
routes_both_tokens = ['/sessions', '/instructors', '/sessions_by_uid']

# make sure that adm tokens can access all the endpoints
endpoints['adm'].extend(endpoints['app'])
endpoints['adm'].extend(endpoints['ust'])
endpoints['adm'].extend(routes_both_tokens)

# add tokens that both types of ust and app can use to their respective fields in the dictionary
for route in routes_both_tokens:
    endpoints['app'].append(route)
    endpoints['ust'].append(route)



@web.middleware
async def validation_middleware(request: web.Request, handler):
    # this is done so that we can properly handle cases, when someone calls the wrong endpoint
    # as the only other way to do that is through calling a handler, and that would mean that sometimes there
    # will be unnecessary calls to the database
    routes = [route.resource.canonical for route in request.app.router.routes()]
    request_path = request.path

    if request_path not in routes:
        return web.Response(body='404 Not Found', status=404)

    if request_path == '/ping':
        return await handler(request)

    headers = request.headers
    received_token: str = headers.get('X-Token')
    token_type = received_token.split('-')[0]
    if request_path not in endpoints.get(token_type):
       return web.Response(body='Access denied', status=403)
    else:
        user_id = int(headers.get('X-User-Id'))
        token_valid = await is_token_valid(user_id, received_token, connection_pool)
        if token_valid:
            return await handler(request)
        else:
            # have not found a way to optimize this, as we have to see if this kind of token can even access this
            # particular endpoint and after that we have to validate the token, doing so in a roundabout way doesn't
            # really make sense
            return web.json_response(body='Access denied', status=403)


