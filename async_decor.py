

def print_decor(coro):

    async def new_function(*args, **kwargs):

        print(f'Вызвана функция {coro.__name__}')
        print(f'с параметрами {args} {kwargs}')
        result = await coro(*args, **kwargs)
        print(f'Получен результат {result}')
        return result

    return new_function
