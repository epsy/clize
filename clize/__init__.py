# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

"""procedurally generate command-line interfaces from callables"""

from clize.parser import Parameter
from clize.runner import Clize, SubcommandDispatcher, run
from clize.legacy import clize, make_flag
from clize.errors import UserError, ArgumentError

__all__ = [
    'run', 'Parameter', 'UserError',
    'Clize', 'ArgumentError', 'SubcommandDispatcher',
    'clize', 'make_flag'
]
