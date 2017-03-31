from clize import run
from clize.parameters import argument_decorator


@argument_decorator
def capitalize(arg, *, capitalize:('c', 'upper')=False, reverse:'r'=False):
    """
    Options to qualify {param}:

    :param capitalize: Make {param} uppercased
    :param reverse: Reverse {param}
    """
    if capitalize:
        arg = arg.upper()
    if reverse:
        arg = arg[::-1]
    return arg


def main(*args:capitalize):
    """
    :param args: Words to print
    """
    return ' '.join(args)


run(main)
