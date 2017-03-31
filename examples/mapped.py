from clize import run, parameters


greeting = parameters.mapped([
    ('Hello', ['hello', 'hi'], 'A welcoming message'),
    ('Goodbye', ['goodbye', 'bye'], 'A parting message'),
])


def main(name='world', *, kind:('k', greeting)='Hello'):
    """
    :param name: Who is the message for?
    :param kind: What kind of message should be given to name?
    """
    return '{0} {1}!'.format(kind, name)


run(main)
