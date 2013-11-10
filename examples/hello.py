#!/usr/bin/env python
from sigtools.modifiers import kwoargs
from clize import run

@kwoargs('no_capitalize')
def hello_world(name=None, no_capitalize=False):
    """Greets the world or the given name.

    name: If specified, only greet this person.

    no_capitalize: Don't capitalize the give name.
    """
    if name:
        if not no_capitalize:
            name = name.title()
        return 'Hello {0}!'.format(name)
    return 'Hello world!'

if __name__ == '__main__':
    run(hello_world)
