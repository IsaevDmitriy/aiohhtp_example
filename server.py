import config
import hashlib

import aiopg

from aiohttp import web
from gino import Gino
from asyncpg.exceptions import UniqueViolationError


db = Gino()


class BaseModel:

    @classmethod
    async def get_or_404(cls, id):
        instance = await cls.get(id)
        if instance:
            return instance
        raise web.HTTPNotFound()

    @classmethod
    async def create_instance(cls, **kwargs):
        try:
            instance = await cls.create(**kwargs)
        except UniqueViolationError:
            raise web.HTTPBadRequest()
        return instance


class User(db.Model, BaseModel):

    __tablename__ = 'users'

    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)

    _idx1 = db.Index('users_user_username', 'username', unique=True)

    def to_dict(self):
        user_data = super().to_dict()
        user_data.pop('password')
        return user_data

    @classmethod
    async def create_instance(cls, **kwargs):
        kwargs['password'] = hashlib.md5(kwargs['password'].encode()).hexdigest()
        return await super().create_instance(**kwargs)


async def set_connection():
    return await db.set_bind(config.DB_DSN)


async def disconnect():
    return await db.pop_bind().close()


async def pg_pool(app):
    async with aiopg.create_pool(config.DB_DSN) as pool:
        app['pg_pool'] = pool
        yield
        pool.close()


async def orm_engine(app):
    app['db'] = db
    await set_connection()
    await db.gino.create_all()
    yield
    await disconnect()


class HealthView(web.View):

    async def get(self):
        return web.json_response({'status': 'OK'})


class UserView(web.View):

    async def get(self):
        user_id = int(self.request.match_info['user_id'])
        user = await User.get_or_404(user_id)
        return web.json_response(user.to_dict())

    async def post(self):
        data = await self.request.json()
        user = await User.create_instance(**data)
        return web.json_response(user.to_dict())


class Users(web.View):

    async def get(self):
        pool = self.request.app['pg_pool']
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT id, username, name FROM users')
                users = await cursor.fetchall()
                return web.json_response(users)


app = web.Application()
app.cleanup_ctx.append(orm_engine)
app.cleanup_ctx.append(pg_pool)
app.add_routes([web.get('/', HealthView)])
app.add_routes([web.get('/user/{user_id:\d+}', UserView)])
app.add_routes([web.post('/user', UserView)])
app.add_routes([web.get('/users', Users)])

web.run_app(app, port=8089)
