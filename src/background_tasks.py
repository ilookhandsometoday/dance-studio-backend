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
                await notifications_cleanup(app)
                result = await DbWrapper().get_all_sessions()
                for session in result:
                    session_id = session['session_id']
                    if  0 < int(session['session_start']) - int(time.time()) <= 3600:
                        notification_by_session_id = await DbWrapper().get_notification_by_session_id(session_id)
                        if not notification_by_session_id:
                            text = f'Скоро начнётся тренировка {session["session_name"]}, время начала занятия: '
                            notification_id = await DbWrapper().add_notification(session_id, text=text)
                        else:
                            notification_id = notification_by_session_id['notification_id']

                        users_bound_to_notification = await DbWrapper().get_users_bound_to_notification(int(notification_id))
                        user_ids_bound_to_notification = [int(binding['user_id']) for binding in users_bound_to_notification]
                        users = await DbWrapper().get_user_ids_by_session(int(session['session_id']))
                        for user in users:
                            if not int(user['user_id']) in user_ids_bound_to_notification:
                                await DbWrapper().bind_notification(user['user_id'], notification_id)
                await asyncio.sleep(60)
            except Exception as e:
                logger.exception('An exception has occured during set_notifications:')
    except asyncio.CancelledError:
        raise

async def notifications_cleanup(app: web.Application):
    notifications = await DbWrapper().get_notifications()
    for notification in notifications:
        if int(notification['session_start_time']) < int(time.time()):
            await DbWrapper.delete_notification(notification['notification_id'])





