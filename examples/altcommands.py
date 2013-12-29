#!/usr/bin/env python

from clize import run


def do_nothing():
    """Does nothing"""
    return "I did nothing, I swear!"


version = 0.2

def version_():
    """Show the version"""
    return 'Do Nothing version {0}'.format(version)

if __name__ == '__main__':
    run(do_nothing, alt=version_)
