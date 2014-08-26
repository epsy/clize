from sigtools import modifiers
from clize import run, extra


@modifiers.kwoargs('listen')
@modifiers.annotate(listen=('l', extra.multi()))
def main(listen):
    """Listens on the given addresses

    listen: An address to listen on.
    """
    for address in listen:
        print('Listening on {0}'.format(address))


run(main)
