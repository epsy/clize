#!/usr/bin/env python

from __future__ import print_function

from sigtools.modifiers import autokwoargs, annotate
from sigtools.signatures import forwards, merge
from clize import run

try:
    from inspect import signature
except ImportError:
    from funcsigs import signature


class Command(object):
    def __init__(self):
        self.__signature__ = forwards(
            signature(self.__call__),
            merge(
                signature(self.do),
                signature(self.prepare),
                signature(self.status)
            )
        )
        self._sigtools__wrappers = (
            self.do, self.prepare, self.status, self.__call__)

    @autokwoargs
    def __call__(self, quiet=False, dry_run=False, *args, **kwargs):
        """
        General options:

        quiet: Print less output

        dry_run: Don't do anything concrete
        """
        self.prepare(*args, **kwargs)
        if not quiet:
            self.status(*args, **kwargs)
        if not dry_run:
            return self.do(*args, **kwargs)

    def prepare(self, *args, **kwargs):
        pass

    def status(self, *args, **kwargs):
        pass

    def do(self, *args, **kwargs):
        pass


class AddCmd(Command):
    """Sums the given numbers

    numbers: The numbers to add together
    """
    @autokwoargs
    def status(self, no_prefix=False, *numbers):
        """
        Formatting options:

        no_prefix: Don't print a prefix in the status message
        """
        if not no_prefix:
            print("summing ", end='')
        print(*numbers, sep=' + ')

    @annotate(numbers=int)
    def do(self, *numbers, **kwargs):
        return sum(numbers)


if __name__ == '__main__':
    run(AddCmd())
