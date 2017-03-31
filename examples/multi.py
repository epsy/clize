from clize import run, parameters


def main(*, listen:('l', parameters.multi(min=1, max=3))):
    """Listens on the given addresses

    :param listen: An address to listen on.
    """
    for address in listen:
        print('Listening on {0}'.format(address))


run(main)
