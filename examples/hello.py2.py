from sigtools.modifiers import kwoargs
from clize import run

@kwoargs('no_capitalize') # turns no_capitalize into a keyword-only parameter
                          # on Python 2
def hello_world(name=None, no_capitalize=False):
    """Greets the world or the given name.

    :param name: If specified, only greet this person.
    :param no_capitalize: Don't capitalize the given name.
    """
    if name:
        if not no_capitalize:
            name = name.title()
        return 'Hello {0}!'.format(name)
    return 'Hello world!'

if __name__ == '__main__':
    run(hello_world)
