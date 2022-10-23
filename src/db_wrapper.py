from singleton import SingletonMeta
import asyncpg

class DbWrapper(object, metaclass=SingletonMeta):
    _pool: asyncpg.Pool = None
    @classmethod
    async def prepare(cls, conn_str: str):
        cls._pool = await asyncpg.create_pool(conn_str)

    @classmethod
    def cleanup(cls):
        cls._pool.close()

    @classmethod
    async def get_user_data_by_email(cls, email: str):
        result = await cls._pool.fetchrow(f"SELECT user_id, firstname, lastname, email, "
                                                   f"hash FROM public.users WHERE email='{email}';")
        return result
    @classmethod
    async def insert_user(cls, firstname, lastname, email, password_hash, timestamp):
        result = await cls._pool.fetchval(
                    f"INSERT INTO public.users(user_id, firstname, lastname, email, hash, tstamp) "
                    f"VALUES (DEFAULT, '{firstname}', '{lastname}', '{email}', '{password_hash}', "
                    f"{timestamp}) on conflict do nothing returning user_id;")
        return result
    @classmethod
    async def insert_token(cls, user_id, token, timestamp, lifetime):
        await cls._pool.execute(f"INSERT INTO public.tokens(user_id, tkn, timestamp, lifetime) "
                                         f"VALUES ({user_id}, '{token}', {timestamp}, {lifetime}) on conflict do nothing;")
    @classmethod
    async def insert_session(cls, session_place: str, session_name: str, capacity: int,
                             session_start: int, instructor_id: int, signed_up: int = 0):
        inserted_session = await cls._pool.fetchval(
                    f"INSERT INTO public.sessions(session_id, session_place, session_name, capacity, signed_up, session_start "
                    f"VALUES(default, '{session_place}', '{session_name}', {capacity}, {signed_up}, {session_start};")
        await cls._pool.execute(f"insert into public.instructors_sessions(instructor_id, session_id)"
                                         f"values({instructor_id, inserted_session['session_id']};")
    @classmethod
    async def get_token(cls, user_id: int = 3):
        return await cls._pool.fetchrow(
                    f"SELECT tkn, timestamp, lifetime FROM public.tokens WHERE user_id={user_id};")

    @classmethod
    async def get_all_sessions(cls):
        return await cls._pool.fetch(
                    f"SELECT public.sessions.session_id, session_start, session_place, session_name, capacity, signed_up, firstname, lastname, info, public.instructors.instructor_id "
                    f"FROM public.sessions "
                    f"inner join public.instructors_sessions on public.sessions.session_id = public.instructors_sessions.session_id "
                    f"inner join public.instructors on public.instructors_sessions.instructor_id = public.instructors.instructor_id;")

    @classmethod
    async def get_instructor_specs(cls, instructor_id: int):
        return await cls._pool.fetch(f"select spec_name "
                                              f"from public.specializations "
                                              f"inner join public.instructors_specs on public.specializations.spec_id = public.instructors_specs.spec_id "
                                              f"where public.instructors_specs.instructor_id = {instructor_id};")

    @classmethod
    async def get_instructors(cls):
        return await cls._pool.fetch(f"select spec_name, firstname, lastname, info "
                                              f"from public.specializations "
                                              f"inner join public.instructors_specs on public.specializations.spec_id = public.instructors_specs.spec_id "
                                              f"inner join public.instructors on public.instructors.instructor_id = public.instructors_specs.instructor_id;")

    @classmethod
    async def get_sessions_by_user(cls, user_id: int):
        return await cls._pool.fetch(
                    f'SELECT public.sessions.session_id, session_start, session_place, session_name, capacity, signed_up, firstname, lastname, info, public.instructors.instructor_id '
                    f'FROM public.sessions '
                    f'inner join public.users_sessions us on public.sessions.session_id = us.session_id '
                    f'inner join public.instructors_sessions on public.sessions.session_id = public.instructors_sessions.session_id '
                    f'inner join public.instructors on public.instructors_sessions.instructor_id = public.instructors.instructor_id '
                    f'where us.user_id = {user_id};')

    @classmethod
    async def sign_up_for_session(cls, user_id: int, session_id: int):
        await cls._pool.fetch(
                    f'insert into public.users_sessions(user_id, session_id) values({user_id}, {session_id});')

    @classmethod
    async def unsign_from_session(cls, user_id: int, session_id: int):
        await cls._pool.execute(
                    f'delete from public.users_sessions where user_id = {user_id} and session_id = {session_id}')

    @classmethod
    async def add_notification(cls, text: str = '', misc: str = ''):
        result = await cls._pool.fetchval(
            f"insert into public.notifications (n_text, misc) values('{text}', {misc}) returning notification_id;")
        return result

    @classmethod
    async def bind_notification(cls, user_id, notification_id):
        await cls._pool.execute(
                    f"insert into public.notifications_users (user_id, notification_id) values({user_id}, {notification_id});")

    @classmethod
    async def get_user_ids_by_session(cls, session_id):
        result = await cls._pool.fetch(
                    'select user_id from public.sessions inner join public.users_sessions on '
                    'public.sessions.session_id = public.users_sessions.session_id;')
        return result

    @classmethod
    async def unbind_notification(cls, user_id, notification_id):
        await cls._pool.execute(
                    f"delete from notifications_users where user_id = '{user_id}' and notification_id = '{notification_id}';")
    @classmethod
    async def get_notification_by_user_id(cls):
        ...