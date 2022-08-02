#!/usr/bin/env python3
"""module containing class Cache"""


import uuid
import redis
from typing import Union, Callable
from functools import wraps


def count_calls(method: Callable) -> Callable:
    """decorator to track methods calls count"""

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """wrapper function
           implements the decorated
           function functionality
        """
        method_name = method.__qualname__
        self._redis.incr(method_name)
        retval = method(self, *args, **kwargs)
        return retval

    return wrapper


def call_history(method: Callable) -> Callable:
    """decorator to track methods call history"""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        inputs = "{}:inputs".format(method.__qualname__)
        outputs = "{}:outputs".format(method.__qualname__)
        self._redis.rpush(inputs, str(args))
        retval = method(self, *args, **kwargs)
        self._redis.rpush(outputs, retval)
        return str(retval)
    return wrapper


def replay(func: Callable):
    """display function's call history"""

    red = redis.Redis()
    try:
        calls = red.get(func.__qualname__).decode('utf-8')
    except Exception:
        calls = 0

    print("{} was called {} times".format(func.__qualname__, calls))
    inputs = red.lrange("{}:inputs".format(func.__qualname__), 0, -1)
    outputs = red.lrange("{}:outputs".format(func.__qualname__), 0, -1)

    for myinput, myoutput in zip(inputs, outputs):
        try:
            myinput = myinput.decode("utf-8")
        except Exception:
            myinput = ""
        try:
            myoutput = myoutput.decode("utf-8")
        except Exception:
            myoutput = ""
        print("{}(*{}) -> {}".format(func.__qualname__, myinput, myoutput))


class Cache:

    """Cache class"""
    def __init__(self) -> None:
        """initializer method"""
        self._redis = redis.Redis()
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """method that stores data under key and returns the key"""

        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(self, key: str,
            fn: Callable = None) -> Union[str, int, float, bytes]:
        """method that take a key string argument and an optional
           Callable argument named fn
        """

        key = self._redis.get(key)
        if fn:
            return fn(key)
        return key

    def get_str(self, key: str) -> str:
        """method to parametrize cache.get"""

        return self._redis.get(key).decode('utf-8')

    def get_int(self, key: str) -> int:
        """method to parametrize cache.get"""

        gotten = self._redis.get(key)
        try:
            gotten = int(gotten.decode('utf-8'))
        except Exception:
            gotten = 0

        return gotten
