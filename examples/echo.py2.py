from sigtools.modifiers import annotate, autokwoargs
from clize import ArgumentError, Parameter, run

@annotate(text=Parameter.REQUIRED,
          prefix='p', suffix='s', reverse='r', repeat='n')
@autokwoargs
def echo(prefix='', suffix='', reverse=False, repeat=1, *text):
    """Echoes text back

    text: The text to echo back

    reverse: Reverse text before processing

    repeat: Amount of times to repeat text

    prefix: Prepend this to each line in word

    suffix: Append this to each line in word

    """
    text = ' '.join(text)
    if 'spam' in text:
        raise ArgumentError("I don't want any spam!")
    if reverse:
        text = text[::-1]
    text = text * repeat
    if prefix or suffix:
        return '\n'.join(prefix + line + suffix
                         for line in text.split('\n'))
    return text

def version():
    """Show the version"""
    return 'echo version 0.2'

if __name__ == '__main__':
    run(echo, alt=version)
