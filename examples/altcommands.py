from clize import run


VERSION = "0.2"


def do_nothing():
    """Does nothing"""
    return "I did nothing, I swear!"


def version():
    """Show the version"""
    return 'Do Nothing version {0}'.format(VERSION)


run(do_nothing, alt=version)
