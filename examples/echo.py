from clize import ArgumentError, Parameter, run

def echo(*text:Parameter.REQUIRED,
         prefix:'p'='', suffix:'s'='', reverse:'r'=False, repeat:'n'=1):
    """Echoes text back

    :param text: The text to echo back
    :param reverse: Reverse text before processing
    :param repeat: Amount of times to repeat text
    :param prefix: Prepend this to each line in word
    :param suffix: Append this to each line in word
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
