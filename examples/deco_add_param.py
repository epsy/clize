from sigtools.wrappers import decorator
from clize import run


@decorator
def with_uppercase(wrapped, *args, uppercase=False, **kwargs):
    """
    Formatting options:

    :param uppercase: Print output in capitals
    """
    ret = wrapped(*args, **kwargs)
    if uppercase:
        return str(ret).upper()
    else:
        return ret


@with_uppercase
def hello_world(name=None):
    """Says hello world

    :param name: Who to say hello to
    """
    if name is not None:
        return 'Hello ' + name
    else:
        return 'Hello world!'


if __name__ == '__main__':
    run(hello_world)
