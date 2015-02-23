#!/usr/bin/env python

from clize import run


VERSION = 0.2


def do_nothing():
    """Does nothing"""
    return "I did nothing, I swear!"


def version():
    """Show the version"""
    return 'Do Nothing version {0}'.format(VERSION)

def build_date(*,show_time=False):
    """Show the build date for this version"""
    print("Build date: 17 August 1979", end='')
    if show_time:
        print(" afternoon, about tea time")
    print()

run(do_nothing, alt={
        'totally-not-the-version': version,
        'birthdate': build_date
        })

run(do_nothing, alt=[version, build_date])


run(do_nothing, alt=version)
