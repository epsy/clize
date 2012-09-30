#!/usr/bin/python
from clize import clize, run

@clize(require_excess=False)
def echo(reverse=False, *text):
    """Echoes text back

    reverse: reverse the text before echoing back?

    text: the text to echo back"""
    text = ' '.join(text)
    if reverse:
        text = text[::-1]
    print(text)


@clize(require_excess=False)
def shout(*text):
    """Echoes text back, but louder.

    text: the text to echo back

    Who shouts backwards anyway?"""

    print(' '.join(text).upper())

if __name__ == '__main__':
    run(
        (echo, shout),
        description="""\
        A collection of commands for eching text back""",
        footnotes="""\
        Now you know how to echo text back""",
        )
