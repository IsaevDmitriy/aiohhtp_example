"""Здесь мы лбращаемся к роутам из http_server.py"""


from asyncio import run

from aiohttp.client import ClientSession


HOST = 'http://127.0.0.1:8080'


async def check_health():
    async with ClientSession() as session:
        async with session.get(f'{HOST}/health') as response:
            status = await response.json()
            return status


async def get_user(user_id: int):
    async with ClientSession() as session:
        async with session.get(f'{HOST}/user/{user_id}') as response:
            if response.status == 200:
                user = await response.json()
                return user


async def create_user(name: str, password: str):
    async with ClientSession() as session:
        async with session.post(f'{HOST}/user/', json={
            'name': name,
            'password': password
        }
                                ) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(response.status)


async def main():
    print(await check_health())
    print(await get_user(1))
    print(await create_user('user_1', '1234'))


if __name__ == '__main__':
    run(main())
