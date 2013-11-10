.. currentmodule:: clize

Function compositing
====================

One of Python's strengths is how easy it is to manipulate functions and
combine them. However, this typically breaks tools such as Clize which try to
inspect the resulting callable and only get vague information. Fortunately, using the functions in `sigtools`, we can overcome this
drawback.

We will look at a few different way of using composite callables with Clize.

Decorators
----------

Let's say you want to decorate these two functions so that their return
value could be serialised as json::

    @json_output
    def return_dict(key, val):
        """Returns a dict with {key: val}, and an extra pair"""
        return {key: val, 'none': None}

    @json_output
    def return_list(first, second):
        """Return a list with [first, second, None]"""
        return [first, second, None]

You could implement ``json_output`` like this::

    from functools import partial, update_wrapper

    def decorate(wrapper):
        return partial(do_decorate, wrapper)

    def do_decorate(wrapper, wrapped):
        ret = partial(wrapper, wrapped)
        update_wrapper(ret, wrapped)
        return ret

    @decorate
    @autokwoargs
    def json_output(func, json_output=False, *args, **kwargs):
        """Decorator to add the following options:

        Formatting options:

        json_output: Format the output as json
        """
        ret = func(*args, **kwargs)
        if json_output:
            return json.dumps(ret)
        else:
            return ret

However, trying to pass the functions to :func:`run` presents an incomplete
version of the function: ``--json-output`` is missing.

To palliate the problem, you can use `sigtools.wrappers.wrapper_decorator`
instead of the ``decorate`` function we had defined::

    import json

    from sigtools.wrappers import wrapper_decorator
    from clize import run

    @wrapper_decorator
    def json_output(func, json_output=False, *args, **kwargs):
        """Decorator to add the following options:

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
        """Returns a dict with {key: val}, and an extra pair"""
        return {key: val, 'none': None}

    @json_output
    def return_list(first, second):
        """Return a list with [first, second, None]"""
        return [first, second, None]

    if __name__ == '__main__':
        run([return_dict, return_list])

`clize.ClizeHelp` will pick up the fact that the function is decorated, and
will read parameter descriptions from the wrapper's docstring and append it to
the decorated function.

Class-based command
-------------------


