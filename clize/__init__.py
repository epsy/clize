# clize - automatically generate command-line interfaces from callables
# Copyright (C) 2013 by Yann Kaiser <kaiser.yann@gmail.com>
# See COPYING for details.

"""procedurally generate command-line interfaces from callables"""

from clize.parser import Parameter
from clize.runner import Clize, SubcommandDispatcher, run
from clize.legacy import clize, make_flag
from clize.errors import UserError, ArgumentError
