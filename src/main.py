import asyncio
import sys
import asyncpg
from middlewares import validation_middleware, error_middleware
from aiohttp import web, ClientSession
from routes import router
from config import get_config
from db_wrapper import DbWrapper

async def on_startup(app: web.Application):
    pass

async def on_shutdown(app: web.Application):
    await DbWrapper().cleanup()

def init_app():
    host, port, postgres_conn = get_config()

    app = web.Application()

    app.add_routes(router)
    app.middlewares.append(error_middleware)
    app.middlewares.append(validation_middleware)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app, host, port, postgres_conn

if __name__ == '__main__':
    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    loop = asyncio.get_event_loop()
    app, host, port, postgres_conn = init_app()
    loop.run_until_complete(DbWrapper().prepare(postgres_conn))
    web.run_app(app, host=host, port=port, loop=loop)