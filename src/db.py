import asyncpg
async def get_user_data_by_email(email, connection_pool: asyncpg.Pool):
    async with connection_pool.acquire() as connection:
        async with connection.transaction():
            result = await connection.fetchrow(f"SELECT user_id, firstname, lastname, email, "
                                               f"hash FROM public.users WHERE email='{email}';")
    return result

async def insert_user(connection_pool: asyncpg.Pool, firstname, lastname, email, password_hash, timestamp):
    async with connection_pool.acquire() as connection:
        async with connection.transaction():
            result = await connection.fetchval(f"INSERT INTO public.users(user_id, firstname, lastname, email, hash, tstamp) "
                                     f"VALUES (DEFAULT, '{firstname}', '{lastname}', '{email}', '{password_hash}', "
                                     f"{timestamp}) on conflict do nothing returning user_id;")
    return result

async def insert_token(connection_pool: asyncpg.Pool, user_id, token, timestamp, lifetime):
    async with connection_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(f"INSERT INTO public.tokens(user_id, tkn, timestamp, lifetime) "
                                     f"VALUES ({user_id}, '{token}', {timestamp}, {lifetime}) on conflict do nothing;")
async def insert_session(connection_pool: asyncpg.Pool, session_place: str, session_name: str, capacity: int, session_start: int, instructor_id: int, signed_up: int = 0):
    async with connection_pool.acquire() as connection:
        async with conneciton.transaction():
            inserted_session = await connection.fetchval(f"INSERT INTO public.sessions(session_id, session_place, session_name, capacity, signed_up, session_start "
                                     f"VALUES(default, '{session_place}', '{session_name}', {capacity}, {signed_up}, {session_start};")
            await connection.execute(f"insert into public.instructors_sessions(instructor_id, session_id)"
                                     f"values({instructor_id, inserted_session['session_id']};")


async def get_token(connection_pool: asyncpg.Pool, user_id: int = 3):
    async with connection_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchrow(f"SELECT tkn, timestamp, lifetime FROM public.tokens WHERE user_id={user_id};")

async def get_all_sessions(connection_pool: asyncpg.Pool):
    async with connection_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(f"SELECT public.sessions.session_id, session_start, session_place, session_name, capacity, signed_up, firstname, lastname, info, public.instructors.instructor_id "
                                          f"FROM public.sessions "
                                          f"inner join public.instructors_sessions on public.sessions.session_id = public.instructors_sessions.session_id "
                                          f"inner join public.instructors on public.instructors_sessions.instructor_id = public.instructors.instructor_id;")

async def get_instructor_specs(connection_pool: asyncpg.Pool, instructor_id: int):
    async with connection_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(f"select spec_name "
                                          f"from public.specializations "
                                          f"inner join public.instructors_specs on public.specializations.spec_id = public.instructors_specs.spec_id "
                                          f"where public.instructors_specs.instructor_id = {instructor_id};")

async def get_instructors(connection_pool: asyncpg.Pool):
    async with connection_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(f"select spec_name, firstname, lastname, info "
                                          f"from public.specializations "
                                          f"inner join public.instructors_specs on public.specializations.spec_id = public.instructors_specs.spec_id "
                                          f"inner join public.instructors on public.instructors.instructor_id = public.instructors_specs.instructor_id;")


async def get_sessions_by_user(connection_pool: asyncpg.Pool, user_id: int):
    async with connection_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(f'SELECT public.sessions.session_id, session_start, session_place, session_name, capacity, signed_up, firstname, lastname, info, public.instructors.instructor_id '
                                          f'FROM public.sessions '
                                          f'inner join public.users_sessions us on public.sessions.session_id = us.session_id '
                                          f'inner join public.instructors_sessions on public.sessions.session_id = public.instructors_sessions.session_id '
                                          f'inner join public.instructors on public.instructors_sessions.instructor_id = public.instructors.instructor_id '
                                          f'where us.user_id = {user_id};')

async def sign_up_for_session(connection_pool: asyncpg.Pool, user_id: int, session_id: int):
    async with connection_pool.acquire() as connection:
        async with connection.transaction():
            await connection.fetch(f'insert into public.users_sessions(user_id, session_id) values({user_id}, {session_id});')

async def unsign_from_session(connection_pool: asyncpg.Pool, user_id: int, session_id: int):
    async with connection_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(f'delete from public.users_sessions where user_id = {user_id} and session_id = {session_id}')