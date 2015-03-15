from sigtools.modifiers import autokwoargs
from sigtools.wrappers import wrapper_decorator
from clize import run


@wrapper_decorator
@autokwoargs
def with_uppercase(wrapped, uppercase=False, *args, **kwargs):
    """
    Formatting options:

    uppercase: Print output in capitals
    """
    ret = wrapped(*args, **kwargs)
    if uppercase:
        return str(ret).upper()
    else:
        return ret


@with_uppercase
def hello_world(name=None):
    """Says hello world

    name: Who to say hello to
    """
    if name is not None:
        return 'Hello ' + name
    else:
        return 'Hello world!'


if __name__ == '__main__':
    run(hello_world)
