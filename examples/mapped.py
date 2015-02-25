from sigtools import modifiers
from clize import run, parameters


greeting = parameters.mapped([
    ('Hello', ['hello', 'hi'], 'A welcoming message'),
    ('Goodbye', ['goodbye', 'bye'], 'A parting message'),
])


@modifiers.kwoargs('kind')
@modifiers.annotate(kind=('k', greeting))
def main(name='world', kind='Hello'):
    """
    name: Who is the message for?

    kind: What kind of message should be given to name?
    """
    return '{0} {1}!'.format(kind, name)


run(main)
