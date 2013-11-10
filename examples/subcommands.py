#!/usr/bin/env python
from sigtools.modifiers import kwoargs, annotate
from clize import Parameter, run

@annotate(text=Parameter.R)
@kwoargs('reverse')
def echo(reverse=False, *text):
    """Echoes text back

    reverse: reverse the text before echoing back?

    text: the text to echo back"""
    text = ' '.join(text)
    if reverse:
        text = text[::-1]
    print(text)


@annotate(text=Parameter.R)
def shout(*text):
    """Echoes text back, but louder.

    text: the text to echo back

    Who shouts backwards anyway?"""

    print(' '.join(text).upper())

if __name__ == '__main__':
    run(
        (echo, shout),
        )
