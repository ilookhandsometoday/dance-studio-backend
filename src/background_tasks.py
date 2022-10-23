import asyncio
import time
from aiohttp import web
from config import logger
from db_wrapper import DbWrapper
async def set_notifications(app: web.Application):
    """A function, that polls the database for all appointments for a session and 'pushes'
    a notification record when the time left before the session starts is approximately 1 hour."""
    try:
        while True:
            try:
                connection_pool = app['ps_connection_pool']
                result = await DbWrapper.get_all_sessions()
                for session in result:
                    if int(time.time()) - int(session['session_start']) <= 3600:
                        text = f'Скоро начнётся тренировка {session["session_name"]}, время начала занятия: {session["session_start"]}.'
                        notification_id = await DbWrapper.add_notification(text=text)
                        users = await DbWrapper.get_sessions_by_user(int(session['session_id']))
                        for user in users:
                            await DbWrapper.bind_notification(user['user_id'], session['session_id'])

                await asyncio.sleep(900)
            except Exception as e:
                logger.exception('An exception has occured during set_notifications:')
    except asyncio.CancelledError:
        raise




