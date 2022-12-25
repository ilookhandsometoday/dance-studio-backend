import hashlib
import time
import utils
import asyncpg
import asyncpg.exceptions as asyncpg_exc
from config import logger
from aiohttp import web
from db_wrapper import DbWrapper


router = web.RouteTableDef()

@router.post('/sign_in')
async def sign_in(request: web.Request):
    body = await request.json()
    email: str = body.get('email')
    password: str = body.get('password')
    hash = hashlib.sha256(password.encode('UTF-8')).hexdigest()
    user_data = await DbWrapper().get_user_data_by_email(email)
    if not user_data:
        return web.json_response(utils.generate_response(0, 'No account with such email'), status=403)

    if not hash == user_data['hash']:
        return web.json_response(utils.generate_response(0, 'Incorrect password'), status=403)

    # TODO send token
    response = utils.generate_response(1, 'Authorization_successful')
    token = await DbWrapper().get_token( user_data['user_id'])
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
    try:
        user_by_email = await DbWrapper().get_user_data_by_email(mail)
        if user_by_email:
            return web.json_response(utils.generate_response(0, 'Account already exists'))

        user_insert_result = await DbWrapper().insert_user(firstname=firstname, lastname=lastname, email=mail, password_hash=pw_hash, timestamp=int(time.time()))
        # this is here because sometimes it's possible for two identical requests happening at the same time
        # causing an error due to none being inserted, as insert_user returns none because in another instance of this
        # handler being run it has already been added
        if user_insert_result:
            token = utils.generate_token()
            await DbWrapper().insert_token(user_insert_result, token, int(time.time()), 0)
            return web.json_response(utils.generate_response(1, 'Account created successfully'))
        else:
            return web.json_response(utils.generate_response(0, 'Account already exists'))

    except Exception as e:
        logger.warning(f'[Route Handlers] {e}, lineno:{e.__traceback__.tb_lineno}')
        # this will send a 500 response code
        raise


@router.get('/sessions')
async def all_sessions(request: web.Request):
    result = await DbWrapper().get_all_sessions()
    response = utils.generate_response(1, 'Session list returned')
    response['data'].update({'sessions':[]})
    for session in result:
        specializations = await DbWrapper().get_instructor_specs(session['instructor_id'])
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

@router.post('/sign_up_for_session')
async def sign_for_session(request:web.Request):
    body = await request.json()
    session_id = body.get('session_id')
    uid = request.headers.get('X-User-Id')

    try:
        await DbWrapper().sign_up_for_session(user_id=uid, session_id=session_id)
    except asyncpg_exc.UniqueViolationError as e:
        return web.json_response(utils.generate_response(0, 'Double signup attempt'), status=400)
    except Exception as e:
        return web.json_response(utils.generate_response(0, f'Something went wrong. {e}'), status=500)

    return web.json_response(utils.generate_response(1, 'Success'), status=200)


@router.post('/unsign_from_session')
async def unsign_from_session(request: web.Request):
    body = await request.json()
    session_id = int(body.get('session_id'))
    uid = request.headers['X-User-Id']

    notification = await DbWrapper().get_notification_by_session_id(session_id)
    await DbWrapper().unsign_from_session(session_id = session_id, user_id=uid)
    await DbWrapper().delete_notification_bind(uid, notification['notification_id'])

    return web.Response(status=200)


@router.get('/instructors')
async def get_instructors(request: web.Request):
    result = await DbWrapper().get_instructors()
    response = utils.generate_response(1, 'Instructor list returned')
    response['data'].update({'instructors': []})
    for instructor in result:
        response['data']['instructors'].append({
            'firstname': instructor['firstname'],
            'lastname': instructor['lastname'],
            'info': instructor['info'],
            'spec': instructor['spec_name']
        })

    return web.json_response(response, status=200)

@router.post('/sessions_by_uid')
async def get_sessions_by_uid(request: web.Request):
    body = await request.json()
    uid = int(request.headers['X-User-Id'])
    start = time.time()
    result = await DbWrapper().get_sessions_by_user(uid)
    logger.info(f'Get sessions by uid: {time.time()-start}')
    response = utils.generate_response(1, 'Session list returned')
    response['data'].update({'sessions': []})
    start_loop = time.time()
    for session in result:
        specializations = await DbWrapper().get_instructor_specs(session['instructor_id'])
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

    logger.info(f'Get instructors specs: {time.time()-start_loop}')

    return web.json_response(response, status=200)

@router.get('/get_notifications_by_uid')
async def get_notifications_by_uid(request: web.Request):
    uid = request.headers['X-User-Id']
    cancellation_notifications = await DbWrapper().get_cancellation_notifications()
    modified_cancellation_notifications = []
    for cancellation_notification in cancellation_notifications:
        # make it so into misc a string is written, comprised of three values separated by SPLT_22
        session_start, session_name, session_place = str(cancellation_notification['misc']).split('SPLT_22')
        text_template = cancellation_notification['n_text']
        additional_text = f'{session_name}, адрес: {session_place}. Тренировка должна была начаться '

        modified_cancellation_notifications.append({'n_text': text_template + ' ' + additional_text, 'session_start': session_start})
    notifications = await DbWrapper().get_notifications_by_user_id(uid)

    for notification in notifications:
        await DbWrapper().soft_delete_notification_bind(int(uid), int(notification['notification_id']))

    notifications.extend(cancellation_notifications)
    data = []
    for notification in notifications:
        new_notification = {
            'text': notification['n_text'],
            'session_start': notification['session_start']
        }

        data.append(new_notification)
    response = utils.generate_response(1, 'Success')
    response['data'] = data
    return web.json_response(response, status=200)


@router.get('/ping')
async def ping(request: web.Request):
    return web.Response(body='pong')
