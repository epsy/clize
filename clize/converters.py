# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.
import contextlib
import sys
import io
import os
import warnings
from functools import partial

from sigtools.modifiers import autokwoargs

from clize import parser, errors, util


@parser.value_converter(name='TIME')
def datetime(arg):
    """Parses a date into a `datetime` value

    Requires ``dateutil`` to be installed.
    """
    from dateutil import parser as dparser

    return dparser.parse(arg)


class _FileOpener(object):
    def __init__(self, arg, kwargs, stdio, keep_stdio_open):
        self.arg = arg
        self.kwargs = kwargs
        self.stdio = stdio
        self.keep_stdio_open = keep_stdio_open
        self.validate_permissions()

    def validate_permissions(self):
        mode = self.kwargs.get('mode', 'r')
        if self.arg == self.stdio:
            return
        exists = os.access(self.arg, os.F_OK)
        if not exists:
            if 'r' in mode and '+' not in mode:
                raise errors.CliValueError(
                    'File does not exist: {0!r}'.format(self.arg))
            else:
                dirname = os.path.dirname(self.arg)
                if not dirname or os.access(dirname, os.W_OK):
                    return
                if not os.path.exists(dirname):
                    raise errors.CliValueError(
                        'Directory does not exist: {0!r}'.format(self.arg))
        elif os.access(self.arg, os.W_OK):
            return
        raise errors.CliValueError(
            'Permission denied: {0!r}'.format(self.arg))

    def __enter__(self):
        if self.arg == self.stdio:
            mode = self.kwargs.get('mode', 'r')
            self.f = sys.stdin if 'r' in mode else sys.stdout
        else:
            try:
                self.f = io.open(self.arg, **self.kwargs)
            except IOError as exc:
                raise _convert_ioerror(self.arg, exc)
        return self.f

    def __exit__(self, *exc_info):
        if self.arg != self.stdio or not self.keep_stdio_open:
            self.f.close()


@contextlib.contextmanager
def _silence_convert_default_warning():
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", "The convert_default parameter of value_converter", DeprecationWarning, r"clize\..*")
        yield


with _silence_convert_default_warning():
    @parser.value_converter(name='FILE', convert_default=True)
    @autokwoargs(exceptions=['arg'])
    def file(arg=util.UNSET, stdio='-', keep_stdio_open=False, **kwargs):
        """Takes a file argument and provides a Python object that opens a file

        ::

            def main(in_: file(), out: file(mode='w')):
                with in_ as infile, out as outfile:
                    outfile.write(infile.read())

        :param stdio: If this value is passed as argument, it will be interpreted
            as *stdin* or *stdout* depending on the ``mode`` parameter supplied.
        :param keep_stdio_open: If true, does not close the file if it is *stdin*
            or *stdout*.

        Other arguments will be relayed to `io.open`.

        You can specify a default file name using `clize.Parameter.cli_default`::

            def main(inf: (file(), Parameter.cli_default("-"))):
                with inf as f:
                    print(f)

        .. code-block:: console

            $ python3 ./main.py
            <_io.TextIOWrapper name='<stdin>' mode='r' encoding='UTF-8'>


        """
        if arg is not util.UNSET:
            return _FileOpener(arg, kwargs, stdio, keep_stdio_open)
        with _silence_convert_default_warning():
            return parser.value_converter(
                partial(_FileOpener, kwargs=kwargs,
                        stdio=stdio, keep_stdio_open=keep_stdio_open),
                name='FILE', convert_default=True)


def _convert_ioerror(arg, exc):
    nexc = errors.ArgumentError('{0.strerror}: {1!r}'.format(exc, arg))
    nexc.__cause__ = exc
    return nexc
