from sigtools import modifiers
from clize import run, parameters


@modifiers.kwoargs('listen')
@modifiers.annotate(listen=('l', parameters.multi(min=1, max=3)))
def main(listen):
    """Listens on the given addresses

    listen: An address to listen on.
    """
    for address in listen:
        print('Listening on {0}'.format(address))


run(main)
