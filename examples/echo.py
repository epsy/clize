#!/usr/bin/env python

import os.path

from clize import clize, run, make_flag

def show_version(name, **kwargs):
    print("{0} version 1.0".format(os.path.basename(name)))
    return True

@clize(
    require_excess=True,
    alias={
            'reverse': ('r',),
        },
    extra=(
            make_flag(
                source=show_version,
                names=('version', 'v'),
                help="Show the version",
            ),
        )
    )
def echo(reverse=False, *text):
    """
    Echoes text back

    text: The text to be echoed

    reverse: Reverse text before echoing

    Beware! There is no warranty this program will not reverse
    your internets!
    """

    text = ' '.join(text)
    if reverse:
        text = text[::-1]
    print(text)

if __name__ == '__main__':
    run(echo)
