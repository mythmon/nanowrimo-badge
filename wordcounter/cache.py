# coding: utf-8
# From https://gist.github.com/FZambia/5123815
# Modified to add decorator
import time
from collections import OrderedDict
from functools import wraps


class Cache():
    """
    In process memory cache. Not thread safe.
    Usage:

    cache = Cache(max_size=5)
    cache.set("python", "perfect", timeout=10)
    cache.get("python")
    >>> perfect
    time.sleep(11)
    cache.get("python")
    >>> None
    cache.get("python", "perfect anyway")
    >>> perfect anyway
    cache.clear()
    """

    def __init__(self, max_size=1000, timeout=None):
        self._store = OrderedDict()
        self._max_size = max_size
        self._timeout = timeout

    def set(self, key, value, timeout=None):
        self._check_limit()
        if not timeout:
            timeout = self._timeout
        if timeout:
            timeout = time.time() + timeout
        self._store[key] = (value, timeout)

    def get(self, key, default=None):
        data = self._store.get(key)
        if not data:
            return default
        value, expire = data
        if expire and time.time() > expire:
            del self._store[key]
            return default
        return value

    def _check_limit(self):
        """
        check if current cache size exceeds maximum cache
        size and pop the oldest item in this case
        """
        if len(self._store) >= self._max_size:
            self._store.popitem(last=False)

    def clear(self):
        """
        clear all cache
        """
        self._store = OrderedDict()

    def __call__(self, key, timeout=None):
        def inner(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                call_key = key.format(*args, **kwargs)
                cached = self.get(call_key)
                if cached is not None:
                    return cached
                result = func(*args, **kwargs)
                self.set(call_key, result, timeout=timeout)
                return result
            return wrapper
        return inner
