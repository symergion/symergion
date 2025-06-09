from functools import wraps


def in_memory_cache(max_size_field):
    """ A decorator, cache a class method's return value in memory.
    If max size is already reached remove one old cached value before cache new.
    No threading support.

    Args:
        max_size_field (str): The name of the class attribute that
                              specifies the maximum cache size.
    """

    cache = {}

    @wraps(in_memory_cache)
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            key = (*args, str(kwargs))

            if key not in cache:
                if len(cache) == getattr(args[0], max_size_field):
                    cache.popitem()

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapped

    return decorator
