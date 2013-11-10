#!/usr/bin/env python
import json

from sigtools.modifiers import autokwoargs
from sigtools.wrappers import wrapper_decorator
from clize import run

@wrapper_decorator
@autokwoargs
def json_output(func, json_output=False, *args, **kwargs):
    """Decorator that adds the following options:

    Formatting options:

    json_output: Format the output as json
    """
    ret = func(*args, **kwargs)
    if json_output:
        return json.dumps(ret)
    else:
        return ret

@json_output
def return_dict(key, val):
    """Returns a dict with {key: val}, and an extra pair 

    key: the key

    val: the value
    """
    return {key: val, 'none': None}

@json_output
def return_list(first, second):
    """Return a list with [first, second, None]"""
    return [first, second, None]

if __name__ == '__main__':
    run(return_dict, return_list)

