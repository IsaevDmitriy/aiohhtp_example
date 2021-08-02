import aiohttp
import asyncio
from async_decor import print_decor

HOST = 'http://0.0.0.0:8080'


@print_decor
async def make_request(path, method='get', **kwargs):
    async with aiohttp.ClientSession() as session:
        request_method = getattr(session, method)
        async with request_method(f'{HOST}/{path}', **kwargs) as response:
            print(response.status)
            return (await response.text())


async def main():
    response = await make_request('user', 'post', json={'username': 'nikitos4', 'password': '1234'})
    await make_request('user/2', 'get')


asyncio.run(main())