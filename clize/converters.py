# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2015 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

import io
import os
from functools import partial

from clize import parser, errors


@parser.value_converter(name='TIME')
def datetime(arg):
    from dateutil import parser as dparser

    return dparser.parse(arg)


class _FileOpener(object):
    def __init__(self, arg, kwargs):
        self.arg = arg
        self.kwargs = kwargs
        self.validate_permissions()

    def validate_permissions(self):
        mode = self.kwargs.get('mode', 'r')
        exists = os.access(self.arg, os.F_OK)
        if not exists:
            if 'r' in mode and '+' not in mode:
                raise errors.CliValueError(
                    'File does not exist: {0!r}'.format(self.arg))
            else:
                dirname = os.path.dirname(self.arg)
                if os.access(dirname, os.W_OK):
                    return
                if not os.path.exists(dirname):
                    raise errors.CliValueError(
                        'Directory does not exist: {0!r}'.format(self.arg))
        elif os.access(self.arg, os.W_OK):
            return
        raise errors.CliValueError(
            'Permission denied: {0!r}'.format(self.arg))

    def __enter__(self):
        try:
            self.f = io.open(self.arg, **self.kwargs)
        except IOError as exc:
            raise _convert_ioerror(self.arg, exc)
        return self.f

    def __exit__(self, *exc_info):
        self.f.close()

def file(**kwargs):
    return parser.value_converter(
        partial(_FileOpener, kwargs=kwargs),
        name='FILE')

def _convert_ioerror(arg, exc):
    nexc = errors.ArgumentError('{0.strerror}: {1!r}'.format(exc, arg))
    nexc.__cause__ = exc
    return nexc
