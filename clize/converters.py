# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2015 by Yann Kaiser <kaiser.yann@gmail.com>
# See COPYING for details.

import io

from dateutil import parser as dparser

from clize import parser, errors


@parser.value_converter(name='TIME')
def datetime(arg):
    return dparser.parse(arg)


def file(**kwargs):
    @parser.value_converter(name='FILE')
    def file_(arg):
        try:
            return io.open(arg, **kwargs)
        except IOError as exc:
            raise _convert_ioerror(arg, exc)

    return file_

def _convert_ioerror(arg, exc):
    nexc = errors.CliValueError('{0.strerror} {1!r}'.format(exc, arg))
    nexc.__cause__ = exc
    return nexc
