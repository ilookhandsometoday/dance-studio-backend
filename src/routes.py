import db
import hashlib
import time
import utils
import asyncpg
from config import logger
from aiohttp import web


router = web.RouteTableDef()

@router.post('/sign_in')
async def sign_in(request: web.Request):
    body = await request.json()
    email: str = body.get('email')
    password: str = body.get('password')
    hash = hashlib.sha256(password.encode('UTF-8')).hexdigest()
    connection_pool = request.app['ps_connection_pool']
    user_data = await db.get_user_data_by_email(email, connection_pool)
    if not user_data:
        return web.json_response(utils.generate_response(0, 'No account with such email'), status=403)

    if not hash == user_data['hash']:
        return web.json_response(utils.generate_response(0, 'Incorrect password'), status=403)

    # TODO send token
    response = utils.generate_response(1, 'Authorization_successful')
    token = await db.get_token(connection_pool, user_data['user_id'])
    response['data'].update({'token': token['tkn'], 'timestamp': token['timestamp'], 'lifetime': token['lifetime']})
    return web.json_response(response, status=200)

@router.post('/sign_up')
async def sign_up(request: web.Request):
    body = await request.json()

    firstname: str = body.get('firstname')
    lastname: str = body.get('lastname')
    mail: str = body.get('email')
    password: str = body.get('password')
    pw_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    connection_pool = request.app['ps_connection_pool']
    try:
        user_by_email = await db.get_user_data_by_email(mail, connection_pool)
        if user_by_email:
            return web.json_response(utils.generate_response(0, 'Account already exists'))

        user_insert_result = await db.insert_user(connection_pool=connection_pool, firstname=firstname, lastname=lastname, email=mail, password_hash=pw_hash, timestamp=int(time.time()))
        # this is here because sometimes it's possible for two identical requests happening at the same time
        # causing an error due to none being inserted, as insert_user returns none because in another instance of this
        # handler being run it has already been added
        if user_insert_result:
            token = utils.generate_token()
            await db.insert_token(connection_pool, user_insert_result, token, int(time.time()), 0)
            return web.json_response(utils.generate_response(1, 'Account created successfully'))
        else:
            return web.json_response(utils.generate_response(0, 'Account already exists'))

    except Exception as e:
        logger.warning(f'[Route Handlers] {e}, lineno:{e.__traceback__.tb_lineno}')
        # this will send a 500 response code
        raise


@router.get('/sessions')
async def all_sessions(request: web.Request):
    connection_pool = request.app['ps_connection_pool']
    result = await db.get_all_sessions(connection_pool)
    response = utils.generate_response(1, 'Session list returned')
    response['data'].update({'sessions':[]})
    for session in result:
        specializations = await db.get_instructor_specs(connection_pool, session['instructor_id'])
        response['data']['sessions'].append({
            'session_id': session['session_id'],
            'session_start': session['session_start'],
            'session_place': session['session_place'],
            'session_name': session['session_name'],
            'capacity': session['capacity'],
            'signed_up': session['signed_up'],
            'firstname': session['firstname'],
            'lastname': session['lastname'],
            'specialization': [record['spec_name'] for record in specializations]
        })

    return web.json_response(response, status=200)


@router.get('/ping')
async def ping(request: web.Request):
    return web.Response(body='pong')
