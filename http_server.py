from functools import partial
from hashlib import md5

from aiohttp import web
from aiopg import pool
from aiopg.sa import create_engine
from sqlalchemy import (
    Column,  Integer, MetaData, String, Table
)


import config

async def get_app():

    app = web.Application()  # создаем приложение


    class Health(web.View):  # простейший вью

        async def get(self):  # определяем метод GET
            return web.json_response({'status': 'OK'})


    app.router.add_view('/health', Health)  # регистрируем роут


    # Зарегистрируем подключение к БД:
    # Для начала опиши функцию для регистрации подкулючения к БД

    async def register_connection(app: web.Application):

        #  действия во время старта приложения
        pg_pool = await pool.create_pool(config.POSTGRE_DSN)  # создаем пулл подключений
        app['pg_pool'] = pg_pool  # заисываем в контекст приложения
        yield
        pg_pool.close()  # когда приложение завершит работу, пул закроется


    # теперь регистрируем

    app.cleanup_ctx.append(partial(register_connection))

    #  Давайте создадим вью исполльзующее подключение


    class User(web.View):

        #  будет доступно по роуту (/user/{user_id:\d+})
        #  вместо user_id постваляется число переланное в url
        async def get(self):
            user_id = self.request.match_info['user_id']  # получаем user_id
            pg_pool = self.request.app['pg_pool']
            async with pg_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute('SELECT * from app_user where id = %s', user_id)
                    result = await cursor.fetchone()
                    if result:
                        return web.json_response({
                            'id': result[0],
                            'name': result[1]
                        })
            raise web.HTTPNotFound()

            # подключаемя к БД и забираем инфу


    app.router.add_view('/user/{user_id:\d+}', User)  # регистрируем роут

    #  Теперь используем алхимию
    #  Начнем с модели
    metadata = MetaData()


    users_table = Table(
        'app_user',
        metadata,
        Column('id', Integer, autoincrement=True, primary_key=True, nullable=False),
        Column('name', String, nullable=False, unique=True),
        Column('password_hash', String, nullable=False, unique=True),
    )

    # зарегистрируем подключени через engine

    async def register_connection_alchemy(app: web.Application):
        engine = await create_engine(
            dsn=config.POSTGRE_DSN,
            minsize=2,
            maxsize=10)

        app['pg_engine'] = engine
        yield
        engine.close()

    app.cleanup_ctx.append(partial(register_connection_alchemy))


    # опишем View


    class UserAlchemy(web.View):

        async def post(self):
            post_data = await self.request.json()
            try:
                name = post_data['name']
                password = md5(post_data['password'].encode()).hexdigest()
            except KeyError:
                raise web.HTTPBadRequest
            engine = self.request.app['pg_engine']

            async with engine.acquire() as conn:

                result = await conn.execute(users_table.insert().values(name=name, password_hash=password))
                user = await result.fetchone()
                return web.json_response({'user_id': user[0]})


    app.router.add_view('/user/', UserAlchemy)  # регистрируем роут



    return app


if __name__ == '__main__':
    app = get_app()
    web.run_app(app, host='127.0.0.1', port=8080)  # запускаем приложение
