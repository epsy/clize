# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2015 by Yann Kaiser <kaiser.yann@gmail.com>
# See COPYING for details.

import io

from dateutil import parser as dparser


def datetime(arg):
    return dparser.parse(arg)


def file(**kwargs):
    def file_(arg):
        return io.open(arg, **kwargs)
    return file_

