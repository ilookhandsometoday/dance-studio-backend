import asyncio
import sys
import asyncpg
from middlewares import validation_middleware
from aiohttp import web, ClientSession
from routes import router
from config import get_config

async def on_startup(app: web.Application):
    pass

async def on_shutdown(app: web.Application):
    pass

async def ps_generator(app):
    conn_string = app['pg_connection_str']
    app['ps_connection_pool'] = await asyncpg.create_pool(conn_string)
    yield
    await app['ps_connection_pool'].close()


def init_app():
    host, port, postgres_conn = get_config()

    app = web.Application()

    app['pg_connection_str'] = postgres_conn

    app.add_routes(router)
    app.middlewares.append(validation_middleware)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    app.cleanup_ctx.append(ps_generator)

    return app, host, port

if __name__ == '__main__':
    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    app, host, port = init_app()
    web.run_app(app, host=host, port=port)
