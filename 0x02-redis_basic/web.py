#!/usr/bin/python3
"""expiring web cache and tracker implementation"""

import requests
import redis
from collections.abc import Callable
from functools import wraps

red = redis.Redis()


def tracker(method: Callable) -> Callable:
    """"decorator tracking  url access"""
    @wraps(method)
    def wrapper(url: str) -> str:
        red.incr("count:{}".format(url))
        htmlcache = red.get("cached:{}".format(url))
        if htmlcache:
            return htmlcache.decode("utf-8")
        response = method(url)
        red.setex("cached:{}".format(url), 10, response)
        return response
    return wrapper


@tracker
def get_page(url: str) -> str:
    """fetches url contents
       return url contents
    """

    response = requests.get(url)
    return response.text
