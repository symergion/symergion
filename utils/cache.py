from functools import wraps


def lru_cache(max_size_field):
    """ A decorator, cache a function's return value.
    If max size is already reached remove one old cached value before cache new.
    No threading support.

    Args:
        max_size_field (str): The name of the attribute in
                              the first positional argument that
                              specifies the maximum cache size.
    """

    cache = {}

    @wraps(lru_cache)
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
