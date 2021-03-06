from functools import wraps
from threading import Thread


def list_in_list(list1: list, list2: list) -> list:
    return [item in list2 for item in list1]


def any_in(list1: list, list2: list) -> bool:
    return any(list_in_list(list1, list2))


def filter_dict(dictionary: dict, fields: (list, set)) -> dict:
    return dict((k, v) for k, v in dictionary.items() if k in fields)


def recursive_dict_update(dictionary: dict, updater: dict):
    for key, value in updater.items():
        if key in dictionary.keys() and isinstance(value, dict) and isinstance(dictionary[key], dict):
            recursive_dict_update(dictionary[key], value)
        else:
            dictionary[key] = value


class CreateObject:
    def __init__(self, **entries):
        self.__dict__.update(entries)


def async(func: callable, daemon: bool=False):
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs, daemon=daemon)
        thread.start()
    return wrapper
